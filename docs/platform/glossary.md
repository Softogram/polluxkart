# Glossary

Parent: [platform/](README.md) | Index: [docs/](../README.md)

Plain-English definitions for every technical term used across this project's docs.
Look here whenever a word in another document is unfamiliar.
Terms are grouped by area, alphabetical within each group.

## Commerce and India

**B2C (business to consumer)**
Selling directly to individual shoppers rather than to other businesses.

**CGST, SGST, IGST**
The three kinds of GST line on an invoice.
A sale within the shop's own state charges central GST (CGST) and state GST (SGST), half each.
A sale to another state charges integrated GST (IGST) instead.

**COD (cash on delivery)**
The shopper pays the courier in cash when the parcel arrives.

**Credit note**
A document that reduces or cancels an invoice already issued, used for cancellations and returns after invoicing.
Invoices are never edited.

**DLT registration**
Registration with Indian telecom operators that businesses need before sending SMS, including one-time codes.

**DPDP Act**
India's Digital Personal Data Protection Act, 2023.

**Financial year (FY)**
India's tax year, 1 April to 31 March. Invoice numbering restarts each financial year.

**GST (Goods and Services Tax)**
India's tax on sales. PolluxKart's prices include GST.

**GSTIN**
A business's 15-character GST registration number.

**GSTR-1**
The monthly or quarterly GST return listing sales. The store exports the data for the accountant.

**HSN code**
The tax category code of a product, 4 to 8 digits, printed on invoices.

**MRP (Maximum Retail Price)**
The highest price a packaged product may be sold for in India. The selling price can be lower, never higher.

**Paise**
One hundredth of a rupee. All money is stored as whole paise.

**Pincode**
India's six-digit postal code.

**Place of supply**
The state the goods are delivered to, which decides CGST and SGST versus IGST.

**RTO (return to origin)**
A parcel the courier could not deliver and is bringing back.

**SKU (stock keeping unit)**
One sellable variant of a product, such as a phone in 128 GB black. Stock and price live on the SKU.

## Backend

**API (Application Programming Interface)**
The set of web addresses the frontend calls to read or change data.

**Compensation**
An action that undoes an earlier step when a later step fails, such as releasing a stock reservation when saving the order fails.

**Endpoint**
One address in the API, for example `POST /api/v1/orders`.

**Event (domain event)**
A record that something happened, such as `OrderPlaced`, that other services react to.

**Flyway**
A tool that applies numbered SQL migration files to the database in order, once each.

**gRPC**
A framework for calling functions on another machine over the network, used if a service later moves to its own server.

**Hibernate / JPA**
The Java library and standard that map database rows to Java objects.

**Idempotency key**
A unique id sent with a request so that repeating the request has the same effect as sending it once.

**Interface (Java)**
A type that lists what something can do without saying how. Services call each other only through interfaces.

**Maven module**
A separately built part of a Java project. Each service is one module.

**Migration**
A numbered, versioned change to the database schema.

**N+1 query**
A bug where code runs one query for a list and then one more query per item, which gets slow as the list grows.

**OpenAPI**
A machine-readable description of every API endpoint, generated from the code.

**Problem Details (RFC 9457)**
A standard JSON shape for API errors. PolluxKart adds a stable `code` field the frontend reads.

**Race condition**
A bug where two things happen at the same moment and the result depends on which finished first.

**Reservation (stock)**
Stock set aside for an order that is not yet shipped, so nobody else can buy it.

**Schema (PostgreSQL)**
A named namespace of tables inside one database. Each service has its own.

**Service**
A self-contained part of the backend that owns one area of the business, with its own code, interface and schema.

**Spring Boot**
A Java framework for building web services with sensible defaults.

**Spring Modulith**
A library that checks module boundaries in a Spring application and stores events durably.

**Testcontainers**
A testing library that starts a real database in a Docker container for a test run.

**Transaction**
A group of database changes that either all happen or none happen.

**UUIDv7**
A random-looking unique id whose first part is a timestamp, so ids sort roughly by creation time.

**Webhook**
A web request a vendor sends to our server to report an event, such as a payment captured.

## Frontend

**App Router**
Next.js's folder-based way of defining pages, layouts, loading and error screens.

**Client component**
A React component that runs in the browser and can respond to clicks and typing.

**CSP (Content Security Policy)**
A browser rule, sent by the server, listing which scripts and resources a page may load.

**JSON-LD**
Structured data inside a page that tells search engines a product's name, price and availability.

**Next.js**
A React framework that can render pages on the server.

**Server component**
A React component that runs only on the server and sends finished HTML.

**Server-side rendering**
Building a page's HTML on the server before sending it, so search engines and link previews see real content.

**Tailwind CSS**
A styling approach using small utility classes, driven by the project's design tokens.

**Token (design)**
A named value such as `primary` or `radius` used instead of a raw colour or size, so the theme is defined in one place.

**TypeScript**
JavaScript with types, so mistakes about the shape of data show up before running.

## Security

**Allow list (secret scanning)**
The one file, `.gitleaks.toml`, listing text that looks like a secret but is not, each entry with a dated reason.

**CSRF (cross-site request forgery)**
An attack where another website tricks a signed-in browser into sending a request. Prevented with a CSRF token.

**gitleaks**
An open-source secret scanner that looks through files and git history for text shaped like passwords, keys and tokens.

**HMAC signature**
A code computed from a message and a shared secret, used to prove a message was not forged.

**httpOnly cookie**
A cookie that page scripts cannot read, only the browser and server.

**IDOR (insecure direct object reference)**
A bug where changing an id in a request shows someone else's data. Prevented by an ownership check on every read.

**OAuth / OIDC**
The standards behind "Sign in with Google".

**Push protection**
A GitHub feature that refuses a push containing a recognised secret before it reaches the repository.

**Rate limiting**
Refusing requests from one source above a set speed, to stop guessing attacks.

**Rotate (a secret)**
Replace a key with a new one and switch the old one off, so any leaked copy stops working.

**TOTP (time-based one-time password)**
The six-digit codes from an authenticator app, used as admins' second sign-in step.

**XSS (cross-site scripting)**
An attack where a malicious script is saved on a site and runs in visitors' browsers.

## Infrastructure

**CloudFront**
AWS's content delivery network, which caches files close to visitors.

**Docker / container**
A packaged, self-contained app that runs the same on a laptop and a server.

**EC2**
AWS virtual servers.

**ECR**
AWS's registry for Docker images.

**Point-in-time restore (PITR)**
Restoring a database to any moment within the backup window.

**RDS**
AWS's managed database service.

**S3**
AWS file storage.

**SES**
AWS's email sending service.

**SSM Parameter Store**
AWS storage for configuration and encrypted secrets.

**Terraform**
A tool that creates cloud infrastructure from text files, so it can be reviewed and rebuilt.

## Working practice

**actionlint**
A linter for GitHub Actions workflow files. It uses ShellCheck to check the shell commands inside them.

**Bypass (ruleset)**
Permission for a named account to ignore the rules of one ruleset. PolluxKart gives one, narrowly: the owner may merge pull requests into `main`.

**CI (continuous integration)**
Automated checks that run on every pull request. PolluxKart runs them with GitHub Actions and, locally, with `make ci`.

**Drift**
Live settings that no longer match what the repository says they should be, such as a ruleset edited by hand in GitHub settings.

**Exit code**
The number a command hands back when it finishes. Zero means success; anything else means failure, and hooks and CI stop on it.

**Force push**
A push that replaces a branch's history instead of adding to it. It can erase other people's work, so it is blocked on `development` and `main`.

**Git hook**
A small script git runs automatically before a commit or a push. If it fails, git stops. PolluxKart's hooks live in `.githooks/` and are enabled once per clone with `git config core.hooksPath .githooks`.

**GitHub Actions workflow**
A YAML file in `.github/workflows/` telling GitHub what to run and when. Each job in it shows up as a named check on a pull request.

**Lint (linter)**
Checking files for mistakes without running them. The linter is the tool that does it.

**LTS (long-term support)**
A release that receives security fixes for years rather than months.

**Make / Makefile**
A command-line program that runs named recipes, called targets, written in a file named `Makefile`. `make ci` runs the target `ci`.

**Merge commit**
Merging a pull request with its commits kept, joined by a commit that records both branches as parents. Used for releases into `main`.

**Release pull request**
A pull request from `development` into `main`. Merging it is a release.

**Required check**
A check that must pass before GitHub lets a pull request merge, matched by its exact name.

**Ruleset**
A named set of branch rules that GitHub itself enforces, such as "changes arrive only through pull requests".

**ShellCheck**
A linter for shell commands, used by actionlint.

**Squash merge**
Merging a pull request as one commit on the target branch.

**Worktree (git)**
A separate working folder for one branch, so tasks and agents never share a checkout.
