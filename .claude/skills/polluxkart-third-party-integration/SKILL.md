---
name: polluxkart-third-party-integration
description: Use when adding, changing or reviewing code that calls an outside vendor from PolluxKart (Razorpay, AWS SES, S3, Google sign-in, later Shiprocket or an SMS OTP provider), when receiving a vendor webhook, when adding a local stub for a vendor, or when deciding where a vendor key lives. Ends with the checklist for adding a new vendor.
---

# Calling outside vendors from PolluxKart

**Status: DRAFT (2026-09-13).**
Written before any application code exists, so every path and interface name below is the approved plan, not built code.
When the repository disagrees with this skill, the repository wins; fix this skill in the same pull request.

Sources: `docs/platform/architecture.md` (services and adapters), `docs/platform/decisions.md`, `docs/services/<service>/README.md` for each owning service, `docs/legacy/audit-2026-09.md` section 1.6.
Security rules for keys and webhooks are summarised here and stated in full in `polluxkart-security-checklist`.

## Words used below

- **Vendor:** an outside company whose service we call, such as Razorpay for payments.
- **Interface:** a Java type that lists what a component can do without saying how, so the code using it does not care which implementation runs.
- **Adapter:** the one class that implements our interface by talking to a specific vendor.
- **Stub:** a small fake server that answers like the vendor, so tests and local development need no real account.
- **Timeout:** the longest we wait for a vendor before giving up; without one, a slow vendor can freeze every request.
- **Idempotent:** safe to repeat, because doing it twice has the same effect as doing it once.
- **Backoff with jitter:** waiting longer after each failed try, plus a small random amount, so many retries do not hit the vendor at the same instant.
- **Database transaction:** a group of database changes that either all happen or none happen, holding a database connection until it ends.
- **Webhook:** a web request a vendor sends to our server to report an event, such as "payment captured".
- **Outbox:** a table where we write "this must be sent" inside our own transaction, which a job later sends, so a vendor call never sits inside the transaction.
- **SSM Parameter Store:** the AWS service holding production secrets, readable only by our server's AWS role.

## Vendors and who owns them (decided 2026-09-13)

| Vendor | Owning service | Our interface (planned) | Local stand-in | When |
|---|---|---|---|---|
| Razorpay | `payment` | `PaymentGateway` | Razorpay stub container | launch |
| AWS SES (email) | `notification` | `EmailSender` | Mailpit, a fake inbox with a web page | launch |
| AWS S3 (product images) | `media` | `MediaStore` | S3 mock container | launch |
| AWS S3 (invoice PDFs) | `invoice` | `InvoiceStore` | S3 mock container | launch |
| Google sign-in (OAuth) | `identity` | Spring Security `oauth2Login` configuration | mock OAuth server container | launch |
| Shiprocket | `shipping` | `ShippingProvider` (a manual implementation at launch) | stub | after launch |
| SMS OTP provider | `identity` | `OtpSender` | stub | after launch, once DLT registration (India's mandatory registry for SMS senders and templates) is done |

- Only the owning service calls its vendor; any other service asks the owner through the owner's `api` interface.
- All stand-ins run in `infra/compose/compose.yml`, started by `make up`.

## Rule 1: the backend holds every key

- Vendor secrets exist only on the API server, never in the browser, the Next.js bundle, or a `NEXT_PUBLIC_` variable.
- The browser receives only values the vendor documents as public, such as the Razorpay key id Checkout.js needs, and it gets them in an API response.
- Secrets live only in the local gitignored `.env` for development and in SSM Parameter Store for staging and production (decided 2026-09-13).
- AWS services (SES, S3) use the server's instance role, so no AWS access key exists in `.env`, SSM or anywhere else.

## Rule 2: one interface in the owning service, one adapter per vendor

The interface speaks our words and our types, and vendor types never leave the adapter's package.

```java
// api/payment/src/main/java/.../payment/internal/gateway/PaymentGateway.java
interface PaymentGateway {
    ProviderOrder createOrder(Money amount, PaymentAttemptId receipt);
    ProviderPayment fetchPayment(String providerPaymentId);
    ProviderRefund refund(String providerPaymentId, Money amount, RefundId refundId);
}
```

```java
// Wrong: a controller calls the vendor, and vendor JSON spreads into business logic
JsonNode rzp = razorpayClient.post().uri("/orders").body(Map.of("amount", req.amount())).retrieve().body(JsonNode.class);
order.setStatus(rzp.get("status").asText());

// Right: the controller calls the payment service, which calls PaymentGateway;
// only RazorpayPaymentGateway knows Razorpay's paths, field names and status strings
```

- The adapter lives in `internal/<vendor>/`, so Spring Modulith and ArchUnit fail the build if another service imports it.
- Money crosses the interface as paise in our `Money` type, and vendor status strings become our enums inside the adapter.
- Service logic is unit tested against an in-memory fake of the interface, and the adapter is tested against the stub.

## Rule 3: explicit timeouts, settings validated at boot

Java's HTTP client waits forever by default, so every client sets both timeouts from validated settings.

```java
@Bean
RestClient razorpayRestClient(RestClient.Builder builder, RazorpayProperties props) {
    HttpClient http = HttpClient.newBuilder().connectTimeout(props.connectTimeout()).build();  // time to open the connection
    JdkClientHttpRequestFactory factory = new JdkClientHttpRequestFactory(http);
    factory.setReadTimeout(props.readTimeout());                                               // time to wait for the answer
    return builder.baseUrl(props.baseUrl().toString())  // the stub locally and in CI, Razorpay's API in staging and production
            .requestFactory(factory)
            .defaultHeaders(h -> h.setBasicAuth(props.keyId(), props.keySecret()))
            .build();
}
```

- `RazorpayProperties` is a `@Validated` `@ConfigurationProperties` record, so a missing key, secret, URL or timeout stops the app at boot.
- The record overrides `toString()` to mask secrets, because a record prints every field by default.
- AWS SDK clients set `apiCallTimeout` and `apiCallAttemptTimeout` through `ClientOverrideConfiguration`, and use `endpointOverride` to point at the S3 mock locally.
- Starting values (tuned from real latency later): connect 2 seconds, read 10 seconds for Razorpay, 5 seconds for SES and S3.

## Rule 4: retry only what is safe to repeat

- Retry at most twice, with backoff and jitter, only on connection failures, 5xx responses and 429 (honouring `Retry-After`), and never on other 4xx.
- The total time spent retrying stays well under the timeout of the request that triggered the call.

| Call | Safe to repeat? | Policy |
|---|---|---|
| Razorpay fetch payment or order | yes, it only reads | retry |
| Razorpay create order | no idempotency key documented | no retry; the timed-out attempt row is closed and the shopper's next try creates a new one, since a Razorpay order nobody pays costs nothing |
| Razorpay refund | only with the idempotency mechanism Razorpay documents, confirmed when S6 is built | otherwise no retry; the reconciliation job checks refund status before trying again |
| SES send email | no, a retry may send twice | the outbox job retries later; a rare duplicate email is better than a lost order email |
| S3 put, key named by the file's hash | yes, the same key gets the same bytes | retry |
| Google sign-in code exchange | no, the code is single-use | no retry; the shopper signs in again |

## Rule 5: never call a vendor inside a database transaction

A vendor call inside a transaction holds a database connection for the whole network wait, so a slow vendor drains the connection pool and stops the store.
A rollback also cannot undo what the vendor already did.

```java
// Wrong
@Transactional
public PaymentAttempt start(Order order) {
    var attempt = attempts.save(PaymentAttempt.creating(order));
    var providerOrder = gateway.createOrder(order.total(), attempt.id());  // network wait with a connection held
    attempt.attachProviderOrder(providerOrder.id());
    return attempt;
}

// Right: short transaction, vendor call with no transaction, short transaction
public PaymentAttempt start(Order order) {
    var attempt = tx.execute(s -> attempts.save(PaymentAttempt.creating(order)));
    var providerOrder = gateway.createOrder(order.total(), attempt.id());
    return tx.execute(s -> attempts.attachProviderOrder(attempt.id(), providerOrder.id()));
}
```

- `tx` is Spring's `TransactionTemplate`, which makes each transaction's start and end visible in the code.
- Side effects that follow a business change, such as emails, go through an outbox table written in the same transaction, drained by a scheduled job.
- The outbox job claims rows in one short transaction, calls the vendor with none, and records the result in another.
- Spring Modulith's `@ApplicationModuleListener` opens its own transaction, so a listener that needs a vendor writes to the outbox instead of calling the vendor directly.

## Rule 6: webhooks are verified, stored raw, idempotent and convergent

- Verify the HMAC over the raw request bytes with a constant-time compare before reading anything (full code in `polluxkart-security-checklist`).
- Store the raw body as `bytea` or `text`, never only as `jsonb`, because `jsonb` reorders keys and the signature could no longer be checked again.
- `payment_events` has a unique constraint on provider plus provider event id, and a replay inserts nothing and changes nothing.
- Return 2xx quickly; slow work runs after the event is stored.
- A failed signature returns 400, is logged as event `webhook_signature_failed`, and raises an alarm (see `polluxkart-observability`).

**Converge to the same end state whichever arrives first (decided 2026-09-13).**
The shopper's browser verify call and Razorpay's webhook can arrive in either order, or at the same moment.
Both call one method, and a conditional update lets exactly one of them make the change.

```java
@Transactional  // database only: the payment was already fetched from Razorpay and its amount, currency and capture checked
public void markCaptured(PaymentAttemptId id, Money amount) {
    int changed = jdbc.update("""
            UPDATE payment.payments SET status = 'CAPTURED', captured_at = now()
            WHERE id = ? AND status IN ('CREATED', 'AUTHORIZED')""", id.value());
    if (changed == 1) {
        events.publishEvent(new PaymentCaptured(id, amount));  // one order confirmation, one email
    }
    // changed == 0: the other path got here first, which is already the end state we want
}
```

Required tests: verify-then-webhook and webhook-then-verify end in identical rows, and 10 concurrent replays of one event give exactly 1 transition and 1 email (see `polluxkart-testing`).

## Rule 7: stubs everywhere, so tests and CI need no secrets

- Where the stub speaks the vendor's own protocol (Razorpay stub, S3 mock, mock OAuth server), the real adapter runs everywhere and only its base URL changes.
- Google sign-in points Spring Security's issuer URI at the mock OAuth server locally and in CI.
- Email is the one case with two adapters, SMTP to Mailpit locally and the SES API in staging and production, chosen by a required setting such as `polluxkart.notification.email.transport`, never by a key happening to be absent.
- The SES adapter is covered by an integration test against a local HTTP stub, and by the SES mailbox simulator in the nightly staging run.
- GitHub Actions runs the whole suite with no vendor secret configured at all.

## Rule 8: test keys, live keys, and where each lives (decided 2026-09-13)

| Environment | Razorpay | Other vendors | Where the values live |
|---|---|---|---|
| Local | stub by default; your own test-mode keys only when testing real Razorpay | Mailpit, S3 mock, mock OAuth server | your gitignored `.env` |
| CI | stub | stubs | nothing secret needed |
| Staging | test-mode keys | real SES and S3, a staging Google OAuth client | SSM `/polluxkart/staging/` |
| Production | live keys | real services | SSM `/polluxkart/production/` only |

- The owner is setting up a new Razorpay merchant account (2026-09-13), and until its test keys exist, all payment work runs against the stub.
- Settings include an explicit mode, and boot fails if the key id does not match it: a `live` environment requires `rzp_live_`, and every other environment refuses `rzp_live_`.
- Keys are never pasted into issues, pull requests, chat, logs or test files.

## How to add a new vendor

1. Name the one service that owns the vendor, and write down why in `docs/platform/decisions.md` with the date.
2. Define the interface in that service in our own words and types, with no vendor types in any signature.
3. Write the adapter in `internal/<vendor>/`, with a validated settings record, explicit timeouts and a masked `toString()`.
4. Fill in the retry table for every call the adapter makes.
5. Confirm that no call runs inside a transaction, and use the outbox for side effects.
6. If the vendor sends webhooks, follow Rule 6 and add the replay and ordering tests.
7. Add a stub or mock container to `infra/compose/compose.yml`, and an in-memory fake for unit tests.
8. Add the setting names to `.env.example` with placeholders, and the SSM parameter placeholders to Terraform.
9. Add rotation steps to `docs/platform/runbook.md`, and alarms for failures that need a human.
10. If the browser loads a vendor script or frame, update the CSP only on the routes that need it.
11. Add the vendor to the privacy notice's processor list, and send it only the personal data it needs.
12. Update `docs/services/<service>/README.md` with the vendor, its failure behaviour, and its local stand-in.

## Checklist before you open a pull request

- [ ] The vendor is called only through its owning service's interface, and no vendor type crosses it.
- [ ] Every client has connect and read timeouts from a validated settings record, and secrets are masked in `toString()`.
- [ ] Only idempotent calls are retried, at most twice, with backoff and jitter, and the retry table is updated.
- [ ] No vendor call runs inside a database transaction or a transactional event listener.
- [ ] Webhooks verify the raw-byte HMAC in constant time, store the raw body, dedupe by provider event id, and converge with the verify path.
- [ ] `make ci` passes with no vendor secret present, using stubs only.
- [ ] Keys live only in local `.env` and SSM, the key-mode guard is in place, and no key appears in code, tests, logs or the pull request.
- [ ] Docs, runbook, `.env.example`, Terraform placeholders and the privacy processor list are updated for any new vendor.
- [ ] No em dash anywhere in the change.
