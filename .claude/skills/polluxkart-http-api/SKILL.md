---
name: polluxkart-http-api
description: Use when adding or changing a REST endpoint, controller, request or response record, servlet filter, security rule, error response, pagination, or the OpenAPI spec in PolluxKart's Spring Boot API, or when deciding where a piece of request handling should live. Covers URL ownership, the filter order, cookie sessions, CSRF, admin paths, Problem Details errors, validation, Idempotency-Key, ownership checks and health endpoints.
---

# PolluxKart's HTTP API conventions (Spring Web MVC)

Source of truth this skill summarizes: `docs/platform/architecture.md` (API section), `docs/platform/security.md` and `docs/platform/decisions.md`.
If this skill and those documents disagree, the documents win - update this skill to match, do not guess.
No backend code exists yet, so every path under `api/` and `web/` below is planned.
Where controllers sit inside a service is in `polluxkart-architecture`; the error code catalogue is in `polluxkart-error-handling`; the security review list is in `polluxkart-security-checklist`.

## Words used here

- **REST endpoint**: one URL plus one HTTP method (`POST /api/v1/orders`) that the frontend calls.
- **Controller**: the Spring class whose methods handle endpoints.
- **Filter**: code that runs on every request before any controller, in a fixed order.
- **Caddy**: the web server in front of everything; it handles HTTPS and forwards each request to the API or the Next.js frontend.
- **CORS**: the browser rules for letting one website call another website's API; PolluxKart never needs them.
- **CSRF (cross-site request forgery)**: a trick where another website makes the customer's browser send a request to our API with the customer's cookie.
- **SameSite**: a cookie setting that tells the browser not to send the cookie on most requests started by other websites.
- **IDOR (insecure direct object reference)**: reading someone else's data just by changing an id or number in the URL.
- **Problem Details (RFC 9457)**: a standard JSON shape for error responses.
- **Bean Validation**: annotations such as `@NotBlank` on request fields, checked before the controller runs.
- **Idempotency key**: a unique value the client sends so that repeating a request performs the action only once.
- **OpenAPI**: a machine-readable description of every endpoint; **springdoc** generates it from our controllers.
- **Bucket4j**: a Java library that counts requests per key and rejects the excess (rate limiting).
- **Actuator**: Spring Boot's built-in endpoints for health checks.

## Spring Web MVC, not WebFlux (decided 2026-09-13)

One request is handled by one thread from start to finish.
JPA and JDBC block a thread per query anyway, so WebFlux's non-blocking model would add a second programming style with nothing gained.
Keeping one model keeps stack traces, transactions and the security context simple.
Do not add WebFlux, `Mono` or `Flux` to the API.

## URLs and who owns them

- Every endpoint lives under `/api/v1/`, and Caddy forwards `/api/*` to Spring Boot with the path unchanged.
- Each service owns its controllers in its `internal.web` package, and its URL prefixes are listed in `docs/services/<service>/README.md`.
  No two services share a prefix, so an extracted service is re-routed in Caddy without any URL changing.
- Paths use plural nouns (`/api/v1/orders/{orderNumber}`), and actions that are not plain create, read, update or delete become sub-resources (`POST /api/v1/orders/{orderNumber}/cancellation`).
- Admin endpoints live under `/api/v1/admin/**`, still inside the owning service (`catalog`'s `AdminProductController`).
- Payment provider webhooks live under `/api/v1/webhooks/**`.
- `GET` never changes state, because browsers send cookies on cross-site `GET` links.
- The API and the web app deploy separately, so for one release the new API must still serve the old web app.
  Add a field instead of renaming it, and remove the old one only after `web/` stopped reading it.

## Same origin, so no CORS (decided 2026-09-13)

Caddy serves `polluxkart.com` for both the pages and `/api/*`, so the browser sees one website.
There is no CORS configuration and no `@CrossOrigin` anywhere; adding one is a bug, because it is the only way another site could read our responses.
The local stack (planned `infra/compose/compose.yml`) also goes through Caddy, so there is no development-only CORS either.
The Next.js server calls `http://api:8080` directly inside the Docker network and forwards the customer's cookie, and on mutations the CSRF header too.

## The filter order is a contract

| # | Filter | Why it sits here |
|---|---|---|
| 1 | Request id | Every later log line, rejection and error body carries the same id |
| 2 | Security headers | Even an early 413 or 429 leaves with `nosniff`, `no-store` and a locked-down policy |
| 3 | Body size cap | An oversized body is refused before anything reads it |
| 4 | Rate limit (Bucket4j, keyed by client IP) | A flood is refused before it costs a database lookup |
| 5 | Session authentication | Hashes the cookie, loads the session and the user, sets `CurrentUser` |
| 6 | CSRF | Checks the token on every state-changing request before any controller runs |

- Filters 1 to 4 are plain servlet filters, registered with an order that runs before Spring Security's filter chain.
- Filters 5 and 6 live inside the security chain, with the session filter added before `CsrfFilter`.
- The exact header set and size cap are in `docs/platform/security.md`.
- Uploads never pass through the API: images go straight to S3 through a presigned POST, so the body cap stays small.
- The client IP comes from Tomcat's trusted-proxy handling (`server.forward-headers-strategy: native`), which believes `X-Forwarded-For` only from Caddy and the `web` container.
  Server-rendered pages would otherwise all share the `web` container's IP and one rate-limit bucket.

```java
@Bean
SecurityFilterChain api(HttpSecurity http, SessionAuthenticationFilter sessions, AdminAccess adminAccess,
                        ProblemResponses problems) throws Exception {
    return http
            .securityMatcher("/api/**")
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))   // no JSESSIONID
            .addFilterBefore(sessions, CsrfFilter.class)
            .csrf(csrf -> csrf
                    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                    .csrfTokenRequestHandler(new CsrfTokenRequestAttributeHandler())
                    .ignoringRequestMatchers("/api/v1/webhooks/**"))
            .authorizeHttpRequests(auth -> auth
                    .requestMatchers("/api/v1/admin/**").access(adminAccess)       // ADMIN role and TOTP passed
                    .requestMatchers(PublicEndpoints.MATCHERS).permitAll()
                    .anyRequest().authenticated())
            .exceptionHandling(e -> e
                    .authenticationEntryPoint(problems::unauthorized)
                    .accessDeniedHandler(problems::forbidden))
            .build();
}
```

The admin rule comes first and everything not listed as public requires a signed-in user, so a new endpoint is private by default.

## Rate limits (decided 2026-09-13)

- Bucket4j, held in memory, which is correct for the single API instance at launch.
- A global per-IP limit, plus tighter limits on login, password reset, verification email resend and order creation.
- Limits keyed by IP run in the filter; the order-creation limit is keyed by user, so it runs after authentication (planned as a handler interceptor).
- Buckets live in a size-bounded, expiring cache, so a flood of new IPs cannot exhaust memory.
- Over the limit returns 429 as Problem Details, with a `Retry-After` header.
- Every limited route has a test proving the request after the limit gets 429, because a limiter that is configured but never attached looks identical in review.
- A second API instance needs a shared bucket store first; that is recorded as a trigger, not built now.

## Sessions: opaque cookie, hash stored (decided 2026-09-13)

- On login the server creates 32 random bytes with `SecureRandom` and sends them, base64url-encoded, in the `__Host-pk_session` cookie (planned name).
- The cookie is `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, with no `Domain`.
  The `__Host-` prefix makes the browser refuse the cookie unless those settings hold, so no subdomain can set or overwrite it.
- The database stores only the SHA-256 hash of the token in `identity.user_sessions`, with the user id, expiry and revocation time.
  A leaked database or backup therefore contains no usable cookies.
  A fast hash is enough because the token is 256 random bits and cannot be guessed; passwords need slow hashing, tokens do not.
- Every request hashes the cookie, loads the active session and reloads the user; a disabled user or a changed role takes effect on the very next request.
- A new token is issued on login and on privilege change (TOTP step passed, password changed), and the old one is revoked.
- Logout revokes the session and clears the cookie; "log out everywhere" and password reset revoke every session of that user.
- Not a JWT in `localStorage` (decided 2026-09-13): any script on the page can read `localStorage`, and a JWT cannot be revoked before it expires.

```java
ResponseCookie cookie = ResponseCookie.from("__Host-pk_session", token)
        .httpOnly(true).secure(true).sameSite("Lax").path("/")
        .maxAge(sessionProperties.maxAge())
        .build();
response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
```

## CSRF on top of SameSite=Lax (decided 2026-09-13)

- Spring Security writes a readable `XSRF-TOKEN` cookie; the frontend copies it into an `X-XSRF-TOKEN` header on every `POST`, `PUT`, `PATCH` and `DELETE`.
- `SameSite=Lax` alone is not enough: browsers treat `media.polluxkart.com` and `staging.polluxkart.com` as the same site, so a flaw on any subdomain could still send the cookie.
- Use the cookie token repository with the plain (non-XOR) request handler, as Spring Security's single-page-app guide shows.
- Spring Security creates the token lazily, so the cookie appears only once something reads it; a small filter or a `GET` token endpoint (planned) forces it.
- Login and registration are CSRF-protected too, so another site cannot sign a customer into an attacker's account.
- Only `/api/v1/webhooks/**` is exempt: webhooks carry no cookie and prove who sent them with an HMAC signature (a keyed hash of the raw body), covered in `polluxkart-third-party-integration`.

## Admin paths: one door, checked by a sweep

- Every admin operation lives under `/api/v1/admin/**`, and the path rule requires an ADMIN whose session passed the TOTP step (authenticator app code).
- Never put an admin-only operation on a customer path, and never write `if (user.isAdmin())` inside a customer endpoint.
- A guard on one path to data must exist on every path to the same data; a second endpoint that returns the same rows needs the same check.
- Admin responses list their fields explicitly and never include password hashes, TOTP secrets or session tokens.
- A sweep test (planned) reads every mapped route from Spring's handler mappings and asserts each `/api/v1/admin/**` route returns 401 to an anonymous request and 403 to a customer, so a new admin route is covered without anyone remembering to add it.

## A controller's only job

Read the request into a request record, call this service's application service, and write a response record.
No business rules, no repositories, no entities, no other service's api.

```java
// WRONG: entity bound from JSON (the client can set status and total), repository in the controller, no ownership check
@PostMapping("/api/v1/orders")
OrderEntity place(@RequestBody OrderEntity order) { return orderRepository.save(order); }

@GetMapping("/api/v1/orders/{id}")
OrderEntity get(@PathVariable UUID id) { return orderRepository.findById(id).orElseThrow(); }

// RIGHT
@PostMapping("/api/v1/orders")
ResponseEntity<OrderResponse> place(@AuthenticationPrincipal CurrentUser user,
                                    @RequestHeader("Idempotency-Key") UUID idempotencyKey,
                                    @Valid @RequestBody PlaceOrderRequest body) {
    var command = new PlaceOrder(user.id(), idempotencyKey.toString(), body.cartId(), body.addressId(),
            body.paymentMethod(), body.expectedTotalPaise());
    return switch (placement.place(command)) {
        case Placed placed -> ResponseEntity.created(URI.create("/api/v1/orders/" + placed.order().number()))
                .body(OrderResponse.from(placed.order()));
        case PriceChanged changed -> throw OrderErrors.priceChanged(changed.quote());   // 409 price_changed with a fresh quote
        case OutOfStock out -> throw OrderErrors.outOfStock(out.shortfalls());          // 409 out_of_stock
    };
}

@GetMapping("/api/v1/orders/{orderNumber}")
OrderResponse get(@AuthenticationPrincipal CurrentUser user, @PathVariable String orderNumber) {
    return OrderResponse.from(orders.getForCustomer(user.id(), orderNumber));   // 404 when missing or not theirs
}
```

## Request records and validation

- Every body is a record with Bean Validation annotations, received as `@Valid @RequestBody`.
- Validation checks shape only: required, length, format.
  Business rules (is this PIN code serviceable, is Cash on Delivery allowed) live in the application service.
- A request record holds only what the client may set.
  Never `id`, `userId`, `role`, `status`, a price or a total to be trusted: identity comes from the session and prices from the database.
- An id in a body is checked for ownership like an id in a URL (the `addressId` in an order must belong to the caller).

```java
public record CreateAddressRequest(
        @NotBlank @Size(max = 80) String fullName,
        @NotBlank @Pattern(regexp = "[6-9][0-9]{9}") String mobile,
        @NotBlank @Size(max = 200) String line1,
        @Size(max = 200) String line2,
        @NotBlank @Pattern(regexp = "[1-9][0-9]{5}") String pincode,
        @NotBlank @Pattern(regexp = "[0-9]{2}") String gstStateCode) {}
```

## Errors: Problem Details from one place

- One `@RestControllerAdvice`, extending `ResponseEntityExceptionHandler`, maps every controller exception, including Spring's own (malformed JSON, missing header, wrong method).
- Filters and Spring Security's handlers run before that advice can see anything, so they write errors through the same mapping component (planned `ProblemResponses`), keeping one table of codes.
- Content type is `application/problem+json`.
- Fields: `type`, `title`, `status`, plus `code` (stable snake_case), `requestId` and, for field problems, `errors[]` with the JSON path the client sent.
- No `detail` field: free text is exactly where internal messages leak, so the frontend writes its own wording per `code`.
- The frontend branches on `code` only, never on `title` or the status alone.
- Raw exception messages, stack traces, SQL and class names never reach a client; an unexpected error returns a generic 500 and the full detail goes to the log under the same request id (`polluxkart-observability`).
- 401 means not signed in, 403 signed in but not allowed, 404 not found or not yours, 409 a conflict with current state; the full code catalogue and status table are in `polluxkart-error-handling`.

```json
{
  "type": "https://polluxkart.com/problems/validation_failed",
  "title": "Some fields are invalid",
  "status": 400,
  "code": "validation_failed",
  "requestId": "0192f0c4-5e1a-7d3b-9a61-3c2f8b1e4d77",
  "errors": [
    { "field": "pincode", "code": "invalid_format" }
  ]
}
```

## Idempotency-Key on orders and payments (decided 2026-09-13)

- `POST /api/v1/orders` and every payment mutation (create a payment attempt, verify, retry, refund) require an `Idempotency-Key` header holding a UUID.
- The frontend creates the key once per attempt and reuses it for retries and double clicks.
- A missing or malformed key is a 400.
- The key is stored in the owning service's `idempotency_keys` table, under UNIQUE `(user_id, idempotency_key)`, with a hash of the request body, in the same transaction as the order or payment it protects (`polluxkart-postgres-jpa`).
- A repeat with the same body returns the same status and body as the first call: no second order, no second charge.
- The same key with a different body is refused; the status and code are in `polluxkart-error-handling`.
- Two simultaneous requests with the same key resolve through the UNIQUE constraint: one creates, the other returns what the first created.
- Webhooks are deduplicated by the provider's event id, not by this header.

## Pagination, sorting and JSON shapes (convention set 2026-09-13)

- Page-numbered lists (storefront listings, admin tables): `?page=1&size=24`, 1-based, with a per-endpoint default and a maximum `size` of 100.
  Response: `{ "items": [...], "page": 1, "size": 24, "totalItems": 312, "totalPages": 13 }`.
- Append-only feeds that grow fast (audit log, stock movements): `?cursor=<opaque>&size=50`, answered with `{ "items": [...], "nextCursor": "..." }`, `null` on the last page.
- `sort` takes a name from an enum per endpoint (`price_asc`); an unknown value is a 400, and the database order always ends with the id so pages never shuffle.
- Filter parameter names match the frontend's URL parameters.
- Never serialize Spring Data's `Page`; its JSON shape is an internal detail Spring itself warns against exposing.
- Field names are camelCase, and every response field is always present, `null` when empty.
- Money is an integer number of paise in a field ending in `Paise` (`"totalPaise": 129900` is ₹1,299.00).
- Moments are ISO-8601 UTC strings (`"2026-09-13T10:30:00Z"`); business dates are plain dates (`"2026-09-13"`).

## Ownership checks on every read by id

Order numbers and invoice numbers are sequential, so anyone can guess the next one.

- Every customer read, update or download by id or number includes the owner in the same query: `WHERE number = :number AND user_id = :userId`.
- Not found and not yours return the same 404 with the same code, so a stranger cannot even learn that the order exists.
- Admins read other people's data only through `/api/v1/admin/**` endpoints, never through a role check inside a customer endpoint.
- Every such endpoint has an IDOR test (planned): customer B asks for customer A's order, invoice and address and gets 404 each time.

## OpenAPI: generated, committed, checked

- springdoc generates the spec from controllers and records; it is committed at `api/openapi/openapi.json`.
- A drift test (planned) regenerates the spec in the test profile and fails with "run `make gen-api`" if it differs from the committed file.
- `make gen-api` (planned) rewrites the spec and the frontend types (`openapi-typescript`), which the typed client in `web/src/lib/api/` uses through `openapi-fetch`.
- CI also fails if the generated types are stale, and `oasdiff` reports breaking changes against `development`.
- Every operation has a stable `operationId`, a tag naming its service, and its error responses documented as `application/problem+json`.
- Record components are required in the spec unless marked `@Nullable` (JSpecify, the null-safety annotations Spring 7 uses), enforced by a planned springdoc customizer.
- Swagger UI and `/v3/api-docs` are enabled only in the `local` and `test` profiles; the committed file is the published spec.

## Health endpoints

- **Public, minimal:** `GET /api/v1/health` returns `{"status":"UP"}` or 503 with `{"status":"DOWN"}`, and nothing else: no versions, no component names, no details.
- **Internal, detailed:** Actuator liveness and readiness run on a separate management port that Caddy never routes and Docker never publishes.
- Liveness says the process works and does not check the database, so a database blip does not restart the app.
- Readiness includes the database; `ops/deploy.sh` (planned) waits for it before sending traffic.
- Only `health` is exposed; `env`, `configprops`, `heapdump` and similar endpoints leak secrets and stay off.

```yaml
management:
  server:
    port: 8081                              # internal only (planned)
  endpoints.web.exposure.include: health
  endpoint:
    health:
      probes.enabled: true
      show-details: never
      group:
        readiness:
          additional-path: "server:/api/v1/health"   # the public minimal path on the main port
```

## Checklist before you open a pull request

- [ ] The endpoint sits under `/api/v1/` in the owning service's `internal.web`, and its prefix is in the service README.
- [ ] Admin operations are under `/api/v1/admin/**` only, and the admin sweep test still passes.
- [ ] No CORS configuration or `@CrossOrigin` was added.
- [ ] No `GET` changes state, and every state-changing endpoint is CSRF-protected (webhooks excepted).
- [ ] The controller takes a validated request record, calls only its own application service, and returns a response record, never an entity.
- [ ] The request record holds no field the client must not set (ids of the caller, roles, statuses, prices, totals).
- [ ] Every read by id or number checks ownership in the query, returns 404 for not-yours, and has an IDOR test.
- [ ] Every error path produces Problem Details with a stable `code` and `requestId`, including errors raised in filters.
- [ ] Order creation and payment mutations require `Idempotency-Key`, and a repeat returns the first response.
- [ ] Lists follow the pagination convention, cap `size`, and sort from an enum with an id tiebreaker.
- [ ] Money is integer paise ending in `Paise`, and moments are UTC ISO-8601 strings.
- [ ] New rate limits have a test that the next request gets 429.
- [ ] `api/openapi/openapi.json` and the generated frontend types were regenerated with `make gen-api` and committed.
- [ ] The change is backward-compatible with the currently deployed web app.
- [ ] `make ci` passes locally.
