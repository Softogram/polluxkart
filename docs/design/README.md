# Design and test documents

Working documents rather than reference material: what is being built, how, and how it will be proved.

Parent: [docs/](../README.md)

Three kinds, and the difference matters:

| Folder | What it holds | Lifespan |
|---|---|---|
| **high-level/** | System-wide plans that cut across services: the road to launch, service boundaries, the data model, the order lifecycle, infrastructure, the design system | Long-lived |
| **low-level/** | One document per GitHub issue, written before it is built, concrete enough to implement from | Written once, then a record |
| **test/** | One test plan per issue, pairing with the low-level design above | Written with the design, executed later |

## Read next

- [high-level/](high-level/README.md) - cross-cutting plans
- [low-level/](low-level/README.md) - per-issue designs
- [test/](test/README.md) - per-issue test plans

## See also (do not follow recursively)

- [../platform/architecture.md](../platform/architecture.md) - the system as a whole
