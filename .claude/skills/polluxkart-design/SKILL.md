---
name: polluxkart-design
description: Use before writing or changing any visual markup, Tailwind class, colour, font, spacing, icon, logo use, animation, copy string, or loading, empty or error state in `web/`, on the storefront or in admin. Covers the fixed PolluxKart theme and its exact tokens, how they map into Tailwind v4, the contrast question the owner must answer, the four states, honest numbers, motion and focus rules, electronics storefront patterns, admin table rules and the writing voice. Pair it with polluxkart-frontend for the React and data side.
---

# PolluxKart: design system and UI writing

Draft written 2026-09-13, before any code exists.

## Rule one: the theme is fixed (decided 2026-09-13)

**The existing PolluxKart colours, fonts and theme must not change.**
The owner ordered this on 2026-09-13.
Every value below is copied from the legacy site: `legacy/frontend/src/index.css`, `legacy/frontend/tailwind.config.js` and `legacy/frontend/src/components/brand/Logo.jsx`.
You may map these values into new files and new names.
You may never change a value, add a brand colour, or swap a font.

Design tools do not override this rule.
The vendored `ui-ux-pro-max` and `web-design-guidelines` skills may guide layout, UX patterns, spacing, component quality and accessibility.
They never choose palette or fonts.
If one suggests a palette or a font pairing, ignore that part.

A colour pair that fails contrast is solved by choosing a different pairing from this same palette, with the owner's approval, never by editing a token.

Sources of truth: `docs/design/high-level/design-system.md` and `web/src/styles/globals.css`.
If this skill disagrees with them, they win - update this skill, do not guess.

## Glossary

- **Token:** a named design value, such as `--primary`, used everywhere instead of a raw colour or size.
- **HSL:** a way to write a colour as hue (0 to 360 degrees round the colour wheel), saturation and lightness.
  The legacy tokens store three numbers like `174 72% 45%`, which are wrapped in `hsl()` when used.
- **Contrast ratio:** how different text is from its background, from 1:1 (invisible) to 21:1 (black on white).
- **WCAG AA:** the accessibility standard we meet.
  Normal text needs 4.5:1, while large text (about 24px, or 19px bold) and non-text parts such as focus rings need 3:1.
- **Four states:** loading, empty, no matches and error, which every list screen needs.

## The tokens (light mode, exact values)

Hex codes are rounded conversions for reading only, and the HSL value is the source.

| Token | HSL | About | Role |
| --- | --- | --- | --- |
| `--primary` | `174 72% 45%` | `#20c5b5` | Brand teal for primary fills and active states |
| `--primary-foreground` | `0 0% 100%` | white | Text meant for teal fills (see the contrast question) |
| `--primary-glow` | `174 72% 55%` | `#3adfce` | Gradient end and glow |
| `--primary-dark` | `174 72% 35%` | `#199a8d` | Darker teal |
| `--accent` | `90 60% 50%` | `#80cc33` | Lime accent, also shadcn hover and menu focus fills |
| `--accent-foreground` | `0 0% 10%` | `#1a1a1a` | Text on lime |
| `--accent-glow` | `90 65% 60%` | `#99db57` | Gradient end and glow |
| `--secondary` | `150 20% 95%` | `#f0f5f2` | Soft sage surface |
| `--secondary-foreground` | `174 40% 25%` | `#265954` | Text on sage |
| `--background` | `0 0% 100%` | white | Page |
| `--foreground` | `200 20% 15%` | `#1f292e` | Body text |
| `--card`, `--popover` | `0 0% 100%` | white | Surfaces |
| `--card-foreground`, `--popover-foreground` | `200 20% 15%` | `#1f292e` | Text on surfaces |
| `--muted` | `150 15% 96%` | `#f3f6f5` | Quiet surface |
| `--muted-foreground` | `200 10% 45%` | `#67777e` | Secondary text |
| `--border` | `174 20% 88%` | `#dae7e5` | Borders |
| `--input` | `174 20% 92%` | `#e7efee` | Input borders |
| `--ring` | `174 72% 45%` | `#20c5b5` | Focus ring |
| `--destructive`, `-foreground` | `0 72% 51%`, `0 0% 100%` | `#dc2828`, white | Danger |
| `--success`, `-foreground` | `142 72% 42%`, `0 0% 100%` | `#1eb857`, white | Success |
| `--warning`, `-foreground` | `38 92% 50%`, `0 0% 10%` | `#f59f0a`, `#1a1a1a` | Warning |
| `--chart-1` to `--chart-5` | `174 72% 45%`, `90 60% 50%`, `200 70% 50%`, `38 92% 50%`, `320 65% 52%` | | Admin charts |

- **Radius:** `--radius: 0.625rem`.
  `rounded-lg` is `var(--radius)`, `rounded-md` is `calc(var(--radius) - 2px)`, `rounded-sm` is minus 4px, `rounded-xl` is plus 4px, and `rounded-2xl` is plus 8px.
- **Shadows** use a teal-tinted ink:
  `sm` is `0 1px 2px 0 hsl(174 30% 20% / 0.05)`;
  `md` is `0 4px 6px -1px hsl(174 30% 20% / 0.08), 0 2px 4px -2px hsl(174 30% 20% / 0.06)`;
  `lg` is `0 10px 15px -3px hsl(174 30% 20% / 0.1), 0 4px 6px -4px hsl(174 30% 20% / 0.1)`;
  `xl` is `0 20px 25px -5px hsl(174 30% 20% / 0.1), 0 8px 10px -6px hsl(174 30% 20% / 0.1)`;
  `glow` is `0 0 20px hsl(174 72% 45% / 0.3)`;
  `accent-glow` is `0 0 20px hsl(90 60% 50% / 0.3)`.
- **Gradients:** `--gradient-primary` runs teal 45% to 55% lightness at 135deg, and `--gradient-accent` runs lime `90 60% 50%` to `90 65% 60%`.
  `--gradient-hero` runs teal at 8% opacity to lime at 5%, `--gradient-card` runs white down to `150 15% 98%`, and `--gradient-subtle` runs `150 20% 98%` down to white.
  The utilities are `gradient-primary`, `gradient-accent`, `gradient-hero`, `gradient-card` and `text-gradient` (teal to lime text).
- **Transitions:** `--transition-fast` 150ms, `--transition-base` 200ms and `--transition-slow` 300ms, all `cubic-bezier(0.4, 0, 0.2, 1)`.
  `--transition-bounce` is 500ms `cubic-bezier(0.68, -0.55, 0.265, 1.55)`, and the `hover-lift` utility rises 4px with `shadow-xl`.
- **Animations:** `fade-in` 0.5s, `slide-up` 0.5s (20px), `slide-down` 0.3s (-10px), `scale-in` 0.3s (from 0.95), `accordion-down` and `accordion-up` 0.2s, and the infinite `shimmer` 2s, `bounce-soft` 2s and `pulse-soft` 2s.
- **Fonts:** Space Grotesk (400, 500, 600, 700) for `h1` to `h6` and the wordmark, as `font-heading`.
  Inter (300 to 700) for everything else, as `font-body` and the default sans.
  Monospace is `source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace`.

**Light mode only, as the live site is today.**
The legacy `.dark` token block is copied verbatim so its values are not lost.
No toggle ships, nothing adds the `dark` class, and components never use `dark:` variants.
Set `color-scheme: light` on `html`, or native controls can render dark.

Two legacy blocks are not theme and are not ported.
One is the Google Fonts `@import`, replaced by `next/font` with the same fonts.
The other is the `[data-debug-wrapper]` rules left by the Emergent builder.

## How the tokens map into Tailwind v4

Tailwind v4 reads design values from CSS `@theme` blocks instead of `tailwind.config.js`.
The mapping adds names only, never new values.
Its shape in `web/src/styles/globals.css`:

```css
@import "tailwindcss";
@import "tw-animate-css"; /* v4 replacement for the legacy tailwindcss-animate plugin */

:root { /* legacy light block, values verbatim, minus the --shadow-* lines */
  --primary: 174 72% 45%;
  /* ...every colour, --radius, --gradient-*, --transition-* ... */
}
.dark { /* legacy dark block, verbatim, never activated */ }

@theme inline {
  --color-*: initial; /* removes Tailwind's default palette, so bg-white or text-gray-500 produce nothing */
  --color-background: hsl(var(--background));
  --color-primary: hsl(var(--primary));
  --color-primary-dark: hsl(var(--primary-dark));
  /* ...one line per colour token... */
  --radius-lg: var(--radius);
  --radius-md: calc(var(--radius) - 2px);
  --font-heading: var(--font-space-grotesk), "Space Grotesk", sans-serif;
  --font-sans: var(--font-inter), "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif;
}

@theme {
  --shadow-sm: 0 1px 2px 0 hsl(174 30% 20% / 0.05);
  /* ...md, lg, xl, glow, accent-glow, values verbatim... */
}
```

- Keep the HSL values, and do not convert to `oklch` even though current shadcn defaults do, because a conversion is a rounding change.
- `@theme inline` is needed because the colour values point at `:root` variables.
- Shadows live directly in `@theme`, not in `:root`, because `--shadow-sm: var(--shadow-sm)` would point at itself and resolve to nothing.
- `bg-primary/90` still works, because Tailwind v4 mixes transparency into any colour value.
- Fonts load with `next/font/google` as the CSS variables `--font-space-grotesk` and `--font-inter`.
  They are the same typefaces, served from our own domain, so there is no layout jump and no third-party request.
- Gradients, `text-gradient` and `hover-lift` become `@utility` blocks with the legacy CSS unchanged.

## The one hard rule in components: tokens only

- Never write a hex value, `rgb()`, `hsl()` or an arbitrary Tailwind value such as `text-[13px]`, `bg-[#fff]` or `w-[347px]` in a component.
- Never use a Tailwind default colour (`bg-white`, `text-black`, `bg-gray-100`, `teal-500`).
  Use `bg-background`, `bg-card` and `text-foreground`.
- Spacing and type sizes come from the Tailwind scale (`p-4`, `text-sm`), which is part of the theme.
  Radii and shadows use only the legacy names above.
- If a value you need does not exist, add a named token in `globals.css` and record it in `design-system.md`.
  For example, the legacy dialog overlay was `bg-black/80`, so port it as a named scrim token with that same value, not an inline class.
- **The one exception is the logo artwork**, whose SVG gradients carry their own colour stops.

**shadcn's `accent` is lime here.**
shadcn components use `bg-accent` for ghost and outline button hovers and for focused menu items, so on this theme they turn lime, exactly as on the live site today.
Keep that.
Do not quietly repoint those hovers to `secondary` or `muted`, because that would change the theme.

## The logo

Port `Logo` and `LogoIcon` to `web/src/components/brand/Logo.tsx` with every path, colour stop and size unchanged.

- `Logo` icon sizes are small 28px, default 36px, large 48px and xlarge 64px.
  The wordmark is Space Grotesk bold, with "Pollux" in `text-foreground` and "Kart" in `text-primary`.
- The two components use slightly different stops on purpose, and both are kept.
  `Logo` uses `hsl(174, 72%, 40%)` to `32%` and lime `hsl(90, 60%, 55%)` to `45%`.
  `LogoIcon` uses `#14B8A6` to `#0D9488` and `#A3E635` to `#84CC16`.
  Unifying them would change the brand.
- **Fix the duplicate gradient ids.**
  Each SVG defines fixed ids such as `bgGradLogo`, so when the logo renders twice on one page (header and footer) both copies share one id.
  A hidden first copy can then break the second copy's fill.
  Build each id from React `useId()`, stripping any character that is not a letter, digit, hyphen or underscore before using it in `url(#...)`.
- The favicon and app icons are generated once from `LogoIcon` as static files.
- A logo is exempt from contrast rules, so "Kart" in teal is fine inside the logo and nowhere else.

## Contrast is measured, not eyeballed

Measured 2026-09-13 with the WCAG 2 formula on the exact tokens:

| Text on background | Ratio | Normal text (4.5) | Large text or UI (3.0) |
| --- | --- | --- | --- |
| `foreground` on `background` | 14.89 | pass | pass |
| `primary-foreground` (white) on `primary` | 2.15 | **fail** | **fail** |
| `foreground` on `primary` | 6.91 | pass | pass |
| white on `primary-dark` | 3.49 | fail | pass |
| `primary` text on `background` | 2.15 | **fail** | **fail** |
| `muted-foreground` on `background` | 4.67 | pass | pass |
| `muted-foreground` on `muted` | 4.30 | **fail** | pass |
| `secondary-foreground` on `secondary` | 7.18 | pass | pass |
| `accent-foreground` on `accent` | 8.83 | pass | pass |
| white on `destructive` | 4.80 | pass | pass |
| white on `success`, or `success` text on `background` | 2.60 | **fail** | **fail** |
| `warning-foreground` on `warning` | 8.18 | pass | pass |
| `ring` (teal) against `background` | 2.15 | not text | **fail** |

### Open question for the owner: ask before building buttons

White text on the teal primary is about 2.2:1 and fails WCAG AA.
The in-palette alternative is the theme's own dark `foreground` on teal, at about 6.9:1.
The other option is to keep white text and accept the failure.
The same measurement also found teal text links, `muted-foreground` on `muted`, the success colour and the teal focus ring below their thresholds.
Each has in-palette pairings to offer.
Links can be dark `foreground` text with a teal underline, `muted-foreground` can stay on white only, success can be a word in `foreground` beside a success-coloured icon, and the focus ring can be `primary-dark` or `foreground`.

**Do not choose silently.**
Put the options to the owner with these numbers, and record the answer and its date in `design-system.md`.
Only then build `Button`, `Badge`, links and the focus ring.
Whatever is chosen is applied in those shared components as a pairing, and the token values stay as they are.

### The contrast test

A Vitest test in `web/` reads the token values from `globals.css` and a pairs file listing every text and background pair the shared components use.
It computes the WCAG ratio for each pair and fails below 4.5, or below 3.0 for large text and UI parts.
A pair the owner has knowingly accepted is listed with the decision date, so the exception is visible rather than hidden.
Playwright also runs axe's `color-contrast` rule on real pages, which catches pairs made with opacity or gradients.

## There are four states, and shipping only one is the bug

Use the shared components in `web/src/components/states/`:

- **Loading:** a skeleton shaped like the final content, with `aria-busy`, so nothing jumps when data arrives.
- **Empty:** nothing exists yet, so say that and say where to go instead.
- **No matches:** the filters matched nothing, so name the filters and offer "Clear filters".
- **Error:** a plain sentence, a retry action and the request id for support.

An empty state must not overstate its scope.
If only one tab or filter is empty, say which.

## Numbers must not lie

- No invented social proof: no "50K+ happy customers", no "Trusted by thousands", and no rating unless it comes from real data.
- No fake urgency: no countdown timers that reset, no "12 people are viewing this", and no "Only 2 left" unless it is real stock at that moment.
- A product with no reviews shows no stars and no rating.
  "No reviews yet" is fine, while five empty stars or "0.0" is not.
- A count that covers only a page or a partial read says so on screen.
- Admin rates with a zero denominator show a sentence, not `0%`.

## Motion and focus

- Honour `prefers-reduced-motion: reduce` globally in `globals.css`.
  Turn off `hover-lift` movement, the bounce transition, and every infinite animation (`shimmer`, `bounce-soft`, `pulse-soft`).
  This is a behaviour rule, not a token change.
- Never remove the focus outline.
  Every interactive element shows a visible focus ring from one shared style, whose colour is part of the owner's contrast question.
- Anything interactive is a real `<button>` or `<a>`, a clickable `<div>` is a bug, and a button is never nested inside a link.
- Do not disable a control that answers a question.
  An out-of-stock variant chip stays selectable and shows "Out of stock", rather than being greyed out with no reason.
- Tap targets are at least 44px (`min-h-11 min-w-11`).

## Electronics storefront patterns

- **Product card:** image, brand, name (two lines at most), two or three key specs, selling price, MRP struck through, discount percentage, a rating only when real reviews exist, and an always-visible add-to-cart button.
  The card title is the link, and the button sits beside it, not inside it.
- **Price block:** the selling price large, the MRP in `<s>` with a screen-reader label ("MRP ₹34,999"), the discount percentage from the API, and "Inclusive of all taxes".
  The UI never calculates any of these.
- **Variant chips** (storage, colour) are links to the variant's URL.
  They work without JavaScript, can be shared, and update the page's URL.
- **Specs table:** grouped by the attribute's group (Display, Performance, Battery, Connectivity), built as a real `<table>` with `<th scope="row">`.
  Values carry units, and a missing value says "Not specified" instead of leaving a blank cell.
- **Filters:** brand, price range and filterable specs, each with counts from the API.
  They sit in a sidebar on desktop and in a bottom sheet on mobile with a "Show N results" button.
  Applied filters show as removable chips, and all filter state is in the URL.
- **Sort:** relevance, price low to high, price high to low, and newest.
  There is no "popularity" or "bestseller" label without real data behind it.
- **Compare up to 4:** a labelled compare checkbox on each card, a compare tray, and a clear message when a fifth is added.
  The compare table highlights rows that differ, and scrolls sideways on mobile with the spec name column fixed.
- **Delivery estimate by pincode:** a labelled 6-digit input (`inputMode="numeric"`) that shows the delivery date range and whether Cash on Delivery is available there.
  It is a client island, so the cached product page never reads a cookie.
- **COD badge** appears only where Cash on Delivery is actually available.
  Before a pincode is entered, it reads "Cash on Delivery available in serviceable areas".
- **Trust row:** GST invoice, brand warranty (the real duration from the product), returns (the real window from store settings) and secure payment.
  Every claim must be true for that product.
- **Seller details and country of origin** appear on the product page, as polluxkart-commerce requires.
- **Mobile product page:** a sticky bottom bar with the price and add to cart.
- **Cart:** quantity steppers with 44px buttons, notices for changed prices and out-of-stock lines, and totals only from the quote.

## Admin screens

- Admin uses the same tokens, the same fonts and light mode only, because admin is not a second theme.
- Tables use TanStack Table with compact rows, a sticky header, and money and counts right-aligned with `tabular-nums`.
- Status badges always carry the word, never colour alone.
- Filters and page number live in the URL, as on the storefront.
- Destructive or money-moving actions (cancel with refund, stock write-off) use the danger treatment plus a confirm dialog that names the order and the amount.
- The main admin user is the owner's father, so labels name the task ("Mark as shipped"), not the database field.

## The writing voice

- Plain, short sentences, explaining any technical word the first time a screen uses it.
- Say what happened and what to do next.
  "This pincode is outside our delivery area. Try another address." beats "Invalid pincode".
- Follow Indian conventions: ₹ with lakh grouping (from `Intl`), "pincode", "Cash on Delivery" and "GST invoice".
- No dark patterns in words: no confirm-shaming ("No thanks, I don't like saving money") and no pre-ticked boxes.
- No em dashes, only plain hyphens.

## Checklist before you open a pull request

- [ ] No token value changed, no colour or font added, and no palette suggestion from a design tool applied.
- [ ] No raw colour, `hsl()`, arbitrary Tailwind value or Tailwind default colour in a component.
- [ ] Any new named token (such as a scrim) is recorded in `design-system.md` with its legacy source.
- [ ] Light only, with no `dark:` variants and no theme toggle.
- [ ] Every new text and background pair is in the contrast pairs file, and the contrast test passes.
- [ ] Button, link, badge and focus colours follow the owner's recorded contrast decision, or you asked instead of choosing.
- [ ] Logo ids are unique per render, and the logo artwork is unchanged.
- [ ] Loading, empty, no matches and error states exist for every list.
- [ ] No fake stats, fake urgency, invented ratings or unearned trust claims.
- [ ] Reduced motion honoured, focus ring visible, real buttons and links, and 44px tap targets.
- [ ] Add to cart is visible without hover on every product surface.
- [ ] Copy is plain, specific and free of em dashes.
- [ ] `make ci-web` passes locally, including Playwright with axe when pages changed.
