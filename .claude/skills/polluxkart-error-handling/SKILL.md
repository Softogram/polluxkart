---
name: polluxkart-error-handling
description: Use whenever you write code that throws, catches, logs or translates an error in PolluxKart's Spring Boot API, add a new error code, map an error to an HTTP response, handle a failure from another service's interface or a vendor, add a setting that a check depends on, or make the Next.js frontend react to an API error.
---

# Error handling in PolluxKart

**Status: DRAFT (2026-09-13).**
Written before any application code exists, so every path below (`api/`, `web/`) is the approved plan, not built code.
When the repository disagrees with this skill, the repository wins; fix this skill in the same pull request.

Sources: `docs/platform/architecture.md` (service boundaries), `docs/platform/decisions.md` (the error format decision), `docs/legacy/audit-2026-09.md` sections 1.1, 1.6 and 3.4.
Service boundaries are described in `polluxkart-architecture`, and this skill holds the full error convention.
A `polluxkart-*` skill wins any disagreement with a vendored skill such as `problem-details-rfc9457`.

## Words used below

- **Exception:** Java's way of signalling that something went wrong; it travels up through the calling methods until some code catches it.
- **Error code:** a short, fixed, machine-readable string such as `price_changed` that names exactly one kind of failure.
- **Problem Details (RFC 9457):** a standard JSON shape for HTTP error responses, sent as `application/problem+json`; an RFC ("Request for Comments") is an internet standards document.
- **4xx and 5xx:** families of HTTP status codes, where 4xx means the caller sent something it can fix and 5xx means the server failed and we must fix it.
- **Enum:** a Java type with a fixed list of values, so the compiler can check that a `switch` covers every one.
- **Stack trace:** the list of method calls that led to an exception, useful to us and dangerous to show outsiders because it reveals how the code is built.
- **Controller advice (`@RestControllerAdvice`):** a Spring class whose methods catch exceptions thrown by any controller and turn them into responses.
- **Optimistic lock:** a version number on a row that makes a second, stale update fail instead of silently overwriting the first.
- **gRPC:** a protocol for one backend service to call another over the network; unused today, but a service may adopt it when it is split out.

## The rules on one screen

1. Every failure a client can meet has a stable error code owned by one service (decided 2026-09-13).
2. One central handler turns every error into Problem Details (decided 2026-09-13).
3. Clients never see raw exception text, class names, SQL, file paths or stack traces.
4. Each error is handled once: log it, or rethrow it, never both.
5. The frontend reads `code`, never `title` and never any message text.
6. Missing or invalid configuration stops the app at boot; code never skips a check because a setting is absent.

## The response shape

Every error from `/api/v1/**` looks like this, and nothing else.

```json
{
  "type": "https://polluxkart.com/problems/validation_failed",
  "title": "Some fields are invalid",
  "status": 400,
  "code": "validation_failed",
  "requestId": "0192f7c4-2b1e-7a3d-9c55-1f0e8a6b2d11",
  "errors": [
    { "field": "shippingAddress.pincode", "code": "invalid_format" },
    { "field": "items[0].quantity", "code": "out_of_range" }
  ]
}
```

- `type` is a fixed address per code that names the problem; clients never fetch it.
- `title` is a short English summary, identical every time that code occurs, meant for people reading logs and not for the UI.
- `code` is the stable value the frontend switches on.
- `requestId` equals the `X-Request-Id` response header and the `requestId` field in our logs (see `polluxkart-observability`).
- `errors` appears only for field problems, and `field` is the JSON path the client sent, so the Next.js form can show the message under the right input.
- A code may carry extra members declared for it in the OpenAPI spec, for example `price_changed` carries `quote`, the fresh quote the shopper must confirm.
- We never send `detail`, because free-text detail is exactly where internal messages leak.

## Typed error codes per service (decided 2026-09-13)

`shared-kernel` holds one exception type and the code contract; each service owns an enum listing every code it can produce.

```java
public interface ErrorCode {
    String code();              // stable wire value, for example "price_changed"
    ErrorCategory category();   // decides the HTTP status today and the gRPC status later
    String title();             // short English summary, the same for every occurrence
}

public class ServiceException extends RuntimeException {
    private final ErrorCode errorCode;
    private final List<FieldProblem> fieldProblems;  // record FieldProblem(String field, String code)
    private final Record details;                     // optional wire-safe record from the owning service's api package
    // the message passed to super(...) is for logs only and never reaches a client
}

public enum OrderErrorCode implements ErrorCode {
    PRICE_CHANGED("price_changed", ErrorCategory.FAILED_PRECONDITION, "Prices changed since your quote"),
    ILLEGAL_TRANSITION("illegal_transition", ErrorCategory.FAILED_PRECONDITION, "Order cannot move to that status"),
    OUT_OF_STOCK("out_of_stock", ErrorCategory.FAILED_PRECONDITION, "Some items are out of stock"),
    COD_NOT_AVAILABLE("cod_not_available", ErrorCategory.FAILED_PRECONDITION, "Cash on delivery is not available for this order");
    // constructor and accessors omitted
}
```

- A service may add small factories such as `OrderErrors.priceChanged(quote)`, so throw sites stay one line.
- A code is snake_case and unique across all services, checked by a test that scans every `ErrorCode` enum.
- A code is never renamed and never reused for a new meaning; a retired code stays in its enum, marked `@Deprecated`.
- Every code appears in the committed OpenAPI spec, so the generated TypeScript client knows the list and `oasdiff` flags a removed code as a breaking change.
- Add a new code only when the client would do something different with it.
  Otherwise use `CommonErrorCode`: `validation_failed`, `malformed_body`, `not_found`, `unauthenticated`, `forbidden`, `csrf_invalid`, `rate_limited`, `payload_too_large`, `unsupported_media_type`, `method_not_allowed`, `concurrent_update`, `service_unavailable`, `internal_error`.

**Some failures must not have their own code, because the code itself would reveal who has an account.**
Login returns `invalid_credentials` whether the email is unknown or the password is wrong.
Registration and password reset return the same success response whether or not the email exists, and the email we send tells the real owner what happened (audit section 1.1).
Asking for another user's order, invoice or address by id returns `not_found`, exactly like an id that does not exist (see `polluxkart-security-checklist`).

## Categories and status codes

| `ErrorCategory` | HTTP | gRPC status later | Use for |
|---|---|---|---|
| `INVALID_ARGUMENT` | 400 | `INVALID_ARGUMENT` | malformed JSON, failed field validation, missing `Idempotency-Key`, a key reused with a different body |
| `UNAUTHENTICATED` | 401 | `UNAUTHENTICATED` | no session, expired or revoked session, disabled user |
| `PERMISSION_DENIED` | 403 | `PERMISSION_DENIED` | logged in but not allowed, bad CSRF token, admin who has not passed TOTP |
| `NOT_FOUND` | 404 | `NOT_FOUND` | does not exist, or exists but belongs to someone else |
| `ALREADY_EXISTS` | 409 | `ALREADY_EXISTS` | a second review of the same product by the same shopper |
| `FAILED_PRECONDITION` | 409 | `FAILED_PRECONDITION` | illegal order state transition, `price_changed`, out of stock, coupon used up, COD not allowed |
| `CONFLICT` | 409 | `ABORTED` | lost an optimistic lock, or the same idempotency key is still being processed, so reload and retry |
| `RESOURCE_EXHAUSTED` | 429 | `RESOURCE_EXHAUSTED` | rate limited, always with a `Retry-After` header |
| `UNAVAILABLE` | 503 | `UNAVAILABLE` | database or vendor unreachable, so the same request may work later |
| `INTERNAL` | 500 | `INTERNAL` | a bug, meaning anything we did not expect |

- If the caller can change something and succeed, it is a 4xx; if no caller action could fix it, it is a 5xx.
- Every 5xx is logged at ERROR with its stack trace, exactly once, by the central handler.
- Never return 200 with an error inside the body, and never let a known business case reach `internal_error`.

**Why the gRPC column exists (decided 2026-09-13).**
Services are independent modules in one codebase and call each other through Java interfaces today.
When one is split out, its gRPC adapter sends the category's gRPC status, puts `code` in `google.rpc.ErrorInfo.reason` and field problems in `google.rpc.BadRequest`.
The client-side adapter rebuilds the same `ServiceException`, so no caller changes.

## One central handler

`ProblemResponses` (planned in `api/app/`) is the only code that builds an error body, and the controller advice routes every controller error through it.

```java
@RestControllerAdvice
class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(ServiceException.class)
    ResponseEntity<Object> service(ServiceException e) {
        return problems.of(e.errorCode(), e.fieldProblems(), e.details());  // expected: no stack trace, no ERROR log
    }

    @ExceptionHandler(AccessDeniedException.class)  // thrown by @PreAuthorize inside a controller
    ResponseEntity<Object> denied(AccessDeniedException e) {
        return problems.of(CommonErrorCode.FORBIDDEN);  // without this it would fall into the 500 branch below
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<Object> unexpected(Exception e) {
        log.error("unhandled exception", e);            // the one place a 500 is logged
        return problems.of(CommonErrorCode.INTERNAL_ERROR);
    }

    @Override  // Spring's own errors (405, 415, unreadable JSON, @Valid failures) arrive here
    protected ResponseEntity<Object> handleExceptionInternal(Exception ex, Object body, HttpHeaders headers,
            HttpStatusCode status, WebRequest request) {
        return problems.fromFramework(ex, status, headers);  // our code and shape; Spring's detail text is dropped
    }
}
```

`problems.of` builds a `ProblemDetail`, sets `type`, `title`, `code`, `requestId` from the MDC (the logging context, see `polluxkart-observability`), `errors` and the details record's fields, and returns it as `application/problem+json`.

**Four paths sit outside the controllers, so the advice never sees their errors.**
Each must call the same `ProblemResponses`, or clients get a second error format.

- Spring Security's `AuthenticationEntryPoint` writes 401 `unauthenticated`.
- Spring Security's `AccessDeniedHandler` writes 403 `forbidden`, or `csrf_invalid` for a CSRF token failure.
- The rate-limit filter writes 429 `rate_limited` with `Retry-After`.
- Spring Boot's fallback `/error` page, which catches anything thrown in a filter, is replaced to return `internal_error`, and these settings stay explicit:

```yaml
server:
  error:
    include-stacktrace: never
    include-message: never
    include-binding-errors: never
    include-exception: false
```

### Validation errors map to fields

Bean Validation failures (from annotations such as `@NotBlank` on request records) become `validation_failed` with one entry per field.

| Constraint | Field `code` |
|---|---|
| `@NotNull`, `@NotBlank`, `@NotEmpty` | `required` |
| `@Size` | `invalid_length` |
| `@Pattern`, `@Email` | `invalid_format` |
| `@Min`, `@Max`, `@Positive`, `@PositiveOrZero`, `@DecimalMin`, `@DecimalMax` | `out_of_range` |
| anything else | `invalid` |

- Field codes are stable and listed in the OpenAPI spec, like error codes.
- Never copy Bean Validation's default message or Jackson's parse message into a response.
- Unreadable JSON is `malformed_body` with no `errors` list, because Jackson's message names our Java classes.

## Handle each error once

Wrong: the failure is logged here, logged again by the central handler, and its original cause is thrown away.

```java
} catch (S3Exception e) {
    log.error("invoice upload failed for {}", invoiceId, e);
    throw new RuntimeException("S3 upload failed: " + e.getMessage());
}
```

Right: keep the cause, add context, and let the central handler log it once.

```java
} catch (S3Exception e) {
    throw new ServiceException(InvoiceErrorCode.STORAGE_UNAVAILABLE, "put failed for invoice " + invoiceId, e);
}
```

- "Handling" means recovering, for example the email outbox job catches a vendor timeout, logs one WARN, schedules a retry and does not rethrow.
- Never swallow an error with an empty `catch` or by returning `null`.
- Catch the specific exception you can handle, never a broad `Exception` in business code.
- Spring already logs an exception escaping a `@Scheduled` method, so jobs use the wrapper in `polluxkart-observability` instead of logging and rethrowing.

## Translating lower-level errors

Only a service's `internal` package ever sees JPA, JDBC, Hibernate or vendor SDK exceptions, and it translates them before they leave.

```java
try {
    reviews.saveAndFlush(review);  // flush now, so the constraint fails here and not at commit time
} catch (DataIntegrityViolationException e) {
    if ("reviews_user_product_uq".equals(ConstraintNames.of(e))) {
        throw new ServiceException(ReviewErrorCode.ALREADY_REVIEWED, "duplicate review", e);
    }
    throw e;  // an unexpected constraint is a bug, so it becomes a 500
}
```

- Match on the constraint name (naming rules in `polluxkart-postgres-jpa`), never on the database's message text.
- An optimistic lock failure becomes `concurrent_update`, and the client reloads and retries.
- A vendor timeout or 5xx becomes a code in the `UNAVAILABLE` category; the vendor's own error text goes to the log, never to the client.

## Errors across service boundaries

- **Expected outcomes the caller must branch on come back as data**, an outcome enum plus fields, as `polluxkart-architecture` requires.
- **Failures cross as `ServiceException` with a code**, never as a JPA, Jackson or vendor exception.
- Exception data is wire-safe (strings, numbers, enums, ids and records of those), so the contract round-trip test can serialize an error and rebuild it.
- Never rely on another service's failure rolling back your transaction, because that call may run in another process later.

```java
ReservationResult result = inventory.reserve(new ReserveStock(idempotencyKey, lines, 30));
ReservationId reservationId = switch (result.outcome()) {  // a new outcome breaks this build until handled
    case RESERVED -> result.reservationId();
    case INSUFFICIENT_STOCK -> throw OrderErrors.outOfStock(result.shortfalls());  // becomes 409 out_of_stock
};
```

## Configuration errors fail at boot

Wrong, and exactly how the first version shipped a payment webhook anyone could forge (audit section 1.6):

```java
if (webhookSecret == null || webhookSecret.isBlank()) {
    log.warn("webhook secret not set, skipping signature check");
    return true;
}
```

Right: a validated settings record, so the application refuses to start without the value.

```java
@Validated
@ConfigurationProperties("polluxkart.payment.razorpay")
public record RazorpayProperties(@NotNull URI baseUrl, @NotBlank String keyId,
                                 @NotBlank String keySecret, @NotBlank String webhookSecret) {}
```

- The `local` and `test` profiles point at the Razorpay stub with stub values, so no environment is ever "not configured".
- Never add a flag that turns a security check off, and never default a secret to an empty string.
- A test using Spring's `ApplicationContextRunner` proves the context fails to start when a required value is missing.

## The frontend reads codes

`ApiError` in `web/src/lib/api/errors.ts` carries `code`, `status`, `requestId` and field errors, and `explain(error)` turns a code into shopper wording (full rules in `polluxkart-frontend`).

- Branch on `code` only: `validation_failed` maps `errors[]` onto form fields with `setError`, and `price_changed` shows the fresh quote.
- An unknown code shows a generic sentence plus `requestId`, so a shopper can quote it to support.
- The UI never displays `title` and never branches on it.

## Checklist before you open a pull request

- [ ] Every new failure a client can meet has a code in its service's enum, listed in the regenerated OpenAPI spec.
- [ ] No new code duplicates a `CommonErrorCode`, and none reveals whether an account exists.
- [ ] The category follows the table: 409 for illegal transitions and `price_changed`, 429 with `Retry-After`, 404 for someone else's resource.
- [ ] No response contains `detail`, exception messages, class names, SQL or stack traces, and a test proves it for the 500 path.
- [ ] Security, rate-limit and fallback errors go through `ProblemResponses`, so every error has one shape.
- [ ] Validation failures return field paths and stable field codes the Next.js form can use.
- [ ] Each error is either logged or rethrown, never both, and every rethrow keeps its cause.
- [ ] Expected outcomes cross service interfaces as data, and no framework or vendor exception crosses at all.
- [ ] Every new setting a check depends on is validated at boot, with a test that startup fails without it.
- [ ] Frontend changes switch on `code` and show `requestId` for unknown errors.
- [ ] No em dash anywhere in the change.
