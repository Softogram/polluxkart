# Compliance: the rules an Indian online store must follow

Parent: [product/](README.md) | Index: [docs/](../README.md)

**Status: DRAFT (2026-09-13).**
This is an engineering checklist, not legal advice.
The legal pages need a lawyer's review, and the invoice needs a chartered accountant's sign-off, before launch.

## Glossary

- **GST (Goods and Services Tax):** India's tax on sales.
- **GSTIN:** the shop's 15-character GST registration number.
- **HSN code:** the tax category code for a product, 4 to 8 digits.
- **CGST, SGST, IGST:** central, state and integrated GST. A same-state sale splits the tax into CGST and SGST; a sale to another state charges IGST.
- **MRP (Maximum Retail Price):** the highest price a packaged product may be sold for in India.
- **DPDP Act:** the Digital Personal Data Protection Act, 2023, India's data protection law.
- **CCPA:** the Central Consumer Protection Authority, which issues consumer protection guidelines.

## 1. Pages the store must publish

Razorpay reviews the website before activating a merchant account, and consumer protection rules expect these to be easy to find.

| Page | Path (planned) | Must contain |
|---|---|---|
| About | `/about` | Who runs the store |
| Contact | `/contact` | Email, phone, registered address |
| Grievance officer | `/grievance` | Name, designation, contact; acknowledges complaints within 48 hours and resolves within one month |
| Terms and conditions | `/terms` | Terms of sale and use |
| Privacy policy | `/privacy` | What data is collected, why, who processes it, how to exercise rights |
| Returns and refunds | `/returns-refunds` | Return window, condition, refund method and timeline |
| Cancellation | `/cancellation` | When and how an order can be cancelled |
| Shipping and delivery | `/shipping-delivery` | Delivery areas, times, fees, cash on delivery rules |
| Warranty | `/warranty` | How brand warranty claims work |

The footer of every page shows the seller's legal name, address, GSTIN and contact details.

## 2. Consumer Protection (E-Commerce) Rules, 2020

- Seller details (legal name, address, GSTIN, contact) visible on the site.
- A grievance officer with the timelines above.
- Return, refund, exchange, warranty, delivery and payment terms shown before purchase.
- Country of origin shown on each product page.
- The total price shown as a single figure with its breakdown before payment.
- No pre-ticked consent boxes.
- No manipulated prices or fake reviews.

## 3. Legal Metrology (Packaged Commodities) Rules

- MRP, manufacturer or importer name and address, and country of origin are required fields when an admin creates a product.
- The selling price never exceeds MRP; the database enforces it.

## 4. CCPA guidelines on dark patterns, 2023

The store never uses:
- False urgency ("only 2 left" when it is not true, fake countdown timers).
- Drip pricing (fees revealed only at the last step).
- Basket sneaking (adding items or donations without asking).
- Confirm shaming (guilt-tripping text on a "no thanks" button).
- Fake reviews or ratings.

## 5. GST invoices

- The invoice is issued when goods leave the shop, which the system treats as the moment an order is marked shipped.
- Invoice numbers are sequential with no gaps within a financial year (April to March), unique, and at most 16 characters.
- The invoice carries the fields GST Rule 46 requires: supplier name, address and GSTIN; invoice number and date; buyer name and address; place of supply; HSN code, description, quantity, taxable value, rate and tax amounts per line; total; signature.
- Cancellations or returns after invoicing produce credit notes, not edited invoices.
- Monthly data for the GSTR-1 return is exported for the accountant.
- Invoices are kept for the retention period GST law requires, even when a shopper deletes their account.
- E-invoicing (IRN generation) applies only above a turnover threshold and is out of launch scope.

The calculation rules live in [../design/high-level/data-model.md](../design/high-level/data-model.md).

## 6. DPDP Act, 2023

- A plain-language notice at sign-up and in the privacy policy listing what is collected, why, and which processors see it (AWS, Razorpay, Google, error monitoring).
- Consent for marketing is separate from what is needed to fulfil an order, and withdrawing it is as easy as giving it.
- Shoppers can download their data, correct it, and delete their account.
- A named contact for data requests.
- A breach response runbook and a data retention schedule.
- Personal data never appears in logs.

## 7. Payments

- Razorpay requires the pages in section 1 on the registered website, visible products and prices in rupees.
- Card data never touches our servers; Razorpay's checkout handles it.
- Refunds go back through Razorpay to the original payment method.

## See also (do not follow recursively)

- [../platform/security.md](../platform/security.md) - how personal data is protected in the system
- [../services/invoice/README.md](../services/invoice/README.md) - the service that issues invoices
