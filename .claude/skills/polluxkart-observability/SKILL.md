---
name: polluxkart-observability
description: Use when adding or changing logging, a request id, a health check, a scheduled job, a CloudWatch metric filter or alarm, or Sentry setup in PolluxKart's Spring Boot API or Next.js app, or when deciding whether something should page the owner or only be logged.
---

# Logs, health checks and alerts in PolluxKart

**Status: DRAFT (2026-09-13).**
Written before any application code exists, so every path, setting and Terraform resource below is the approved plan, not built code.
When the repository disagrees with this skill, the repository wins; fix this skill in the same pull request.

Sources: `docs/platform/architecture.md` (deployment on EC2 with Docker and Caddy), `docs/platform/runbook.md` (what to do when an alarm fires), `docs/platform/decisions.md`, `docs/legacy/audit-2026-09.md` section 5.

## Words used below

- **Structured log:** a log line written as JSON with named fields, so tools can filter by field instead of searching text.
- **Request id:** a unique id given to one incoming request and written on every log line that request produces, so its whole story can be found at once.
- **MDC (Mapped Diagnostic Context):** a per-thread set of fields the logging library adds to every log line automatically, such as `requestId`.
- **PII (Personally Identifiable Information):** data that identifies a person, such as name, email, phone, address or IP address.
- **Actuator:** Spring Boot's built-in operations endpoints, such as health checks.
- **Liveness:** "is the process running and not stuck"; if this fails, restarting helps.
- **Readiness:** "can the app serve requests right now", which for us means the database is reachable; if this fails, send no traffic, but restarting does not help.
- **CloudWatch Logs:** AWS's log storage, where our containers' output ends up.
- **Metric filter:** a CloudWatch rule that counts log lines matching a pattern and turns the count into a number over time.
- **Alarm:** a CloudWatch rule that notifies people when a number crosses a threshold.
- **Sentry:** a hosted service that groups crashes and errors and shows their stack traces.
- **ShedLock:** a Java library that makes sure a scheduled job runs on only one server at a time.

## The rules on one screen

1. Every log line is JSON, and every line written while serving a request carries `requestId` (decided 2026-09-13).
2. No PII, tokens or secrets in any log, error report or alarm message.
3. Liveness never touches the database; readiness does (decided 2026-09-13).
4. Alarms match the stable `event` or `level` field, never message wording.
5. Every alarm links to a section of `docs/platform/runbook.md`, and anything that does not need a human soon is logged, not alarmed.

## Structured JSON logs

Spring Boot writes structured logs natively, so no extra logging library is needed.

```yaml
logging:
  structured:
    format:
      console: logstash   # one JSON object per line; field names below assume this format
  level:
    root: INFO
```

Add facts as named fields with SLF4J's fluent API, never glued into the message.

```java
// Wrong: a PII leak and unsearchable text
log.info("Order placed by " + user.getEmail() + " for Rs " + total);

// Right: ids and amounts as fields; the message is a fixed phrase
log.atInfo()
   .addKeyValue("event", "order_placed")
   .addKeyValue("orderId", order.id())
   .addKeyValue("userId", order.customerId())
   .addKeyValue("totalPaise", order.totalPaise())
   .log("order placed");
```

- `event` is a snake_case name that never changes once alarms or queries use it.
- Never use `System.out.println` or `printStackTrace()`; the first version's debug prints are how personal data reached its logs.

## Request id (decided 2026-09-13)

A filter that runs before Spring Security sets the id, so even a 401 response carries it.

```java
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
class RequestIdFilter extends OncePerRequestFilter {
    private static final Pattern SAFE = Pattern.compile("[A-Za-z0-9-]{8,64}");

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String incoming = req.getHeader("X-Request-Id");
        String id = incoming != null && SAFE.matcher(incoming).matches() ? incoming : UUID.randomUUID().toString();
        MDC.put("requestId", id);
        res.setHeader("X-Request-Id", id);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.remove("requestId");  // threads are reused; a leftover id would mislabel the next request
        }
    }
}
```

- An incoming id is accepted only if it matches the safe pattern, so nobody can inject fake log lines through the header.
- The Next.js server sends its own `X-Request-Id` when it calls the API, so one id covers the page render and the API work behind it.
- The same id goes into every Problem Details error body as `requestId` (see `polluxkart-error-handling`), and error screens show it as a reference.
- After login, the session filter adds `userId` (a random UUID, not PII on its own) to the MDC.
- MDC does not follow work to another thread, so the `@Async` executor gets a `TaskDecorator` that copies the MDC across.
- Event listeners replayed later by Spring Modulith have no request, so they log the order, payment or invoice id instead.

To follow one request in CloudWatch Logs Insights (the query page for CloudWatch Logs):

```
fields @timestamp, level, event, message
| filter requestId = "0192f7c4-2b1e-7a3d-9c55-1f0e8a6b2d11"
| sort @timestamp asc
```

## No PII in logs

**Never log:** emails, phone numbers, names, addresses, IP addresses outside security events, passwords, session or reset tokens, cookies, `Authorization` headers, TOTP codes or secrets, Razorpay signatures, presigned URLs (they contain a signature), request or response bodies, or vendor webhook payloads.
**Log instead:** our ids (`userId`, `orderId`, `orderNumber`, `paymentId`), counts, amounts in paise, status values and durations.

- Settings records that hold secrets override `toString()`, so logging the object is safe.
- Caddy's access log hides query strings on `/reset-password` and `/verify-email`, whose links carry tokens.
- A log capture test runs the register, login and password reset flows and fails if the test email address appears in any output.
- CloudWatch log groups have an explicit retention period set in Terraform, never "keep forever", because logs are personal data under the DPDP Act (India's data protection law).

## Log levels

| Level | Means | Examples |
|---|---|---|
| `ERROR` | A bug or failure a human must look at; also sent to Sentry | an unhandled exception (the 500 path), an invoice PDF that failed to store, a job run that failed |
| `WARN` | Unusual and handled, often security relevant | webhook signature failed, vendor call failed after retries and was queued, outbox row retried, payments stuck |
| `INFO` | A business event or job result worth keeping | order placed, payment captured, shipment created, job succeeded |
| `DEBUG` | Detail for local work; off in staging and production | query parameters, branch decisions |

- An expected 4xx error is not an `ERROR`; log it at `DEBUG`, or at `WARN` with an `event` only when it is a security signal.
- Never log one line per item inside a loop at `INFO`; log one summary line with counts.
- Each failure is logged once, where it is handled (see `polluxkart-error-handling`).

## Health checks (decided 2026-09-13)

Actuator runs on a separate management port that is never published to the host and never routed by Caddy.

```yaml
management:
  server:
    port: 8081
  endpoints:
    web:
      exposure:
        include: health          # never heapdump, env or configprops: they expose secrets and session tokens
  endpoint:
    health:
      probes:
        enabled: true
      show-details: never
      group:
        readiness:
          include: readinessState, db
```

- `/actuator/health/liveness` on port 8081 checks only that the process is alive, never the database, because restarting the app cannot fix a database outage.
- `/actuator/health/readiness` on port 8081 includes the database check.
- `ops/deploy.sh` waits for readiness inside the container before the smoke test, and rolls back if it never arrives.
- The public `GET /api/v1/health` returns only `{"status":"UP"}` with 200, or `{"status":"DOWN"}` with 503, and no component names, versions or details.
- It reuses the readiness result cached for a few seconds, so hammering it cannot load the database.
- A Route 53 health check (AWS's outside-in probe) calls the public endpoint over HTTPS.

## Shipping logs to CloudWatch

Docker's `awslogs` logging driver sends each container's output straight to CloudWatch Logs.

```yaml
# the server's compose file used by ops/deploy.sh (planned)
services:
  api:
    logging:
      driver: awslogs
      options:
        awslogs-region: ap-south-1
        awslogs-group: /polluxkart/production/api
        mode: non-blocking     # if CloudWatch is slow, drop log lines rather than freeze the store
        max-buffer-size: 8m
```

- Terraform creates the log groups (`api`, `web`, `caddy`) with retention, so the driver never creates them.
- The EC2 instance role allows only `logs:CreateLogStream` and `logs:PutLogEvents` on those groups.
- EC2 does not report disk usage by itself, so the CloudWatch agent is installed only to publish the disk metric.

## Metric filters and alarms

Metric filters match the JSON `event` or `level` field, then alarms fire on the resulting numbers.

```hcl
# infra/terraform/modules/app-env/alarms.tf (planned)
resource "aws_cloudwatch_log_metric_filter" "webhook_signature_failed" {
  name           = "webhook-signature-failed"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "{ $.event = \"webhook_signature_failed\" }"
  metric_transformation {
    name      = "WebhookSignatureFailed"
    namespace = "PolluxKart/${var.environment}"
    value     = "1"
  }
}
```

Alarms send to an SNS topic (AWS's notification service) that reaches the owner by email and SMS (decided 2026-09-13).

| Alarm | Source | Fires when | Why a human is needed |
|---|---|---|---|
| Site down | Route 53 health check on `/api/v1/health` | 3 failed checks in a row (Route 53's default) | shoppers cannot buy |
| API errors | metric filter `level = "ERROR"` | 5 or more in 5 minutes | a bug is hitting real requests |
| Webhook signature failures | metric filter `event = "webhook_signature_failed"` | 1 or more in 5 minutes | a wrong secret silently stops payment confirmations, or someone is forging events |
| Payments stuck | metric filter `event = "payments_stuck"`, summing `count` | any payment unresolved after 30 minutes | a shopper paid and has no confirmed order |
| Job heartbeat missing | metric filter `event = "job_succeeded"` per job | no success in 3 schedule periods, missing data counted as failing | stock stays reserved, emails stop, or payments go unreconciled |
| Email outbox backlog | metric filter `event = "outbox_backlog"` | oldest unsent email over 15 minutes | order emails are not reaching shoppers |
| RDS | RDS metrics | CPU over 80% for 15 minutes, free storage under 20%, connections near the limit | the database is about to fail |
| EC2 disk | CloudWatch agent `disk_used_percent` | over 80% | a full disk stops Docker and Postgres clients |
| EC2 status | EC2 status check | failed | triggers auto-recover, and tells the owner it happened |
| SES reputation | SES bounce and complaint rates | well below SES's own review thresholds | SES may pause all email |

- Staging alarms go to email only.
- The first production alarm is proven with a test notification that reaches the owner's phone before launch.

## Sentry (decided 2026-09-13)

```yaml
sentry:
  dsn: ${SENTRY_DSN}
  environment: production
  release: ${GIT_SHA}
  send-default-pii: false
  traces-sample-rate: 0.0
  logging:
    minimum-event-level: error   # only ERROR logs become Sentry events, so each failure is reported once
```

- The DSN (the Sentry project address) comes from SSM, and in the `prod` profile a validated settings record fails boot without it, because Sentry silently disables itself when the DSN is missing.
- Expected 4xx errors never reach Sentry.
- The Next.js app uses Sentry with `sendDefaultPii: false` and session replay turned off, because replay records screens full of addresses.
- A `beforeSend` hook removes query strings, cookies and request bodies from every event.

## Scheduled jobs

Every job runs through one small wrapper, so success and failure look the same for every job.

```java
@Scheduled(fixedDelayString = "PT1M")
@SchedulerLock(name = "reservation-expiry", lockAtMostFor = "PT5M")  // ShedLock: one server at a time
void expireReservations() {
    jobs.run("reservation-expiry", () -> reservations.releaseExpired(clock.instant()));
}
```

- `jobs.run` measures the duration, logs `event=job_succeeded` with `job`, `durationMs` and the returned count at `INFO`, or `event=job_failed` with the exception at `ERROR`, and does not rethrow.
- The heartbeat alarm catches the failure errors cannot: a job that silently stopped running.
- A job that finds a problem it cannot fix logs a named `WARN` event with a count, such as `payments_stuck` from the reconciliation job.
- Jobs at launch include reservation expiry, payment reconciliation and the email outbox; each gets a heartbeat alarm when it is added.

## Alert or only log

| Alert (a human acts soon) | Only log (look when investigating) |
|---|---|
| Site or readiness down | Any single 4xx, including 401, 403 and 404 |
| Sustained `ERROR` logs | A single 429, or a failed login |
| Any webhook signature failure | A vendor call that failed once and succeeded on retry |
| A payment stuck over 30 minutes | Validation failures |
| A job heartbeat missing | A job that ran and found nothing to do |
| Email backlog, SES reputation | A duplicate webhook that deduplication ignored |
| RDS, disk, EC2 status | Slow requests below the performance budget |

An alarm that fires often and needs no action gets fixed or removed, because an owner who learns to ignore alarms will ignore the real one.

## Not built yet (2026-09-13)

- **Distributed tracing** (following one request across several processes, with OpenTelemetry): everything runs in one process, so the request id is enough; revisit when the first service is split out.
- **Metrics dashboards:** alarms come first; a dashboard is added only when a real question needs one.

## Checklist before you open a pull request

- [ ] New log lines are structured, use a fixed message plus named fields, and carry an `event` name if anything will query or alarm on them.
- [ ] No new log line, Sentry event or alarm text contains PII, tokens, signatures, presigned URLs or bodies.
- [ ] The level matches the table: no `ERROR` for expected 4xx, and nothing logged twice.
- [ ] Work moved to another thread keeps `requestId`, or logs a business id instead.
- [ ] Liveness still does not touch the database, and nothing new is exposed on Actuator or the public health endpoint.
- [ ] A new scheduled job uses ShedLock and `jobs.run`, and has a heartbeat metric filter and alarm in Terraform.
- [ ] A new alarm has a runbook section in `docs/platform/runbook.md`, and its metric filter matches an `event` or `level` field.
- [ ] New Sentry or logging settings keep PII sending off and fail boot in `prod` when required values are missing.
- [ ] No em dash anywhere in the change.
