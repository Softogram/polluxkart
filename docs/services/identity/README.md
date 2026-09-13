# identity

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PROPOSED (2026-09-13), confirmed ticket by ticket. Built in slice S1.**

## Owns

Accounts, email verification, password reset, Sign in with Google, sessions, addresses, admin two-step sign-in codes (TOTP), consent records and data requests.
Schema: `identity`.

## Promises

- Sign-in creates a session: a random token in an httpOnly, Secure, SameSite=Lax cookie with the `__Host-` prefix. Only its SHA-256 hash is stored.
- Every request reloads the user and role, so a disabled account or removed admin role is refused on the next request.
- Sessions expire after inactivity and after an absolute limit; admins time out after 30 minutes idle and 12 hours total.
- Password reset uses a single-use link emailed to the verified address, stored hashed, valid 30 minutes, and signs out every session when used.
- Responses to sign-up, sign-in and reset look identical whether or not an email exists.
- Signing in with Google onto an account whose email was never verified removes that account's password and sessions, so someone who registered a victim's email first cannot keep access.
- Every admin must enrol an authenticator app and enter its code at sign-in.
- The first admin is created only by a one-off command on the server, recorded in audit.
- Phone sign-in is reserved in the data model for after DLT registration.

## Interface (planned)

`IdentityApi`: resolve a session to a user and role; get a user's contact details and default address as a snapshot; check whether an email is verified; record consent.

## Endpoints (planned)

`POST /api/v1/auth/register`, `/verify-email`, `/login`, `/logout`, `/logout-all`, `/password-reset/request`, `/password-reset/confirm`, `GET /api/v1/auth/google/start` and callback; `GET/PATCH /api/v1/me`, `/me/addresses`, `/me/sessions`, `/me/security/totp`, `/me/data-export`, `/me/delete`; admin users list under `/api/v1/admin/users`.

## Events

Publishes `UserRegistered`, `EmailVerified`, `UserDisabled`, `AccountDeleted`.

## Refuses

- A password reset without a valid, unexpired, unused token.
- More sign-in or reset attempts than the rate limits allow.
- Any admin request without a completed two-step sign-in.
- Returning a password hash or TOTP secret in any response.

## See also (do not follow recursively)

- [../../platform/security.md](../../platform/security.md) - the security rules in one table
