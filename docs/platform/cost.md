# Running cost

Parent: [platform/](README.md) | Index: [docs/](../README.md)

**Status: ESTIMATE, 2026-09-13.**
These are rough monthly figures for the planned setup, in US dollars, before taxes.
They will be replaced with figures from the AWS Pricing Calculator for the Mumbai region when the staging environment is built in Phase 3, and then with real bills.

## Monthly estimate

| Item | Production | Staging | Notes |
|---|---|---|---|
| Application server (EC2 Graviton) | $25 to $50 | $10 to $15 | Production sized larger for Java and Next.js together; staging smaller and can be stopped when idle |
| Database (RDS PostgreSQL, single zone) | $15 to $30 | $12 to $15 | Includes storage and 14-day point-in-time restore |
| Backups copied to a second region | $1 to $5 | none | Grows with data |
| S3 and CloudFront for images and invoices | $1 to $5 | under $1 | Grows with catalog size and traffic |
| Email (SES) | under $1 | under $1 | About $0.10 per 1,000 emails |
| Logs, alarms, health checks (CloudWatch, Route 53) | $3 to $8 | $1 to $3 | 30-day log retention |
| Container registry (ECR) | under $1 | shared | Old images expire automatically |
| Threat detection (GuardDuty) | $1 to $5 | shared | Free for the first 30 days |
| **Total AWS** | **roughly $40 to $100** | **roughly $25 to $35** | |

## Outside AWS

| Item | Cost |
|---|---|
| Razorpay | A percentage fee per successful online payment, as per the merchant agreement; no monthly fee |
| Domain | Annual renewal |
| Sentry | Free tier |
| Plausible analytics | Optional, about $9 a month |
| GitHub | Free for a public repository, including Actions |

## What makes it grow

- More traffic: a larger server, then a second server behind a load balancer.
- More data: database storage and backups.
- More products and images: S3 storage and CloudFront transfer.
- Moving the database to two availability zones: roughly doubles the database line, worth it only once the app itself runs on more than one server.

## How to keep it down

- Stop the staging server and database when nobody is testing.
- Keep log retention at 30 days.
- Expire old container images and old versions of static files.
- An AWS Budgets alert emails the owner at 80% actual, 100% actual and 100% forecasted of a $10 monthly limit for now (owner decision, 2026-09-16, "AWS monthly budget alert"). The limit is raised in #85 when staging is built and in #175 when production is built.

## See also (do not follow recursively)

- [../design/high-level/infrastructure.md](../design/high-level/infrastructure.md) - what these resources are for
