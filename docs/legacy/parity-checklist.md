# Parity checklist: legacy features versus the rebuild

The `legacy/` folder is deleted only when every line below is ticked.
A line is ticked when the rebuilt feature works end to end on staging, or when the owner has decided in writing to drop it.
Dropped items say why, next to the line.

"Parity" here means the new store does at least what the old one tried to do.
It does not mean copying the old behaviour, which was often wrong (see [`audit-2026-09.md`](audit-2026-09.md)).

## Storefront

- [ ] Home page with categories and featured products (real data only)
- [ ] Store listing with category, brand and price filters, sorting and pagination
- [ ] Search
- [ ] Product page with image gallery, details and reviews
- [ ] Cart
- [ ] Wishlist
- [ ] Checkout with saved addresses
- [ ] Cash on delivery
- [ ] Razorpay online payment
- [ ] Order history
- [ ] Re-order from a past order

## Accounts

- [ ] Register and log in with email and password
- [ ] Password reset (rebuilt securely, see audit 1.1)
- [ ] Phone OTP login (planned after launch, needs DLT registration)

## Admin

- [ ] Dashboard with order, revenue and low-stock numbers
- [ ] Products: create, edit, archive, images, stock
- [ ] Categories
- [ ] Brands
- [ ] Promotions and coupon codes
- [ ] Orders: list, filter, update status, tracking number
- [ ] Users: list, change role
- [ ] Inventory with stock movement log
- [ ] Image uploads

## Emails

- [ ] Order confirmation
- [ ] Shipped notification with tracking
