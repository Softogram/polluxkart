# Design system

Parent: [high-level/](README.md) | Index: [docs/](../../README.md)

**Status: APPROVED 2026-09-13.**

## The rule that overrides everything else on this page

**The store's colours, fonts, logo and theme stay exactly as they are (owner decision, 2026-09-13).**
The first plan proposed three new visual directions; the owner rejected that.
The rebuild improves layout, usability, accessibility and speed, never the brand's look.
Design tools and skills may shape layout, components, spacing rhythm and accessibility; if one suggests a palette or font, ignore it.

## Where the theme comes from

The source of truth is the first version's theme, carried over value for value:
- `legacy/frontend/src/index.css` (the colour tokens, shadows, gradients, transitions)
- `legacy/frontend/tailwind.config.js` (fonts, radius, token names)
- `legacy/frontend/src/components/brand/Logo.jsx` and `legacy/frontend/public/favicon.svg` (the logo)

When `legacy/` is deleted at launch, these values will already live in `web/src/app/globals.css`, which becomes the source of truth.

## Colour tokens (HSL values, unchanged)

| Token | Value | Used for |
|---|---|---|
| `primary` | `174 72% 45%` | Teal brand colour: primary buttons, links, highlights |
| `primary-foreground` | `0 0% 100%` | Text on primary (see the open question below) |
| `primary-glow` | `174 72% 55%` | Gradient end, hover glow |
| `primary-dark` | `174 72% 35%` | Darker teal |
| `accent` | `90 60% 50%` | Lime accent |
| `accent-foreground` | `0 0% 10%` | Text on accent |
| `accent-glow` | `90 65% 60%` | Accent gradient end |
| `secondary` | `150 20% 95%` | Soft sage surfaces |
| `secondary-foreground` | `174 40% 25%` | Text on secondary |
| `background` | `0 0% 100%` | Page background |
| `foreground` | `200 20% 15%` | Body text |
| `card` / `popover` | `0 0% 100%` | Surfaces |
| `card-foreground` / `popover-foreground` | `200 20% 15%` | Text on surfaces |
| `muted` | `150 15% 96%` | Muted surfaces |
| `muted-foreground` | `200 10% 45%` | Secondary text |
| `border` | `174 20% 88%` | Borders |
| `input` | `174 20% 92%` | Input borders |
| `ring` | `174 72% 45%` | Focus ring |
| `destructive` | `0 72% 51%` | Errors, destructive actions |
| `destructive-foreground` | `0 0% 100%` | Text on destructive |
| `success` | `142 72% 42%` | Success states |
| `success-foreground` | `0 0% 100%` | Text on success |
| `warning` | `38 92% 50%` | Warnings |
| `warning-foreground` | `0 0% 10%` | Text on warning |
| `chart-1` to `chart-5` | `174 72% 45%`, `90 60% 50%`, `200 70% 50%`, `38 92% 50%`, `320 65% 52%` | Admin charts |

## Other tokens (unchanged)

| Token | Value |
|---|---|
| Radius | `0.625rem` (with `sm`, `md`, `xl`, `2xl` derived as in the original) |
| Heading font | Space Grotesk |
| Body font | Inter |
| Shadows | `shadow-sm` to `shadow-xl`, `shadow-glow`, `shadow-accent-glow` as defined in the original |
| Gradients | `gradient-primary`, `gradient-accent`, `gradient-hero`, `gradient-card`, `gradient-subtle` as defined in the original |
| Transitions | fast 150 ms, base 200 ms, slow 300 ms, bounce 500 ms, with the original easing curves |
| Mode | **Light only**, as the live store is today. Dark tokens exist in the original but no toggle ships. |

## How the tokens move into Tailwind v4

The new frontend declares the same values as CSS variables and exposes them to Tailwind with `@theme`, so class names like `bg-primary` and `text-muted-foreground` keep working:

```css
:root {
  --primary: 174 72% 45%;
  --primary-foreground: 0 0% 100%;
  /* ...every token above, same value... */
}

@theme inline {
  --color-primary: hsl(var(--primary));
  --color-primary-foreground: hsl(var(--primary-foreground));
  --font-heading: "Space Grotesk", sans-serif;
  --font-body: "Inter", sans-serif;
  --radius-lg: 0.625rem;
}
```

Components never use raw colours or sizes, only tokens.
Fonts are self-hosted through Next.js font loading instead of a render-blocking stylesheet import, which changes how they load, not how they look.
The logo SVG gets unique gradient ids per render, because the original reused the same ids and broke when the logo appeared twice on one page.

## Open question for the owner (asked 2026-09-13, not yet answered)

White text on the teal primary (`primary-foreground` on `primary`) has a contrast ratio of about 2.2 to 1.
The accessibility minimum (WCAG AA) for normal text is 4.5 to 1, so small white text on teal buttons is hard to read for many people.

Options that keep the palette unchanged:
1. **Use the theme's own dark text (`foreground`) on teal buttons**, about 6.9 to 1. Only the text colour on those buttons changes, using a colour already in the theme.
2. **Keep white text on teal**, as today, and accept the failure.

**Buttons are not built until the owner chooses.**
A test measures the contrast of every text and background pair the site uses, and its expectations follow the owner's answer.

## The four states every list and page shows

| State | What the shopper sees |
|---|---|
| Loading | A skeleton shaped like the content, never a lone spinner |
| Nothing yet | A friendly empty state with one next step, such as "Browse phones" |
| No matches | What was searched or filtered, and a way to clear filters |
| Error | A plain message, a retry, and the request id for support |

## Storefront patterns for an electronics store

- Grouped specifications table (display, performance, camera, battery) driven by each category's specification fields.
- Filters by brand, price range and filterable specifications; a bottom sheet on phones; all filter state in the URL.
- Compare up to four products from one category, with differences highlighted.
- Variant chips (storage, colour) that update the URL and the images.
- MRP struck through beside the selling price, with the discount percentage.
- Delivery estimate for a pincode, and a cash on delivery badge when available.
- A trust row: GST invoice, brand warranty, return window, secure payment.
- Add to cart always visible on touch screens, never only on hover.
- Ratings shown only when real verified reviews exist.

## Honesty and accessibility rules

- No invented numbers, counters, urgency or reviews. See [../../product/compliance.md](../../product/compliance.md).
- Real `<button>` and `<a>` elements; no buttons nested inside links; labels on every icon-only button.
- Tap targets at least 44 by 44 pixels.
- Visible focus rings using the `ring` token.
- Motion reduced when the device asks for reduced motion.
- Every product image has meaningful alternative text.

## See also (do not follow recursively)

- [../../platform/testing.md](../../platform/testing.md) - accessibility and performance checks
