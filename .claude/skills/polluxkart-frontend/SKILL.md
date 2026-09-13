---
name: polluxkart-frontend
description: Use before writing or reviewing any code in `web/` - a storefront page, a cart, checkout or account screen, an admin screen, an API call, a form, a route's rendering or caching mode, SEO metadata, or a frontend test. Covers the Next.js App Router layout, the one typed API surface, rendering and cache rules per route, URL state, errors read by code, forms, the four list states, SEO, CSP, accessibility, performance budgets and what must pass before a pull request. Pair it with polluxkart-design for anything visual and polluxkart-commerce for anything touching money, stock or orders.
---

# PolluxKart: frontend architecture

Draft written 2026-09-13, before any code exists.
Every path under `web/` and `api/` is planned, not built yet.

The storefront, the customer account area and the admin screens are one Next.js app in `web/`.
Next.js is a React framework that can render pages on the server.
Its App Router is folder-based routing, where each folder under `web/src/app/` becomes a URL.
The backend is Spring Boot in `api/`, in the same repository, so an API change and the screen that uses it ship in one pull request.

Sources of truth this skill summarises: `docs/platform/architecture.md`, `docs/design/high-level/design-system.md` and `docs/services/<service>/README.md`.
If anything here disagrees with them, they win - update this skill, do not guess.

## Glossary

- **Server component:** a React component that runs only on the server and sends HTML, so its code never reaches the browser.
- **Client island:** a small component marked `'use client'` that runs in the browser inside an otherwise server-rendered page.
- **OpenAPI spec:** a machine-readable list of every API endpoint and its request and response shapes, generated from the Spring Boot code.
- **Problem Details (RFC 9457):** the standard JSON error shape our API returns, with our own stable `code` field added.
- **Cache tag:** a label attached to cached data, so one call can throw away everything carrying that label.
- **CSP (Content Security Policy):** a response header telling the browser which scripts may run.
  A nonce is a random value, new on every request, that marks our own inline scripts as allowed.
- **JSON-LD:** structured data in a `<script type="application/ld+json">` tag that tells search engines what a page is about.
- **LCP and CLS:** Largest Contentful Paint (how quickly the main content appears) and Cumulative Layout Shift (how much the page jumps while loading).
- **MSW (Mock Service Worker):** a test library that answers HTTP requests with prepared fixtures.

## Stack (decided 2026-09-13)

- Next.js, latest stable at scaffold time, App Router only, with no `pages/` directory.
- TypeScript with `strict: true`, no `any`, and no `@ts-ignore` to make a screen compile.
- pnpm with the lockfile committed, on Node 24.
- Tailwind CSS v4 with the fixed tokens from polluxkart-design.
- shadcn/ui, copying in only the components a screen actually uses.
  An unused component is dead code somebody later copies as a pattern.
- Forms use react-hook-form with zod schemas.
- Admin only: TanStack Query for server data in the browser, and TanStack Table for tables.
- Tests use Vitest, Testing Library and MSW, plus Playwright with axe for end-to-end.

Next.js caching APIs changed between versions 14, 15 and 16.
Before relying on a name used below (`'use cache'`, `cacheTag`, `revalidateTag`, `proxy.ts`, the image `preload` prop), check it against the installed version's docs, and fix this skill if it moved.

## Layout

```
web/src/
├── app/
│   ├── (store)/        /, c/[slug], p/[slug], search, brands/[slug], compare,
│   │                   cart, checkout, orders/[number]/confirmation
│   ├── (auth)/         login, register, verify email, reset password
│   ├── (account)/account/
│   ├── (legal)/        about, contact, grievance, terms, privacy, returns-refunds, ...
│   ├── admin/
│   ├── internal/revalidate/route.ts
│   └── sitemap.ts, robots.ts, not-found.tsx, error.tsx, global-error.tsx
├── components/         ui/ (shadcn), brand/, states/, store/, admin/
├── lib/
│   ├── api/            schema.d.ts (generated), browser.ts, server.ts, catalog.ts,
│   │                   errors.ts, keys.ts
│   └── format.ts       formatPaise and paiseToDecimalString, the only money-to-text code
├── styles/globals.css
└── test/               MSW handlers and fixtures typed from schema.d.ts
```

The revalidate route lives under `/internal/`, not `/api/`, because Caddy sends every `/api/*` request to Spring Boot.
Caddy refuses `/internal/*` from the internet, and the API calls it over the private Docker network with a shared secret.
Do not name the folder `_internal`, because App Router folders starting with `_` are private and never become routes.

## One API surface: pages and components never call `fetch`

Everything goes through `web/src/lib/api/`.
A page or component that calls `fetch`, or builds an API URL by hand, is a bug.

- `schema.d.ts` is generated by `openapi-typescript` from `api/openapi/openapi.json` with `make gen-api`, and is never hand-edited.
- `browser.ts` is an `openapi-fetch` client for client components.
  It calls same-origin `/api/v1/...`, so the session cookie goes along automatically, and a middleware adds the CSRF header on every mutation.
- `server.ts` starts with `import 'server-only'`.
  It forwards the incoming `Cookie` header and the request id to `API_INTERNAL_URL` (`http://api:8080` inside Docker), and only dynamic routes may use it.
- `catalog.ts` also starts with `import 'server-only'`, and it never reads or forwards cookies.
  Cached catalog pages use only this client, so a personalised response can never land in a shared cache.
- `errors.ts` turns every failure into one `ApiError` shape, described below.

`openapi-fetch` returns `{ data, error, response }` instead of throwing.
Each client wraps calls in one `unwrap` helper that throws `ApiError`, so no screen ever inspects a `Response`.

**Types are generated, not written.**
If the spec marks a field optional that is always present, fix the Spring Boot annotation in `api/` and regenerate.
Never widen a type in `web/` to make a screen compile.
CI fails when the committed spec or `schema.d.ts` is out of date.

**No silent fallback to mock data (decided 2026-09-13).**
The legacy homepage rendered products from `legacy/frontend/src/data/products.js` that did not exist in the database, and customers saw them as real.
If an endpoint fails, the screen shows the error state.
It never shows sample products, placeholder prices or a default rating.
Mock data exists only in test fixtures under `web/src/test/`.

**No invented reviews or ratings.**
A product with zero reviews shows no stars and no rating number.
The legacy site showed a default 4.5, which Indian consumer rules treat as a fake review.

**The UI never computes money.**
Line totals, discounts, delivery, GST and the grand total come from `POST /api/v1/checkout/quote` and are displayed as returned.
The frontend does no arithmetic on any `*Paise` field.
The only code that touches a paise value is `web/src/lib/format.ts`, which turns it into text for display (`formatPaise`) or for JSON-LD (`paiseToDecimalString`).
The discount percentage next to an MRP also comes from the API, and the rules are in polluxkart-commerce.

## A screen's request count must not grow with the catalog

The number of API calls a page makes must stay the same whether the shop has 3 categories or 300, and 10 products or 10,000.

- The home page reads its sections in a fixed number of calls, never one call per category row.
- A listing returns its facets (filter options with counts) in the same response as the products.
- A product card never fetches its own price, stock or rating.
- Compare reads up to 4 products in one batch call, and the cart reads all its lines in one call.
- `sitemap.ts` pages through products sequentially, never firing every page at once.

The API has per-IP rate limits, and server-side calls all come from the web container.
A burst of server calls can therefore throttle every shopper at once.

**Test the request count, not just the rendering.**
Run the page's data loader against MSW fixtures with 2 categories and with 20, count the requests, and assert the counts are equal.

## Rendering and caching per route (decided 2026-09-13)

| Routes | Mode | Reads cookies | Indexed |
| --- | --- | --- | --- |
| `/`, `/c/[slug]`, `/p/[slug]`, `/brands/[slug]` | Cached server components, invalidated by tag | Never | Yes |
| `/search`, `/compare` | Server-rendered from URL params, with cached data | Never | `noindex, follow` |
| `(legal)` pages | Static | Never | Yes |
| `/cart`, `/checkout`, `/orders/.../confirmation`, `/account/*`, `(auth)` | Dynamic, `no-store` | Yes, via `server.ts` | `noindex` |
| `/admin/*` | Client-rendered with TanStack Query and Table | Browser only | `noindex` plus `X-Robots-Tag` |

- **Catalog pages never read cookies.**
  Reading one would make every shopper's page unique and switch caching off.
  The signed-in user's name and the cart count are client islands that call the browser client after load.
- **Tags:** tag catalog reads as `product:<slug>`, `category:<slug>`, `brand:<slug>` and `home`.
  After an admin change, the API calls `/internal/revalidate` with the shared secret and the tags.
  Use immediate expiry for price and availability changes, not stale-while-revalidate, so no page shows an old price once the change is saved.
- **Filters are part of the cache key.**
  Normalise search params (sorted keys and values, defaults dropped) before the cached read, so `?brand=b&brand=a` and `?brand=a&brand=b` share one entry and one canonical URL.
- **`next build` must pass with no API running.**
  CI builds the image without a backend, so catalog data is fetched at request time and cached, never during the build.
  Check it by building with `API_INTERNAL_URL` pointing nowhere.
- **One image for staging and production.**
  Anything that differs between them (Razorpay key id, media host) is read on the server at runtime and passed down as props, never baked in through a `NEXT_PUBLIC_*` variable.
- **Admin** checks the session in its server layout and redirects non-admins, but that is only a convenience.
  The real guard is the API, which refuses every `/api/v1/admin/**` call from a customer.
- A `next` redirect parameter after login is accepted only when it is a relative path on our own site, so the login page cannot send people to another website.

## State that someone would want to keep lives in the URL

Category filters, sort order, page number, search query, compare list and selected variant live in URL search params, not `useState`.
That makes a filtered listing shareable on WhatsApp, and it survives a reload or the back button.
Use `useState` only for things nobody would bookmark, such as an open drawer or a half-typed pincode.
Update the URL with `router.replace` for filter changes, so each checkbox click does not add a history entry.

## Errors are read by code, never by status number or message text

The API returns Problem Details with a stable `code`, a `requestId` and, for validation failures, an `errors[]` list of field problems.
`ApiError` in `web/src/lib/api/errors.ts` carries `code`, `status`, `requestId` and `fieldErrors`.

- `explain(error)` returns a plain sentence and, where there is one, an action.
  Showing a raw code, a status number or the API's `detail` text to a shopper is a bug in `errors.ts`.
- Branch on `code`, using the names the spec declares.
  For example, `price_changed` shows the fresh quote, `out_of_stock` marks the cart line, and a signed-out code sends the shopper to log in.
- A `fetch` `TypeError` means the network failed, and it gets its own sentence: "We could not reach PolluxKart. Check your connection and try again."
- An unknown code gets a generic sentence plus the request id, so support can find the log line.
- A test asserts that every error code the OpenAPI spec declares has an entry in `explain`.

**Expected failures are rendered, not thrown.**
In production, Next.js replaces the message of an error thrown in a server component with a generic one plus a `digest`, so the `code` and `requestId` never reach `error.tsx`.
Catch `ApiError` in the page and render the error state with the request id.
`error.tsx` and `global-error.tsx` are the last resort for unexpected crashes, and they show the `digest`.
A missing product (`product_not_found`) calls `notFound()`, which renders `not-found.tsx` with a real 404 status.

## Forms

- react-hook-form holds the form state, and a zod schema validates in the browser for fast feedback.
  The API is still the authority and validates everything again.
- The zod output type must be assignable to the generated request body type, checked at compile time, so a renamed API field breaks the build instead of the form.
- On a validation failure, map each `errors[]` entry onto its field with `setError`, using the API's dotted paths (`address.pincode`) as field names.
  An entry with no matching field shows in a form-level alert and is never dropped.
- Every input has a visible `<label>`, because placeholders are not labels.
- Submit is disabled while pending and shows progress.
- Order placement sends an `Idempotency-Key` created once per attempt and reused on retry, plus `expectedTotalPaise` from the quote on screen.
  After a `price_changed` response, show the new quote and create a new key when the shopper confirms.
  Details are in polluxkart-commerce.

## There are four list states, and shipping only one is the bug

Import them from `web/src/components/states/`, and never hand-roll them.

- **Loading:** a skeleton with the final layout's dimensions, so nothing jumps, carrying `aria-busy`.
  Route-level ones live in `loading.tsx`.
- **Empty:** nothing exists yet, for example a new category with no products.
- **No matches:** the filters matched nothing.
  Say which filters, and offer "Clear filters" that keeps the category.
- **Error:** the `explain` sentence, a retry action and the request id.

"Nothing exists yet" and "your filters matched nothing" send people to different places, so they are never the same component.

## Admin screens

- Query keys come from the `keys` factory in `web/src/lib/api/keys.ts`, never inline arrays, so related screens invalidate together.
- After a mutation, invalidate every prefix whose data changed.
  Shipping an order changes the order list, the order detail, stock and invoices.
- Paginated lists use `placeholderData: keepPreviousData`, so paging does not flash a skeleton.
- Anything with no undo (cancel with refund, stock write-off) uses the shared confirm dialog, never a bare button.

## SEO

- `generateMetadata` gives every product, category and brand page its own title, description and canonical URL.
  Titles use a plain hyphen or a pipe, never an em dash.
- Product pages get a 1200x630 Open Graph image, so WhatsApp and other apps show a preview.
  Keep it a small JPEG, because WhatsApp often drops large preview images.
- Product pages carry JSON-LD `Product` with `Offer` (price as a decimal string such as `"2999.00"`, `priceCurrency` `INR`, real availability) and `BreadcrumbList`.
  `aggregateRating` appears only when real reviews exist, and the JSON-LD price must equal the visible price.
- Escape JSON-LD before injecting it with `JSON.stringify(data).replace(/</g, '\\u003c')`, so a product name cannot close the script tag.
- `sitemap.ts` lists product, category, brand and legal pages only.
- `robots.ts` disallows `/admin`, `/account`, `/cart`, `/checkout` and `/api/`.
- Filtered and search URLs are `noindex, follow` with a canonical link to the unfiltered page, so crawlers do not index endless filter combinations.

## Images

- Always use `next/image`, loading only from the media domain (`media.polluxkart.com`, plus the staging media host) listed in `images.remotePatterns`.
- Every image has `width` and `height` (or `fill` inside a sized parent) and a real `sizes` attribute.
- The one LCP image per page (the main product photo, or the hero) gets `preload`, which was named `priority` before Next.js 16.
  Nothing else does.
- Alt text comes from the API, where it is required on product images.

## Content Security Policy (decided 2026-09-13)

- **Catalog routes** send a static CSP header, because a nonce forces a fresh render per request and would switch off caching.
  It allows only our own origin and the media domain, with `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'` and `form-action 'self'`.
  Without a nonce, Next.js's own inline bootstrap scripts need `'unsafe-inline'` in `script-src`, which is weaker against injected scripts.
  That trade-off is accepted only because catalog pages render no user-written HTML and load no third-party scripts.
- **Checkout, account and admin** use a nonce-based CSP generated per request in `proxy.ts` (called `middleware.ts` before Next.js 16).
  These routes are dynamic anyway.
- Razorpay Checkout.js loads only on `/checkout`, through `next/script` with the nonce.
  Take Razorpay's allowed hosts from its current docs, and run the policy in report-only mode on staging before enforcing it.

## Accessibility

- Anything clickable is a real `<button>` or `<a>`, and a clickable `<div>` is a bug.
- Never nest a button inside a link.
  A product card's title is the link to the product page, and the add-to-cart button sits beside it, not inside it.
- Icon-only buttons (cart, wishlist, close, quantity plus and minus) have an `aria-label`.
- Add to cart is always visible, including on touch screens, never hover-only.
  The legacy listing hid it until mouse hover, so phone users could not add from listings.
- Tap targets are at least 44 by 44 CSS pixels.
- The whole checkout works with a keyboard alone, and a Playwright test proves it.
- axe reports zero serious or critical violations on every E2E page, and `eslint-plugin-jsx-a11y` runs in lint.

## Performance budgets (Lighthouse CI, mobile)

- Performance at least 90, and SEO 100.
- LCP at most 2.5 s, and CLS at most 0.1.
- Storefront first-load JavaScript at most 150 KB gzip.

Keep them by default rather than by tuning later.
That means server components unless interaction needs the browser, fonts through `next/font`, sized skeletons and images, TanStack Query only in admin, and Checkout.js only on `/checkout`.

## Tests

- **Fixtures are contract-shaped.**
  Type each fixture against `components['schemas'][...]` from `schema.d.ts` with `satisfies`, including fields that can be null.
  A fixture invented to make a screen pass proves only that the screen renders that fixture.
- **Mocks are written from the interface,** not from what one test needs.
- Every storefront and admin list screen has a render test for each list state: loading, empty, no matches and error.
- Every page that lists catalog data has a request-count test.
- A test checks that every declared error code has an `explain` entry.
- Async server components are awkward to render in Vitest, so test their data loaders with MSW and cover the rendered page in Playwright.
- Playwright runs with `retries: 0` on the compose stack, so a flaky test gets fixed, not retried.

## Checklist before you open a pull request

- [ ] No `fetch` or hand-built API URL outside `web/src/lib/api/`.
- [ ] `schema.d.ts` regenerated with `make gen-api` if the API changed, and committed.
- [ ] No mock data, placeholder product, invented rating or fake review outside `web/src/test/`.
- [ ] No arithmetic on money: every amount comes from the API and goes through `web/src/lib/format.ts`.
- [ ] Catalog pages do not read cookies or use `server.ts`, and personal data never goes through `catalog.ts`.
- [ ] Request count does not grow with the number of categories or products, and a test proves it.
- [ ] Filter, sort, page and variant state is in the URL.
- [ ] Errors branch on `code`, new codes have an `explain` entry, and the error state shows the request id.
- [ ] Every list has loading, empty, no matches and error states.
- [ ] Metadata, JSON-LD and the Open Graph image are checked on new catalog pages.
- [ ] Real buttons and links, labelled icon buttons, 44px tap targets, and a working keyboard path.
- [ ] Visual rules from polluxkart-design are followed, with tokens only and the contrast test passing.
- [ ] `make ci-web` passes locally, then `make ci`.
- [ ] You say which command you ran, and never claim CI is green if it did not run.
- [ ] Work happened in your own worktree from a fresh `origin/development`, with explicit paths staged, and the pull request targets `development`.
