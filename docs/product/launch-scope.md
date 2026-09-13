# Launch scope

Parent: [product/](README.md) | Index: [docs/](../README.md)

**Status: APPROVED 2026-09-13.**
This is the scope contract for the first release.
A feature not listed under "In scope" is not part of launch, even if it seems small.

## Decisions this scope rests on (all 2026-09-13)

| Area | Decision |
|---|---|
| Existing data | Nothing is carried over from the first version. Clean database, fresh catalog entered through admin. |
| Catalog | Mainly electronics: specifications, brands, compare, light variants such as storage and colour. |
| Login | Email and password, and Sign in with Google. Phone OTP (a one-time code by SMS) comes after launch. |
| Payments | Razorpay (an Indian payment gateway) and cash on delivery. |
| Shipping | Manual at launch: the shop books the courier and enters the tracking number. |
| GST | The shop has a GSTIN (GST registration number), so every order gets a GST tax invoice. |
| Brand | Colours, fonts, logo and theme stay exactly as they are. |

## In scope

**Storefront**
- Home page with real categories and products only.
- Category listing with filters (brand, price, specifications), sorting and pagination, all kept in the URL so a filtered page can be shared.
- Search by product name, brand and model.
- Product page: image gallery, variant picker, grouped specifications, MRP and price, delivery estimate by pincode, cash on delivery badge, warranty and returns summary, verified reviews.
- Compare up to four products from one category.
- Cart for guests and signed-in shoppers; the guest cart merges on sign-in.
- Wishlist for signed-in shoppers.
- Checkout with saved addresses, one server quote, Razorpay or cash on delivery, and a confirmation page.
- Account: profile, address book, sessions and security, order history and detail, invoice download, cancel before packing.
- Legal and help pages listed in [compliance.md](compliance.md).
- Search engine and link-preview support: per-product titles and images, structured product data, sitemap.

**Accounts**
- Register with email and password, verify the email by link.
- Password reset by a single-use emailed link.
- Sign in with Google.
- Sign out of one device or all devices.

**Admin**
- Catalog: categories with their specification fields, brands, products, variants (SKUs), specifications, images, publish and archive.
- Stock: receipts and adjustments with a reason, movement history, low-stock view.
- Orders: filter, pack, ship with courier and tracking number, mark delivered, record cash collected, cancel with refund.
- GST invoices and credit notes, and a GSTR-1 export for the accountant.
- Coupons with usage limits.
- Review moderation.
- Store settings: legal name, GSTIN, address, invoice prefix.
- Users list without any password data, and an audit log of admin actions.
- Two-step sign-in (authenticator app codes) required for every admin.

**Emails**
- Verify email, password reset, security notices.
- Order placed, payment confirmed, shipped with tracking link, delivered, cancelled, refunded.

**Data rights**
- A shopper can download their data and delete their account; invoices are kept for the period GST law requires.

## Deliberately cut from launch

| Cut | Why | When it comes back |
|---|---|---|
| Phone OTP login | Indian law requires DLT registration (registering as an SMS sender) first, which takes weeks | After DLT registration |
| Shiprocket or courier integration | Manual shipping works at launch volume, and the code keeps a seam for it | When manual booking becomes a daily burden |
| Guest checkout without an account | A verified account protects cash on delivery from fake orders | After launch, with fraud checks |
| Self-service returns flow | Returns are handled by the shop from admin at launch | After launch |
| Back-in-stock and price-drop alerts | Not needed to sell | After launch |
| WhatsApp notifications | Message templates need approval and add a vendor | After launch |
| EMI display, B2B invoices with buyer GSTIN, e-invoicing | Not needed for B2C launch; e-invoicing applies only above a turnover threshold | When needed |
| Dedicated search engine | PostgreSQL full-text search handles a few thousand products | Past about 5,000 SKUs |
| Staff roles beyond admin | One family team at launch | When staff join |
| Dark mode | The live store is light only, and the theme is fixed | Only if the owner asks |

## See also (do not follow recursively)

- [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md) - the build order for this scope
- [../legacy/parity-checklist.md](../legacy/parity-checklist.md) - what the first version had, which this scope must cover
