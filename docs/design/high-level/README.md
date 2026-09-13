# High-level design

Parent: [design/](../README.md) | Index: [docs/](../../README.md)

System-wide, forward-looking plans: the kind that cut across every service rather than belonging to one.
[../../platform/architecture.md](../../platform/architecture.md) summarizes the system; these documents hold the full reasoning and rules.

One file per topic, written once the topic is discussed and decided: Claude researches and proposes, the owner reviews and decides, and only then is it written here as settled.

## Read next - approved 2026-09-13

- **[The road from here to a production-class PolluxKart](road-to-launch.md)** - the phased plan: emergency actions, repository and tooling, skills and docs, the walking skeleton, staging, nine feature slices, compliance, production hardening, launch, and the backlog after launch. **Read this first.**
- **[Service boundaries](service-boundaries.md)** - how thirteen independent services live in one codebase, run together at launch, and can each move to its own server over gRPC later without changing their callers.
- **[Data model](data-model.md)** - every table per service schema, the constraints the database enforces, the stock reservation rule and the GST calculation rule.
- **[Order lifecycle](order-lifecycle.md)** - the order state machine, what each transition does to stock, money, invoices and email, and who may trigger it.
- **[Infrastructure](infrastructure.md)** - AWS environments, the deploy pipeline, backups and restore, monitoring.
- **[Design system](design-system.md)** - the fixed PolluxKart theme carried over unchanged, how it maps into the new frontend, the storefront patterns, and the one open contrast question for the owner.

## See also (do not follow recursively)

- [../../platform/decisions.md](../../platform/decisions.md) - the dated decisions these plans rest on
