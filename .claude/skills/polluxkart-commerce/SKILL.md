---
name: polluxkart-commerce
description: Use before writing or reviewing anything that touches money, prices, GST, discounts, coupons, stock, reservations, checkout quotes, order placement, order status changes, Razorpay payments, refunds, Cash on Delivery, shipping, GST invoices, credit notes or consumer-law display rules, in `api/` or `web/`. Covers integer paise, the tax-inclusive GST engine with worked examples, the order state machine, the reservation lifecycle, Razorpay and COD rules, invoice numbering per Indian financial year, and what must pass before a pull request.
---

# PolluxKart: commerce rules

Draft written 2026-09-13, before any code exists.
Paths under `api/` and `web/` are planned.

Sources of truth: `docs/design/high-level/data-model.md`, `docs/design/high-level/order-lifecycle.md`, `docs/product/compliance.md`, and `docs/services/<service>/README.md` for `inventory`, `order`, `payment`, `invoice`, `promotion` and `shipping`.
If this skill disagrees with them, they win - update this skill, do not guess.

This is an engineer's summary of GST and consumer law, not legal advice.
A chartered accountant (CA) signs off on tax and invoices, and a lawyer on legal text.
Anything marked "CA confirms" is not settled.

## Glossary

- **Paise:** one hundredth of a rupee, so ₹1 is 100 paise.
- **Basis points (bps):** hundredths of a percent, so 18% is 1800 bps.
- **GST (Goods and Services Tax):** India's tax on sales.
  Within one state it splits into **CGST** (central) and **SGST** (state), or **UTGST** in a Union Territory without its own legislature.
  Between states it is one **IGST** (integrated).
- **Place of supply:** the state a sale is taxed in; for goods we deliver, the delivery address state.
- **Taxable value:** the price without GST.
- **HSN code:** the government's number for a kind of product, printed on invoices.
- **MRP (Maximum Retail Price):** the price printed on the product, which we may never exceed.
- **Quote:** the server's calculation of every amount in a checkout.
- **Idempotency key:** a unique id sent with a request, so repeating the request does not repeat its effect.
- **SKU (Stock Keeping Unit):** one sellable variant, such as "128 GB, black".
- **Reservation:** stock held for an order so nobody else can buy it.
- **RTO (Return to Origin):** a parcel the courier brings back undelivered.
- **AWB (Air Waybill):** the courier's tracking number.
- **Webhook:** a request Razorpay sends to our server to report an event.
- **HMAC:** a code made from a message and a secret, proving the message is genuine.
- **Financial year (FY):** 1 April to 31 March, the year GST invoice numbering resets.
- **Credit note:** a GST document that reduces an invoice already issued.
- **GSTR-1:** the monthly or quarterly GST return that lists sales.
- **Compensation:** an action that undoes an earlier committed step when a later step fails.

## 1. Money is integer paise everywhere (decided 2026-09-13)

- Postgres `BIGINT`, Java `long` inside the shared-kernel `Money` type, TypeScript `number`, with field names ending in `Paise`.
- Never `float`, `double` or decimal rupees for money.
  The legacy site stored floats, which cannot hold paise exactly.
- Java arithmetic uses `Math.addExact` and `Math.multiplyExact`, so an overflow throws instead of wrapping.
- Format only at display, with `new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(paise / 100)`.
  `11800000` shows as `₹1,18,000.00`, and `99900` as `₹999.00`.
- Never pass `maximumFractionDigits: 0`, because it rounds `₹19,999.99` up to `₹20,000`.
  Hide decimals only when `paise % 100 === 0`.
- Java's `DecimalFormat` cannot do lakh grouping (it repeats only the last group size), so the invoice template uses a small tested formatter or ICU4J.
- The database enforces `price_paise <= mrp_paise` on every SKU.
- The discount percentage beside an MRP is computed by the API and rounded down, so it never overstates.
  MRP ₹3,499 with price ₹2,999 gives `(349900 - 299900) * 100 / 349900 = 14.29`, shown as 14%.

## 2. GST inputs

- **Prices are tax-inclusive** (Indian B2C, decided 2026-09-13).
  The shopper pays exactly the price shown, and tax is extracted from it, never added on top.
- **The rate is stored per product in basis points** (`gst_rate_bps`), with a category default for new products.
  It is a checked integer range, not a hard-coded list of slabs.
  The September 2025 reform moved most goods to 5% or 18% and removed the 12% and 28% slabs for most items, and rates can change again.
- **HSN is stored per product**, 4 to 8 digits, with `CHECK (hsn ~ '^[0-9]{4,8}$')`.
  How many digits the invoice must show depends on turnover (CA confirms).
- **Place of supply** is the delivery address state, stored on the order as a GST state code.
  The shop's state comes from store settings.
- Same state means CGST plus SGST (UTGST instead of SGST if the shop is in a Union Territory without a legislature).
  Different states means IGST.

## 3. The tax engine is one pure function

It takes numbers and returns numbers: no database, no clock, no Spring.
It lives in the `order` service (planned) and runs when the quote is built.
Order lines store its output, and the invoice prints those stored values, so the checkout and the invoice can never disagree.

```java
record LineTax(long taxablePaise, long cgstPaise, long sgstPaise, long igstPaise) {}

static LineTax taxLine(long netInclusivePaise, int rateBps, boolean interState) {
    long d = 10_000L + rateBps;
    long taxable = (2 * Math.multiplyExact(netInclusivePaise, 10_000L) + d) / (2 * d); // round half up
    long tax = netInclusivePaise - taxable;
    if (interState) return new LineTax(taxable, 0, 0, tax);
    long sgst = tax / 2;                                                                 // odd paisa goes to CGST
    return new LineTax(taxable, tax - sgst, sgst, 0);
}
```

- `taxable = round(price * 10000 / (10000 + rate_bps))`, rounding half up, in integers only.
- `tax = price - taxable`, so taxable value plus tax always equals what the shopper paid, to the paisa.
- The odd paisa of a CGST and SGST split always goes to CGST (CA confirms the convention).
  Deterministic means the same input gives the same split on every machine and every re-run.
- Tax is computed per order line on the line's net value: unit price times quantity, minus the line's share of any discount.
  Never compute per unit and multiply, because the rounding error multiplies too.
- Order totals are sums of line values, and a unit test table pins every example below.

### Worked examples (arithmetic checked 2026-09-13)

**A. ₹1,18,000 at 18%.**
Price `11,800,000` paise, so `d = 11,800`.
Taxable value is `11,800,000 * 10,000 / 11,800 = 10,000,000` exactly, which is ₹1,00,000.
Tax is `1,800,000` paise, which is ₹18,000.
Same state: CGST ₹9,000 plus SGST ₹9,000.
Different state: IGST ₹18,000.

**B. ₹999 at 18%.**
Price `99,900` paise.
Taxable value is `99,900 * 10,000 / 11,800 = 84,661.02`, rounded to `84,661` (₹846.61).
Tax is `99,900 - 84,661 = 15,239` (₹152.39).
Same state: CGST `7,620` (₹76.20) plus SGST `7,619` (₹76.19).
Different state: IGST ₹152.39.

**Place of supply, illustrated** with a shop registered in Maharashtra (state code 27), since the real shop state is still an owner input.
Delivery to Pune (27) is CGST plus SGST.
Delivery to Bengaluru, Karnataka (29) is IGST.

## 4. Discounts are allocated across lines before tax

A coupon's discount reduces taxable value, so it is split across the eligible lines first, and each line is then taxed on its net value.
The invoice shows the discount (CA confirms the presentation).

Allocation uses the largest remainder method:
1. Each line's share is `floor(D * v_i / V)`, where `D` is the discount, `v_i` the line value and `V` the eligible total.
2. The leftover paise, always fewer than the number of lines, go one each to the lines with the largest remainder `D * v_i mod V`, ties to the lowest line number.
3. The discount is capped at `V`.

**Worked example.**
Line 1 is ₹2,999 at 18% (`299,900`), line 2 is ₹499 at an illustrative 5% (`49,900`), and the coupon is ₹500 (`50,000`), so `V = 349,800`.
- Line 1: `50,000 * 299,900 = 14,995,000,000`, divided by `349,800`, is `42,867` remainder `123,400`.
- Line 2: `50,000 * 49,900 = 2,495,000,000`, divided by `349,800`, is `7,132` remainder `226,400`.
- The floors sum to `49,999`, so 1 paisa is left, and line 2 has the larger remainder, so it gets `7,133`.
- Line 1 net `257,033`: taxable `round(2,570,330,000 / 11,800) = round(217,824.58) = 217,825`, tax `39,208`, CGST `19,604`, SGST `19,604`.
- Line 2 net `42,767`: taxable `round(427,670,000 / 10,500) = round(40,730.48) = 40,730`, tax `2,037`, CGST `1,019`, SGST `1,018`.
- Order: taxable `258,555` plus tax `41,245` is `299,800`, which is ₹3,498 minus ₹500, with every paisa accounted for.

## 5. The quote and order placement

- **`POST /api/v1/checkout/quote` is the single source of totals.**
  It reads current prices, stock, coupon, address and payment method.
  It returns every line (price, quantity, discount, taxable value, rate, HSN, tax parts), delivery and any COD fee, the total, and COD eligibility with a reason code.
  The cart stores no prices, and the UI does no maths.
- **`POST /api/v1/orders` requires an `Idempotency-Key` header and `expectedTotalPaise` in the body.**
  The server recomputes the quote, and if the total differs it returns 409 `price_changed` with the fresh quote and reserves nothing.
- The same key with the same body returns the first result and never creates a second order.
  The same key with a different body is refused.
- The order snapshots what it was sold with: product name, SKU, MRP, price, quantity, HSN, rate, tax parts, discount share, address, place of supply and the shop's state.
  Later catalog edits never change an order.
- Database CHECK constraints tie the totals together, so a wrong sum cannot be saved.
- Open question for the CA: how GST applies to delivery charges and COD fees on an order with mixed rates.
  The engine takes those fees as inputs with their own treatment, so the answer is configuration, not a rewrite.

## 6. Stock and reservations

Stock lives on the SKU: `inventory.stock` has `on_hand` and `reserved`, with `CHECK (on_hand >= 0 AND reserved >= 0 AND reserved <= on_hand)`.
Available to sell is `on_hand - reserved`.

| Reservation status | Meaning | Counter change |
| --- | --- | --- |
| `ACTIVE` | Held for an order not yet confirmed, with `expires_at` 30 minutes ahead for online payment | `reserved += n` when created |
| `COMMITTED` | Held for a confirmed order (COD placed, or payment verified), with no expiry | none |
| `RELEASED` | Given back after cancellation, expiry or failed placement | `reserved -= n` |
| `CONSUMED` | Shipped: the stock has left the shop | `on_hand -= n` and `reserved -= n` |

- Shipment consumes a committed reservation: `on_hand -= n` and `reserved -= n` together.
- Returns and RTO add stock back only after a quality check passes, as a stock movement.
  A failed check is a write-off movement.
- Admins never edit counters.
  Receipts, adjustments and write-offs are append-only `stock_movements` rows with a reason and an actor, applied in the same transaction as the counter change.

**Reserve with one conditional update, never read-then-write:**

```sql
UPDATE inventory.stock
   SET reserved = reserved + :qty
 WHERE sku_id = :skuId
   AND on_hand - reserved >= :qty;
```

Zero rows updated means out of stock, and the whole reservation rolls back.
Lock SKUs in sorted id order, so two orders never wait on each other in opposite order (a deadlock).
Sort in SQL or with the shared-kernel lock-order helper, not Java's `UUID.compareTo`, which can disagree with PostgreSQL's order.
The legacy code read stock and then updated it, so two buyers of the last unit could both succeed.

**Across services** (plan, decided 2026-09-13), because `inventory` and `order` never share a transaction:
1. `inventory.reserve(key, lines)` commits on its own, idempotent by key, and every reservation is born `ACTIVE` with an expiry, COD included.
2. `order` saves the order, as `CONFIRMED` for COD or `PENDING_PAYMENT` for online payment.
3. If the save fails, `inventory.release(reservationId)` compensates.
   A duplicate idempotency key on save is not a failure: the order already exists, so return it and release nothing.
4. For COD, `inventory.commit(reservationId)` follows the save.
5. Two safety nets, because `inventory` may never read order state (docs Rule 7):
   `order`'s expiry job takes `PENDING_PAYMENT` orders past their hold, asks `payment` for the latest status (payment asks Razorpay), then confirms and commits, or cancels and releases;
   `inventory`'s sweeper releases only `ACTIVE` reservations past their hold time plus a grace period, which catches reservations that never got an order.

Required tests: 50 threads buying the last 5 units create exactly 5 orders; a crash between any two steps leaks no stock once the job runs; concurrent admin adjustments never break the CHECK constraints.

## 7. The order state machine

| From | To | Trigger | Side effects |
| --- | --- | --- | --- |
| `PENDING_PAYMENT` | `CONFIRMED` | Payment verified | Reservation committed, confirmation email |
| `PENDING_PAYMENT` | `CANCELLED` | Expiry job after Razorpay check, or shopper | Reservation released |
| `CONFIRMED` | `PACKED` | Admin | none |
| `PACKED` | `SHIPPED` | Admin enters courier and AWB | Invoice issued, stock consumed, tracking email |
| `SHIPPED` | `DELIVERED` | Admin (manual at launch) | COD cash recorded as collected |
| `CONFIRMED` | `CANCELLED` | Shopper (before packing) or admin | Reservation released, full refund if paid |
| `PACKED` | `CANCELLED` | Admin | Reservation released, full refund if paid |
| `SHIPPED` | `RTO` | Admin, after the courier returns it | Credit note, stock back after check, refund if prepaid |
| `DELIVERED` | `RETURN_REQUESTED` | Shopper within the return window | none |
| `RETURN_REQUESTED` | `RETURNED` | Admin after receiving and checking | Credit note, stock back after check, refund |
| `RETURN_REQUESTED` | `DELIVERED` | Admin rejects the return | Email with the reason |

- One transition table in the `order` service and one `transition` method, and nothing else writes the order status.
- The write is conditional: `UPDATE ... SET status = :to, version = version + 1 WHERE id = :id AND status = :from`.
  Zero rows, or a pair missing from the table, returns 409 with a stable code.
- Every transition writes `order_status_history` (from, to, actor, reason, time) and its event in the same transaction; order's own listener then calls `AuditApi`, because audit is a separate service.
- Emails and refund requests go out through durable events after commit, with idempotent handlers.
- A test walks every from-to pair: legal pairs succeed, and every other pair returns 409.
- Not in the launch table yet: partial cancellation or return, and reshipping after RTO.
  Adding one starts with a change to `order-lifecycle.md`.

**Shipping and the invoice.**
No order may be `SHIPPED` without an invoice, and no invoice number is ever reused or deleted.
Recommended sequence: `invoice.issue(orderId)` (idempotent by order id), then consume stock (idempotent), then the `PACKED` to `SHIPPED` transition.
Retrying "ship" returns the same invoice, and a daily check flags any invoice whose order is not `SHIPPED`.
`order-lifecycle.md` has the final word.

## 8. Razorpay

1. **Create.** Insert a `payments` attempt row in a short transaction, then call Razorpay's Orders API outside any transaction.
   `amount` is the order's stored total, passed in by `order` (never from the browser), `currency` is `INR`, and `receipt` is our attempt id.
   Store the returned `razorpay_order_id`, one row per attempt.
   A network call inside a transaction would hold a database connection and row locks for seconds.
2. **Verify.** Checkout.js returns `razorpay_payment_id`, `razorpay_order_id` and `razorpay_signature`.
   Compute hex HMAC-SHA256 of `<razorpay_order_id from our attempt row>|<razorpay_payment_id>` with the key secret, and compare in constant time (`MessageDigest.isEqual`).
   Use our stored order id, never the one the browser sent.
3. **Confirm with Razorpay.** After the signature passes, fetch the payment and check `order_id`, `amount` equal to our total, `currency` INR and `status` `captured`.
   `authorized` is not paid yet.
   Any mismatch is flagged for an admin and never confirms the order.
4. **Webhooks.** Compute HMAC-SHA256 over the raw request bytes with the webhook secret, and compare it with `X-Razorpay-Signature` in constant time.
   Insert the event id (the `x-razorpay-event-id` header, confirmed against Razorpay's current docs) into `payment_events` under a unique constraint first, and a duplicate returns 200 and does nothing more.
5. **Converge.** The browser verification and the webhook both call the same idempotent `markPaid`, and whichever arrives first wins.
   Ten concurrent replays give exactly one transition and one email.
6. **Retry payment** before expiry creates a new attempt row.
   Set Checkout's `timeout` below the 30-minute reservation window.
7. **Reconcile and expire,** with ShedLock so a second instance is safe.
   `payment`'s reconciliation job asks Razorpay about attempts stuck for more than 30 minutes and publishes what it finds.
   `order`'s expiry job asks `payment` for each expired `PENDING_PAYMENT` order: a capture confirms the order, and no capture cancels it and releases stock.
8. **Late capture** after cancellation reaches `order` as a `PaymentCaptured` event; order tries to re-reserve with the conditional update.
   Success confirms the order, and failure asks `payment` to refund in full and emails the shopper why.
9. **A second capture** on an already confirmed order (two browser tabs) is refunded automatically.
10. **Refunds** (paid cancellation, RTO, return) write the `refunds` row before calling Razorpay.
    On retry, fetch the payment's existing refunds before creating another, and let `refund.processed` mark it done.
11. Missing Razorpay configuration stops the app from starting, so checks are never skipped.
    Razorpay's documented signature examples are unit tests.

## 9. Cash on Delivery

COD is allowed only when every rule holds, checked in the quote and again at placement:
- the account's email is verified;
- the order total is at or below the maximum COD order value (store setting, owner decides);
- the delivery pincode is serviceable and marked COD-capable;
- the shopper's open COD orders are below the cap (store setting).

The quote returns `codEligible` with a reason code, so checkout can explain a refusal.
Any COD fee is a quote line shown before the shopper picks a payment method, never added at the end.
An RTO on a COD order has nothing to refund, and stock returns after the check.

## 10. GST invoices and credit notes

- **When:** issued as part of `PACKED` to `SHIPPED`, because GST requires the invoice by the time goods leave.
- **Gapless numbering:** one `invoice_sequences` row per series and FY.
  Create it with `INSERT ... ON CONFLICT DO NOTHING`, then `SELECT ... FOR UPDATE`, increment, insert the invoice and commit, all in one transaction.
  Never use a Postgres `SEQUENCE`, which skips numbers on rollback, because GST numbers must be consecutive.
- **Financial year** is computed in `Asia/Kolkata` from an injected `Clock`, never the server's zone, because EC2 runs in UTC.
  `2027-03-31T18:29:59Z` is 23:59:59 IST on 31 March, so it belongs to FY 2026-27.
  `2027-03-31T18:30:00Z` is midnight IST on 1 April, FY 2027-28, so it gets `PK/27-28/000001`.
- **Format:** `PK/26-27/000123` is 15 characters.
  Rule 46 allows at most 16, using letters, digits, hyphen and slash, unique within the FY.
  A seventh digit still fits in exactly 16, and a CHECK enforces length and pattern.
- **Rule 46 fields:** supplier legal name, address and GSTIN; invoice number and date; buyer name and delivery address with state name and code (required for unregistered buyers at ₹50,000 or more, and we always print it); HSN; description; quantity and unit; total value; taxable value after discount; rate and amount of CGST and SGST (or UTGST), or IGST; place of supply with state name for inter-state sales; delivery address if different from place of supply; whether tax is payable on reverse charge (no); signature or digital signature.
- Amounts come from the tax parts stored on the order lines, and the template only formats them.
  Invoices render with Thymeleaf and OpenHTMLtoPDF into private S3, and every download checks ownership.
- **Credit notes:** a cancellation, RTO or return after an invoice exists gets a credit note referencing it.
  Credit notes use their own gapless series (proposed `CN/26-27/000012`, CA confirms) with the same locking.
  An issued invoice is never edited or deleted.
  Section 34 sets a deadline of 30 November after the FY ends, or the annual return date if earlier (CA confirms).
- **GSTR-1 export:** CSV with B2C summaries by place of supply and rate, large inter-state B2C invoices one by one, the HSN summary, credit notes and the document number ranges.
  Thresholds are settings, not code, and the CA reviews the first export.
- **Sign-off:** the CA approves HSN codes, rates, the template and a sample PDF before launch.
  Golden-file tests cover rounding and the 31 March IST boundary, and concurrent issuance leaves no gaps.

## 11. Coupons

- The quote validates a coupon, and placement enforces it under a row lock (`SELECT ... FOR UPDATE` on the coupon).
  Check the validity window, minimum order value, total uses and per-user limit, then insert the redemption and increment the count in one transaction.
- Redemption is idempotent by the placement key and compensated if placement fails, like a reservation.
- Test: 50 threads racing for the last 5 uses produce exactly 5 redemptions.
- Codes never live in the browser.
  The legacy site hard-coded them in JavaScript and never applied them to orders.

## 12. Consumer Protection (E-Commerce) Rules 2020 and dark patterns

- One total price with its breakdown (items, discount, delivery, fees, "inclusive of GST") before the shopper commits, matching the quote exactly.
- Seller legal name, address, GSTIN, customer care and grievance officer contacts in every footer.
  The grievance officer acknowledges a complaint within 48 hours.
- Product pages show country of origin, manufacturer or importer, and MRP, which Legal Metrology rules also require, so they are required admin fields.
- Returns, refunds, cancellation, warranty, delivery and payment-method policies are linked from product and checkout pages.
- Only real, verified-purchase reviews, no invented ratings, and MRP is the real MRP.
- Consent needs a deliberate action, so there are no pre-ticked boxes.
- The CCPA dark-pattern guidelines (2023) forbid false urgency, basket sneaking (adding a warranty or donation the shopper did not choose), drip pricing (revealing charges late), confirm-shaming and bait-and-switch.

## 13. Shipping (decided 2026-09-13)

- Manual at launch: an admin enters the courier and AWB when marking an order shipped, and the tracking link comes from the courier's URL template.
- The `shipping` service exposes a `ShippingProvider` interface with a manual implementation, so a Shiprocket adapter can replace it later without callers changing.
- Serviceability and delivery estimates come from the pincode directory table, not a courier API.
- The delivery fee rule is a store setting, computed only in the quote.

## Open questions (not decided)

- CA: GST on delivery and COD fees for mixed-rate orders; which rate applies if a rate changes between order and invoice; HSN digits; credit note series; GSTR-1 thresholds.
- Owner: maximum COD value, open-COD cap, COD fee, delivery fee, return window, and whether a cancelled order gives a coupon use back. Shop state is Uttar Pradesh (2026-09-17, decisions.md: "Business details for the site, invoices and legal pages").

## Checklist before you open a pull request

- [ ] Every amount is integer paise, with no float, double or decimal rupees anywhere in the change.
- [ ] Money is formatted only at display, with lakh grouping.
- [ ] No totals, tax or discount maths outside the quote and the pure tax engine.
- [ ] New tax or allocation cases are pinned in the unit table, and the worked examples still pass.
- [ ] Order creation keeps `Idempotency-Key`, `expectedTotalPaise` and 409 `price_changed`.
- [ ] Stock changes only through the conditional update, sorted locks and stock movements.
- [ ] Status changes only through the transition table, with history, audit and 409 on illegal moves.
- [ ] Razorpay: stored order id in the HMAC, raw-body webhook HMAC, constant-time compare, amount and currency checked, events deduplicated, no network call inside a transaction.
- [ ] Concurrency tests exist for any new contended resource (stock, coupon uses, invoice numbers).
- [ ] Invoice changes keep gapless numbering, IST financial years, the 16-character limit and Rule 46 fields, and the CA has seen template changes.
- [ ] Shopper-facing price display follows section 12.
- [ ] `make ci` passes locally with Docker running for Testcontainers.
- [ ] You say which command you ran, and never claim CI is green if it did not run.
