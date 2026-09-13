# Product requirements

Parent: [product/](README.md) | Index: [docs/](../README.md)

**Status: APPROVED 2026-09-13.**
Written from the owner's decisions of that day.
Supersedes the Emergent-era PRD kept at [../legacy/emergent-prd.md](../legacy/emergent-prd.md) for the record.

## The store

PolluxKart is the online store of a family electronics business in India.
It sells phones, laptops, accessories and other electronics directly to shoppers (B2C, business to consumer).
The first version was generated with an AI app builder in early 2026 and was never safe to run with real money.
This rebuild makes it a store the owner can trust with real payments, real stock and real customers for years.

## Who it is for

**The shopper.**
Most arrive on a phone, often from a WhatsApp link or a Google search for a specific model.
They compare specifications and prices, want to know when it will arrive and whether cash on delivery is available, and need a proper GST invoice for warranty claims.
They are wary of online stores that look unofficial, so trust signals matter as much as price.

**The shop owner and staff.**
They add products and stock, pack and ship orders by hand, collect cash on delivery, issue refunds and answer customers.
They are not engineers, so every admin screen and runbook is written for them.

## Core journeys

1. **Find a product.** Browse a category, filter by brand, price and specifications, search by name or model, compare up to four products.
2. **Decide.** Read grouped specifications, see MRP and the selling price, check delivery time and cash on delivery for a pincode, read real reviews from verified buyers.
3. **Buy.** Add to cart as a guest, sign in with email or Google, pick a saved address, see one total from the server, pay with Razorpay or choose cash on delivery.
4. **After buying.** Get an email for each step, track the shipment, download the GST invoice, cancel before packing, request a return after delivery.
5. **Run the shop.** Manage catalog and stock, move orders through packing and shipping, record cash collected, refund, moderate reviews, export GST data.

## Principles

**Never show the shopper something untrue.**
No mock products, no invented reviews or ratings, no fake counters like "50K+ happy customers", no false urgency.
The first version did all of these; see [../legacy/audit-2026-09.md](../legacy/audit-2026-09.md).

**The server is the only source of money.**
Prices, discounts, shipping, GST and the total come from one backend quote.
The browser only displays it.

**Stock is never sold twice.**
The database itself refuses to reserve stock that is not there.

**The brand stays as it is (decided 2026-09-13).**
Colours, fonts, logo and theme carry over unchanged from the first version.
The rebuild improves layout, speed, accessibility and trust, not the look.

**Built to last, not built fast.**
Development effort is not the deciding factor in technical choices.
Correctness, simplicity, robustness, room to grow and long-term maintainability are.

## Success at launch

- A shopper can find, compare and buy a product on a phone in a few minutes, and pay by Razorpay or cash on delivery.
- Every order produces a correct GST invoice that a chartered accountant has signed off.
- The owner can run a normal day (add stock, pack, ship, refund) from the admin screens without help.
- Product pages appear properly in Google results and show the product photo, name and price in WhatsApp link previews.
- No security finding from the legacy audit exists in the new code.

## See also (do not follow recursively)

- [../design/high-level/road-to-launch.md](../design/high-level/road-to-launch.md) - how this gets built
