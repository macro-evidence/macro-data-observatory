# 0008. ADR placement moves to per-repository decisions folders

**Status:** Accepted
**Date:** 2026-08-09

## Context

All 7 prior ADRs (0001–0007) were centralized in `governance/decisions/`, on the original assumption that centralizing every architectural decision in one place would serve the organization as it grew. With a real track record to check that assumption against, none of the 7 turned out to be genuinely cross-cutting — every one governs `macro-data-observatory` specifically (schema, validation rules, the pipeline runner, source selection, CI) and doesn't constrain `governance`, `website`, or any other repository.

This was also in mild tension with an existing rule: `DOCUMENTATION_STANDARDS.md` §3 already states that anything specific to one platform belongs in that repository, not in `governance`. A validation year-ceiling decision is platform-specific by the organization's own existing definition.

Centralizing also creates real friction against `macro-data-observatory`'s AGPL-3.0-only license, which is chosen specifically to invite outside forks and contribution: an outside contributor changing code and recording the ADR for that change in the same PR, in a repository they can already see, is the standard pattern most open-source projects use. Requiring a second PR in a separate `governance` repository for every MDO-internal decision adds friction aimed at exactly the audience AGPL was chosen to welcome.

## Decision

Split ADR placement by scope, going forward:

- **Repository-specific ADRs live in that repository's own `decisions/`** — starting with `macro-data-observatory/decisions/`, and `website/decisions/` once that repository is standardized.
- **`governance/decisions/` is reserved for genuinely cross-cutting decisions** — ones that constrain or apply across multiple repositories, or the organization's structure itself.

All 7 existing ADRs were moved from `governance/decisions/` to `macro-data-observatory/decisions/`, same filenames, numbers, and content — this was the cheapest point to do it, before the count or repository list grew further. `GOVERNANCE.md` §5 and `DOCUMENTATION_STANDARDS.md` §3 were both updated to describe the split.

While migrating, the ADR template itself (`decisions/README.md`) was corrected: it specified 5 sections (Context, Decision, Alternatives Considered, Rationale, Consequences), but all 7 real ADRs — this one included — only ever used 3 (Context, Decision, Consequences). The template now matches seven-for-seven actual practice rather than a 5-section format nothing had used.

## Consequences

- `governance/decisions/` now sits empty, correctly — the same honest state `GOVERNANCE.md` described before 7 non-cross-cutting entries filled it, this time backed by an actual rule rather than just not having gotten to it yet.
- Git history for the 7 moved files restarts in their new location; cross-repository `git mv` isn't possible, so this is a real (small) cost of the correction, not a hidden one.
- Every internal reference to "governance decision NNNN" across `macro-data-observatory` (code comments, README, tests) was updated to "decision NNNN" as part of this same change, since the ADRs are now local.
- If a decision genuinely spanning multiple repositories comes up in the future, it goes in `governance/decisions/` starting at 0001 there — the two numbering sequences are independent and are expected to diverge, not stay in sync.
