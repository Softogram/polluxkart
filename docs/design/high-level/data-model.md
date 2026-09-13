# Data model

Parent: [high-level/](README.md) | Index: [docs/](../../README.md)

**Status: APPROVED design, 2026-09-13. Tables are created slice by slice as Flyway migrations; none exist yet.**

## Conventions for every table (decided 2026-09-13)

- **One schema per service.** No foreign key or join crosses schemas; cross-service references are ids only. See [service-boundaries.md](service-boundaries.md).
- **Ids** are UUIDv7 (`uuid` columns defaulting to PostgreSQL 18's `uuidv7()`), so they sort roughly by creation time.
- **Money** is `bigint` paise. Never `float`, `double` or a decimal in JSON.
- **Tax rates** are `integer` basis points (1800 means 18%).
- **Time** is `timestamptz`. The server runs in UTC; dates that matter to people (invoice date, financial year) are computed in `Asia/Kolkata`.
- **Status** columns are `text` with a `CHECK` constraint listing allowed values, which is easier to change than a database enum type.
- **Mutable aggregates** carry a `version` column for optimistic locking (a check that nobody else changed the row since it was read).
- **Every invariant** that can be a constraint is one: `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys within a schema.
- **Extensions:** `citext` for case-insensitive emails and codes, `pg_trgm` for fuzzy search.
- **Roles:** `pk_migrator` changes the schema; `pk_app` reads and writes data and cannot update or delete audit rows.

## identity

| Table | Key columns and constraints |
|---|---|
| `users` | `email citext UNIQUE NOT NULL`, `email_verified_at`, `password_hash` (nullable for Google-only accounts), `full_name`, `phone`, `phone_verified_at` (kept for phone OTP later), `role CHECK IN ('CUSTOMER','ADMIN')`, `status CHECK IN ('ACTIVE','DISABLED','DELETED')`, `totp_secret_encrypted`, `version` |
| `user_identities` | `user_id`, `provider CHECK IN ('GOOGLE','PHONE')`, `provider_subject`, `UNIQUE (provider, provider_subject)` |
| `email_verification_tokens` | `user_id`, `token_hash UNIQUE`, `expires_at`, `consumed_at` |
| `password_reset_tokens` | `user_id`, `token_hash UNIQUE`, `expires_at`, `consumed_at` |
| `user_sessions` | `user_id`, `token_hash UNIQUE`, `idle_expires_at`, `absolute_expires_at`, `revoked_at`, `ip`, `user_agent` |
| `addresses` | `user_id`, name, phone, lines, city, `state_code` (GST state code), `pincode CHECK (pincode ~ '^[1-9][0-9]{5}$')`, `is_default` |
| `states` | GST state codes and names, seeded |
| `consents` | `user_id`, `purpose`, `policy_version`, `granted_at`, `withdrawn_at` |
| `data_requests` | `user_id`, `kind CHECK IN ('EXPORT','DELETE','CORRECT')`, `status`, timestamps |

## catalog

| Table | Key columns and constraints |
|---|---|
| `categories` | `parent_id` (within schema), `slug UNIQUE`, `name`, `default_hsn_code`, `default_gst_rate_bps` |
| `spec_attributes` | `category_id`, `key`, `label`, `data_type CHECK IN ('TEXT','NUMBER','BOOLEAN','ENUM')`, `unit`, `group_name`, `filterable`, `comparable`, `is_variant_axis`, `allowed_values`, `UNIQUE (category_id, key)` |
| `brands` | `slug UNIQUE`, `name` |
| `products` | `slug UNIQUE`, `brand_id`, `category_id`, `name`, `model_number`, `description_md`, `hsn_code CHECK (hsn_code ~ '^[0-9]{4,8}$')`, `gst_rate_bps CHECK (gst_rate_bps BETWEEN 0 AND 4000)`, `warranty_months`, `country_of_origin NOT NULL`, `manufacturer_or_importer NOT NULL`, `status CHECK IN ('DRAFT','PUBLISHED','ARCHIVED')`, generated `search tsvector`, `version` |
| `skus` | `product_id`, `sku_code UNIQUE`, `mrp_paise`, `price_paise`, `CHECK (price_paise > 0 AND price_paise <= mrp_paise)`, `weight_grams`, `is_active` |
| `sku_option_values` | `sku_id`, `attribute_id`, `value`, one value per axis per SKU |
| `product_specs` | `product_id`, `attribute_id`, `value_text`, `value_number`, `value_bool` |
| `product_images` | `product_id`, `sku_id` (nullable, for colour-specific images), `media_asset_id` (id from media), `alt_text NOT NULL`, `position` |

GST rates are stored per product rather than as a fixed list of slabs, because the slabs were rationalized in 2025 and can change again.

## media

| Table | Key columns and constraints |
|---|---|
| `media_assets` | `s3_key UNIQUE` (content-addressed), `content_type CHECK IN ('image/jpeg','image/png','image/webp','image/avif')`, `sha256`, `width`, `height`, `bytes`, `status CHECK IN ('PENDING','READY','REJECTED')`, `uploaded_by` |

## inventory

| Table | Key columns and constraints |
|---|---|
| `stock` | `sku_id PRIMARY KEY` (id from catalog), `on_hand`, `reserved`, `CHECK (on_hand >= 0 AND reserved >= 0 AND reserved <= on_hand)`, `version` |
| `stock_reservations` | `order_id`, `sku_id`, `quantity CHECK (quantity > 0)`, `status CHECK IN ('ACTIVE','COMMITTED','RELEASED','CONSUMED')`, `expires_at`, `idempotency_key`, `UNIQUE (order_id, sku_id)` |
| `stock_movements` | append-only: `sku_id`, `delta_on_hand`, `delta_reserved`, `reason CHECK IN ('RECEIPT','ADJUSTMENT','RESERVE','RELEASE','SALE','RETURN','RTO')`, `order_id`, `actor`, `note`, `created_at` |
| `pincodes` | `pincode PRIMARY KEY`, district, `state_code`, imported from the India Post directory |
| `shipping_zones` | zone rules: `min_days`, `max_days`, `cod_available`, `serviceable` |

### The reservation rule

Reserving stock is one conditional update per SKU:

```sql
UPDATE inventory.stock
   SET reserved = reserved + :quantity, version = version + 1
 WHERE sku_id = :sku_id
   AND on_hand - reserved >= :quantity;
```

If it changes zero rows, that SKU is out of stock and the whole reservation is rolled back.
SKUs are always processed in sorted id order, so two orders can never lock each other.

| Event | `on_hand` | `reserved` | Reservation status |
|---|---|---|---|
| Any order placed | unchanged | `+ quantity` | `ACTIVE`, with a hold time (30 minutes for online payment) |
| Cash on delivery order saved, or payment captured | unchanged | unchanged | `COMMITTED` |
| Order shipped | `- quantity` | `- quantity` | `CONSUMED` |
| Cancelled before shipping, expired by order's job, or orphaned and swept by inventory | unchanged | `- quantity` | `RELEASED` |
| Returned or RTO, after quality check | `+ quantity` | unchanged | stays `CONSUMED`, movement recorded |
| Admin receipt or adjustment | `+/- quantity` through a movement | unchanged | not applicable |

The database's `CHECK` constraint stops an admin adjustment from dropping `on_hand` below `reserved`.

## cart

| Table | Key columns and constraints |
|---|---|
| `carts` | `user_id UNIQUE` (nullable), `anonymous_token_hash UNIQUE` (nullable), `CHECK (user_id IS NOT NULL OR anonymous_token_hash IS NOT NULL)` |
| `cart_items` | `cart_id`, `sku_id`, `quantity CHECK (quantity BETWEEN 1 AND 10)`, `price_seen_paise` (only to tell the shopper a price changed), `UNIQUE (cart_id, sku_id)` |
| `wishlist_items` | `PRIMARY KEY (user_id, product_id)` |

The cart stores no price it will charge; the quote always uses current prices.

## orders

| Table | Key columns and constraints |
|---|---|
| `orders` | `order_number UNIQUE` from a sequence (for example `PK2609-00123`), `user_id`, `status`, `payment_method CHECK IN ('RAZORPAY','COD')`, `payment_status`, `subtotal_paise`, `discount_paise`, `shipping_paise`, `tax_paise`, `total_paise`, `CHECK (total_paise = subtotal_paise - discount_paise + shipping_paise)`, `CHECK (total_paise >= 0)`, address snapshot columns, `place_of_supply_state_code`, `is_interstate`, `coupon_code`, `version` |
| `order_items` | `order_id`, `sku_id`, snapshots of product name, variant, `hsn_code`, `gst_rate_bps`, `mrp_paise`, `unit_price_paise`, `quantity`, `line_discount_paise`, `taxable_paise`, `cgst_paise`, `sgst_paise`, `igst_paise`, `line_total_paise`, `CHECK (taxable_paise + cgst_paise + sgst_paise + igst_paise = line_total_paise)`, `CHECK ((igst_paise = 0) OR (cgst_paise = 0 AND sgst_paise = 0))` |
| `order_status_history` | `order_id`, `from_status`, `to_status`, `actor_type`, `actor_id`, `note`, `created_at` |
| `idempotency_keys` | `user_id`, `key`, `request_hash`, `response_body`, `expires_at`, `UNIQUE (user_id, key)` |

Prices include GST, so `total_paise` already contains `tax_paise`; the tax is shown as a breakdown, not added on top.

### The GST calculation rule

Calculated per order line, on the line's amount after its share of any discount.

1. `taxable_paise = round_half_up(line_amount_paise * 10000 / (10000 + gst_rate_bps))`
2. `tax_paise = line_amount_paise - taxable_paise`
3. Same state as the shop: `cgst_paise = ceil(tax_paise / 2)`, `sgst_paise = tax_paise - cgst_paise`. Another state: `igst_paise = tax_paise`.

Worked example, a phone at ₹1,18,000 including 18% GST:
- line amount 1,18,00,000 paise
- taxable = 1,18,00,000 x 10000 / 11800 = 1,00,00,000 paise (₹1,00,000)
- tax = 18,00,000 paise (₹18,000)
- same state: CGST ₹9,000 and SGST ₹9,000; another state: IGST ₹18,000

Worked example with an odd paisa, a cable at ₹999 including 18%:
- line amount 99,900 paise
- taxable = round_half_up(99,900 x 10000 / 11800) = round_half_up(84,661.02) = 84,661 paise
- tax = 15,239 paise
- same state: CGST 7,620 paise, SGST 7,619 paise

**Discounts** are split across lines in proportion to line amounts, rounded down, with leftover paise given one each to the lines with the largest remainders (ties by line order).

**To confirm with the chartered accountant before launch:** the rounding mode, which half receives the odd paisa, and whether shipping charges carry GST on the invoice.

## payment

| Table | Key columns and constraints |
|---|---|
| `payments` | `order_id`, `attempt_number`, `provider_order_id UNIQUE`, `provider_payment_id UNIQUE`, `amount_paise`, `currency CHECK (currency = 'INR')`, `status CHECK IN ('CREATED','AUTHORIZED','CAPTURED','FAILED')`, `UNIQUE (order_id, attempt_number)` |
| `payment_events` | `provider_event_id UNIQUE`, `event_type`, `raw_payload`, `signature_valid`, `received_at`, `processed_at`, `error` |
| `refunds` | `payment_id`, `provider_refund_id UNIQUE`, `amount_paise`, `status`, `reason` |

## invoice

| Table | Key columns and constraints |
|---|---|
| `store_settings` | legal name, GSTIN, address, `state_code`, invoice prefix, signature image, `version` |
| `invoice_sequences` | `financial_year PRIMARY KEY` (for example `2026-27`), `last_number` |
| `invoices` | `order_id UNIQUE`, `invoice_number UNIQUE` (for example `PK/26-27/000123`, at most 16 characters), `financial_year`, `sequence_number`, `UNIQUE (financial_year, sequence_number)`, seller and buyer snapshots, line snapshots, totals, `pdf_s3_key`, `pdf_sha256`, `issued_at` |
| `credit_notes` | `invoice_id`, own number and sequence, lines, totals, reason |

The next number is taken by locking the financial year's row in `invoice_sequences` inside the same transaction that writes the invoice, so numbers have no gaps.

## shipping

| Table | Key columns and constraints |
|---|---|
| `couriers` | `name UNIQUE`, `tracking_url_template` |
| `shipments` | `order_id`, `provider CHECK IN ('MANUAL','SHIPROCKET')`, `courier_id`, `tracking_number`, `packed_at`, `shipped_at`, `delivered_at`, `status` |

## promotion

| Table | Key columns and constraints |
|---|---|
| `coupons` | `code citext UNIQUE`, `kind CHECK IN ('PERCENT','FIXED')`, `value`, `min_order_paise`, `max_discount_paise`, `starts_at`, `ends_at`, `limit_total`, `limit_per_user`, `redeemed_count`, `CHECK (limit_total IS NULL OR redeemed_count <= limit_total)` |
| `coupon_redemptions` | `coupon_id`, `user_id`, `order_id UNIQUE` |

## review

| Table | Key columns and constraints |
|---|---|
| `reviews` | `product_id`, `user_id`, `order_item_id NOT NULL` (verified purchase), `rating CHECK (rating BETWEEN 1 AND 5)`, `title`, `body`, `status CHECK IN ('PENDING','PUBLISHED','REJECTED')`, `UNIQUE (user_id, product_id)` |
| `rating_summaries` | `product_id PRIMARY KEY`, `review_count`, `rating_total`, counts per star |

## notification

| Table | Key columns and constraints |
|---|---|
| `email_outbox` | `dedupe_key UNIQUE`, `template`, `recipient`, `payload`, `status CHECK IN ('PENDING','SENT','FAILED','SUPPRESSED')`, `attempts`, `next_attempt_at`, `provider_message_id` |
| `email_suppressions` | `email citext PRIMARY KEY`, `reason CHECK IN ('BOUNCE','COMPLAINT')`, `created_at` |

## audit

| Table | Key columns and constraints |
|---|---|
| `audit_log` | append-only: `actor_type`, `actor_id`, `action`, `entity_type`, `entity_id`, `before jsonb`, `after jsonb`, `request_id`, `ip`, `created_at` |

## Framework tables

`shedlock` (scheduled job locks) and Spring Modulith's `event_publication` (events awaiting delivery) live in a `platform` schema owned by the `app` module.

## See also (do not follow recursively)

- [order-lifecycle.md](order-lifecycle.md) - how order status and payment status change
- [../../product/compliance.md](../../product/compliance.md) - the invoice fields GST law requires
