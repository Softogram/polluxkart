---
name: polluxkart-security-checklist
description: Use when writing or reviewing anything in PolluxKart that touches sessions, login, password reset, Google sign-in, admin routes, a by-id read, uploads, payment webhooks, prices or totals, rate limits, browser security headers, secrets, dependencies or personal data, and before any security review or OWASP walkthrough. Holds the "second door" rule and the full checklist table.
---

# Security checklist for PolluxKart

**Status: DRAFT (2026-09-13).**
Written before any application code exists, so every path and route below is the approved plan, not built code.
When the repository disagrees with this skill, the repository wins; fix this skill in the same pull request.

Sources: `docs/platform/security.md` (the full policy and limit values), `docs/platform/decisions.md`, `docs/legacy/audit-2026-09.md` sections 1 and 2 (every rule here answers a real hole in the first version).

## Words used below

- **Session token:** a long random string the server gives the browser at login, which proves who is calling on later requests.
- **Hash:** a one-way fingerprint of a value, so the database can check a token without storing the token itself.
- **httpOnly cookie:** a cookie the browser sends to the server but page scripts cannot read, so injected JavaScript cannot steal it.
- **IDOR (Insecure Direct Object Reference):** changing an id in a request shows or changes someone else's data.
- **CSRF (Cross-Site Request Forgery):** another website making the shopper's browser send a request to our API with the shopper's cookies.
- **CSP (Content Security Policy):** a response header that tells the browser which scripts, images and frames a page may load.
- **HMAC:** a code computed from a message and a shared secret, proving the message came from someone who knows the secret.
- **TOTP (Time-based One-Time Password):** the six-digit code an authenticator app shows, which changes every 30 seconds.
- **OAuth and PKCE:** OAuth is the standard behind "Sign in with Google"; PKCE (Proof Key for Code Exchange) stops a stolen sign-in code from being used by anyone else.
- **Magic bytes:** the first few bytes of a file, which reveal its real type whatever its name or claimed type says.
- **Presigned POST:** a short-lived, limited permission we sign so a browser can upload one file straight to S3 (Amazon's file storage).
- **SSM Parameter Store:** the AWS service holding production secrets, readable only by our server's AWS role.
- **DTO (Data Transfer Object):** a class that exists only to shape what the API sends or receives.
- **PII (Personally Identifiable Information):** data that identifies a person, such as name, email, phone or address.
- **DPDP Act 2023:** India's Digital Personal Data Protection Act, the law on collecting and handling personal data.

## The second door rule (decided 2026-09-13)

**If one path to some data is guarded, every other path to the same data needs the same guard.**
**A comment claiming a guard is not a guard, and a hidden button is not a guard.**
Real examples of a second door to look for:

- Order detail checks ownership, but the invoice PDF download by invoice id does not.
- The address book checks ownership, but `POST /api/v1/checkout/quote` accepts any `addressId`.
- Product editing sits under `/api/v1/admin/`, but a bulk import route was added somewhere else.
- The admin page hides a button from customers, but the API route behind it has no role check.
- A method carries `// only called by admins` and nothing enforces it.

When you add or change a guard, search every controller, export, download and Next.js server route that reads the same table, and add a test for each path.

## Sessions: verify on every request (decided 2026-09-13)

- The session is 32 random bytes from `SecureRandom`, sent as `__Host-pk_session` with `Secure`, `HttpOnly`, `SameSite=Lax` and `Path=/`.
- The `__Host-` prefix makes the browser refuse the cookie unless it is secure, has no domain and has path `/`, so a subdomain cannot overwrite it.
- `user_sessions` stores only the SHA-256 hash; a fast hash is safe here because the token is random, unlike a password.
- A new token is issued at login and after TOTP verification, and logout deletes the row.
- Password change and password reset revoke every session of that user.

```java
// Wrong (the first version): the role was frozen into a token at login and trusted for 24 hours
String role = token.getClaim("role");

// Right: look the session up and reload the user on every request
Optional<AuthenticatedUser> resolve(String rawToken) {
    var session = sessions.findActiveByHash(sha256(rawToken), clock.instant());  // checks expiry and revocation
    if (session.isEmpty()) return Optional.empty();
    return users.findById(session.get().userId())
            .filter(User::isActive)                                                // a disabled user fails the next request
            .map(u -> new AuthenticatedUser(u.id(), u.role(), session.get().totpVerified()));  // role read now
}
```

Never cache the user between requests; one indexed query per request is cheap, and a cache brings stale roles back.

## Authorization

Deny by default, and guard the whole admin tree with one rule.

```java
http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/api/v1/admin/**").access(adminWithVerifiedTotp)   // every admin route, one rule
        .requestMatchers(HttpMethod.GET, "/api/v1/categories/**", "/api/v1/products/**", "/api/v1/brands/**",
                "/api/v1/search", "/api/v1/delivery-estimate").permitAll()
        .requestMatchers(HttpMethod.POST, "/api/v1/auth/login", "/api/v1/auth/register").permitAll()
        .requestMatchers(HttpMethod.POST, "/api/v1/webhooks/**").permitAll()  // the HMAC is their guard
        .requestMatchers(HttpMethod.GET, "/api/v1/health").permitAll()
        .anyRequest().authenticated());                                      // anything not listed needs a session
```

- Every admin route lives under `/api/v1/admin/`, with no exceptions.
- A generated test reads every `/api/v1/admin/**` route from Spring's route registry, calls each with no session (expects 401) and as a verified customer (expects 403), and fails if it finds no routes (see `polluxkart-testing`).
- Every by-id read or write of an owned resource puts the owner in the query itself.

```java
// Wrong: any logged-in shopper can read any order by changing the id
Order order = orders.findById(orderId).orElseThrow(OrderErrors::notFound);

// Right: "not yours" looks exactly like "does not exist", so ids cannot be probed
Order order = orders.findByIdAndCustomerId(orderId, caller.userId()).orElseThrow(OrderErrors::notFound);
```

- Owned resources include orders, invoices, credit notes, payments, addresses, carts, wishlists, reviews and data export files, and each has an IDOR test.
- Request records never bind straight to entities, so a shopper sending `"role": "ADMIN"` changes nothing.
- Search and every other query use bound parameters, never SQL built from strings.

## Admin accounts

- Every admin route requires TOTP verified in the current session, or returns 403 `totp_required` (decided 2026-09-13).
- TOTP secrets are encrypted at rest with a key from SSM, the last used time step is stored so a code cannot be reused, and attempts are rate limited.
- No debug, setup, seed or data-wipe endpoint exists in any environment, staging included.
- The first admin is created by a one-off CLI command run on the server through SSM Session Manager, never over HTTP (decided 2026-09-13).
- That command creates the user with no password and sends a reset email, so no password lands in shell history, and it writes an audit log row.
- Every admin write records who, what and when in `audit_log`, which the app's database role cannot update or delete.

## Passwords, reset and Google sign-in

- Passwords are hashed with a slow password hash (Argon2id or bcrypt, chosen and dated in `docs/platform/decisions.md` when identity is built) through Spring Security's `DelegatingPasswordEncoder`, never SHA-256.
- Login returns the same `invalid_credentials` for an unknown email and a wrong password, and still runs a hash check for an unknown email so the response time gives nothing away.
- Password reset uses a single-use token stored as a hash, valid 30 minutes, which revokes every session when used (decided 2026-09-13).
- Reset and registration give identical responses whether or not the email exists.
- Email verification tokens are hashed, single-use and expiring too.
- Google sign-in uses Spring Security's `oauth2Login` with PKCE, `state` and `nonce`, never a hand-written token check.
- A Google identity is keyed by its stable `sub` claim in `user_identities`, never by email alone after the first link.

**Account linking rule (decided 2026-09-13).**
Google must report `email_verified=true`, or sign-in is refused.
If a local account already has that email, the Google identity is linked to it.
If that local account never verified its email, its password is wiped and its sessions revoked, because someone may have registered the shopper's email first to plant a password.
After sign-in, a `returnTo` target must be a relative path on our own site, so a link cannot bounce the shopper to an attacker's site.

## Rate limits (decided 2026-09-13)

Bucket4j, a Java rate-limiting library, counts requests in memory on our single instance.
Values live in `docs/platform/security.md`; every refusal is 429 `rate_limited` with `Retry-After`.

| Endpoint | Counted per | Stops |
|---|---|---|
| Login | IP and email | password guessing |
| Password reset request | IP and email | email flooding, account probing |
| Verification email resend | user | email flooding and SES reputation damage |
| TOTP check | user | guessing six-digit codes |
| Order creation | user and IP | stock hoarding, COD abuse |
| Everything | IP | scraping and floods |

- The client IP comes from `X-Forwarded-For`, which Caddy (our HTTPS web server) overwrites, and Spring trusts it only from Caddy's network via `server.tomcat.remoteip.internal-proxies`.
- In-memory buckets are correct for one instance only; adding a second instance requires a shared store first, recorded in the ADR.

## Browser protections

- **CSRF:** Spring Security's cookie token plus request header on every POST, PUT, PATCH and DELETE, on top of `SameSite=Lax`; the exact setup is confirmed in the API foundation pull request.
- The Next.js server forwards the CSRF header when it calls the API for the shopper, and the only exempt route is the webhook, matched by exact path.
- **CSP (decided 2026-09-13):** static on catalog pages, nonce-based on checkout, account and admin, where a nonce is a random value per response that marks which inline scripts are ours.
- CSP always includes `default-src 'self'`, `object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'` and `img-src 'self' https://media.polluxkart.com`.
- Razorpay's Checkout.js script and frame hosts are allowed on `/checkout` only, and only first-party scripts load anywhere else.
- Other headers: `Strict-Transport-Security` in production, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` (`no-referrer` on pages whose URL carries a token), and `Cache-Control: no-store` on authenticated API responses.
- The Next.js internal revalidate route is reachable only on the Docker network and still checks its shared secret with a constant-time compare.

## Uploads (decided 2026-09-13)

1. An admin asks the API for a presigned POST limited to one pending key, a maximum size and an `image/` content type, valid for minutes.
2. The browser uploads straight to a private `pending/` prefix that nobody can read publicly, and a lifecycle rule deletes leftovers.
3. The admin confirms, and the media service reads the first bytes from S3 and checks magic bytes: JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `RIFF....WEBP`, AVIF `ftypavif` or `ftypavis`.
4. Anything else is rejected and deleted, including SVG, which can carry scripts, and HTML renamed to `.png`.
5. A valid file is copied to a key named by its SHA-256 hash, with `Content-Type` set by the server from the detected type.
6. Images are served only from `media.polluxkart.com`, never from the API or storefront domain, so a bad file can never run as our page.

## Payments: webhooks and prices

The webhook HMAC is computed over the exact bytes received, never over re-serialized JSON, which is how the first version broke (audit section 1.6).

```java
@PostMapping("/api/v1/webhooks/razorpay")
ResponseEntity<Void> webhook(@RequestBody byte[] rawBody,
                             @RequestHeader("X-Razorpay-Signature") String signature,
                             @RequestHeader("X-Razorpay-Event-Id") String eventId) throws GeneralSecurityException {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(props.webhookSecret().getBytes(UTF_8), "HmacSHA256"));
    byte[] expected = HexFormat.of().formatHex(mac.doFinal(rawBody)).getBytes(US_ASCII);
    if (!MessageDigest.isEqual(expected, signature.getBytes(US_ASCII))) {  // constant time: no timing hints
        throw PaymentErrors.webhookSignatureInvalid();                       // 400, logged as event webhook_signature_failed
    }
    webhooks.recordIfNew(PROVIDER_RAZORPAY, eventId, rawBody);             // unique event id: a replay changes nothing
    return ResponseEntity.ok().build();
}
```

- A missing webhook secret stops the app at boot (see `polluxkart-error-handling`).
- The checkout verify call checks Razorpay's signature the same way, then fetches the payment and confirms amount, currency, order id and capture before confirming anything.
- **Never trust a price, discount, shipping fee, tax or total sent by the client.**

```java
// Wrong: the browser decides what we charge
gateway.createOrder(request.totalPaise());

// Right: the server computes the quote; the client's number is only a check that nothing moved
Quote quote = checkout.quote(caller, request.cartId(), request.addressId(), request.couponCode());
if (quote.totalPaise() != request.expectedTotalPaise()) throw OrderErrors.priceChanged(quote);  // 409 with the fresh quote
```

## Responses: allowlists, never blocklists

The first version removed a field called `password` while the stored field was `password_hash`, and leaked every hash (audit section 1.5).

```java
// Wrong: returns the entity, so every field added later leaks too
return userRepository.findAll();

// Right: a record listing exactly what the screen needs
public record AdminUserView(UUID id, String email, Role role, UserStatus status, Instant createdAt) {
    static AdminUserView from(User u) { return new AdminUserView(u.id(), u.email(), u.role(), u.status(), u.createdAt()); }
}
```

- No JPA entity is ever returned from a controller, enforced by an ArchUnit rule (a test that checks code structure).
- A test asserts the exact set of JSON keys for every response that describes a user, so a new field needs a deliberate test change.
- Actuator (Spring Boot's operations endpoints) exposes only `health`, on an internal port Caddy never routes to, because `heapdump` and `env` contain secrets and session tokens.

## Secrets (decided 2026-09-13)

- Production and staging secrets live only in SSM Parameter Store under `/polluxkart/<environment>/`, and each server's role reads only its own environment.
- Locally, secrets live only in a gitignored `.env`; `.env.example` is committed with names and placeholder values only.
- No AWS access keys exist anywhere: the server uses its instance role, and GitHub Actions deploys through OIDC (short-lived credentials GitHub requests per run).
- `gitleaks`, a secret scanner, runs in the pre-commit hook (`gitleaks git --pre-commit --staged`, the form that replaced the older `gitleaks protect`) and in `make ci`, through `tools/secrets/scan.py`.
- A false alarm is allowed only by an entry in `.gitleaks.toml` with a description starting `YYYY-MM-DD:` and a reason. Inline `gitleaks:allow` comments are refused.
- **Any secret that ever reaches a commit is public, and is rotated the same day**, whether or not the commit was pushed; follow the rotation steps in `docs/platform/runbook.md`.
A key the pre-commit hook blocked before any commit existed only needs removing (owner decision, 2026-09-14).
- A settings record holding a secret overrides `toString()`, because a Java record prints every field by default and one debug log would expose it.

## Dependencies

- `osv-scanner`, a vulnerability scanner, checks the Maven dependencies and `web/pnpm-lock.yaml` in `make ci`.
- Dependabot opens weekly update pull requests, and CodeQL, GitHub's code scanner, runs in Actions.
- `pnpm audit --prod` is a quick local second opinion for the frontend.
- A high or critical finding is fixed before merge, and any ignore entry carries a dated reason.

## Personal data and the DPDP Act

- No PII, tokens, cookies, signatures or presigned URLs in logs; log ids instead (see `polluxkart-observability`).
- Collect only what an order, invoice or delivery needs, and show admins only what the task needs.
- The privacy notice lists every processor (Razorpay, AWS, Google, Sentry) in plain language.
- Marketing consent is separate from service consent and never pre-ticked, recorded in `consents`.
- Access, correction and erasure requests go through `data_requests`, and erasure anonymises personal data while invoices are kept for the GST retention period.
- The breach runbook in `docs/platform/runbook.md` holds who to notify under the DPDP rules and how fast.

## The checklist table

| Area | What must be true | How it is proven |
|---|---|---|
| Sessions | Opaque token, hash stored, user and role reloaded every request | Integration test: disable a user, the next request is 401 |
| Authorization | Deny by default, whole admin tree guarded | Generated admin sweep: 401 anonymous, 403 customer |
| IDOR | Owner is part of every by-id query | Customer B test against each of A's resources |
| Second door | Every path to guarded data has the same guard | One test per path, named in the pull request |
| Admin | TOTP required, first admin by CLI, audit row per write | Sweep with TOTP unverified returns 403 |
| No debug routes | No setup, seed, wipe or debug endpoint | Every new route shows up in the committed OpenAPI spec diff, reviewed in the pull request |
| Password reset | Single-use hashed token, 30 minutes, revokes sessions, identical responses | E2E reset via Mailpit, old session dead |
| Google sign-in | PKCE, `email_verified`, keyed by `sub`, linking wipes unverified password | Integration test against the mock OAuth server |
| Rate limits | Login, reset, resend, TOTP, orders, global per IP | Test the N+1th attempt returns 429 with `Retry-After` |
| CSRF | Token required on unsafe methods, webhook the only exemption | Test a POST without the token returns 403 `csrf_invalid` |
| CSP and headers | Policy per route group, Razorpay only on checkout | Playwright asserts the headers and fails on any CSP violation in the browser console |
| Uploads | Presigned POST, magic bytes, raster only, media domain | HTML renamed `.png` and an SVG are rejected |
| Webhooks | HMAC over raw bytes, constant time, deduped by event id | Razorpay's documented examples pass; 10 replays give 1 transition |
| Prices | Server computes every amount | Tampered total returns 409 `price_changed` |
| Responses | Explicit record allowlists, no entities | Exact JSON key set test; ArchUnit rule |
| Secrets | SSM and local `.env` only, gitleaks everywhere | `make ci` gitleaks step; boot fails without required values |
| Dependencies | No known high or critical vulnerability | osv-scanner in `make ci`, Dependabot, CodeQL |
| Personal data | No PII in logs, DPDP rights handled | Log capture test on register and reset flows |

## Checklist before you open a pull request

- [ ] Every row of the table your change touches is still true, and its proof still runs in `make ci`.
- [ ] Any new guard has a matching guard and test on every other path to the same data.
- [ ] New admin routes live under `/api/v1/admin/` and appear in the sweep output.
- [ ] New owned resources are fetched with the owner in the query and have an IDOR test.
- [ ] No request amount is trusted, and no response is built from an entity.
- [ ] New secrets are in `.env.example` as placeholders, have SSM entries planned, are validated at boot, and are masked in `toString()`.
- [ ] No log line added by this change contains an email, phone, address, name, token or signature.
- [ ] osv-scanner and gitleaks are clean, with no new unexplained ignore entries.
- [ ] No em dash anywhere in the change.
