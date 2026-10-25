# 0015. License MDO under AGPL-3.0-only

**Status:** Accepted
**Date:** 2026-10-25

## Context

The Macro Data Observatory (MDO) repository has carried the GNU Affero General Public License, version 3, as its `LICENSE` since 2026-08-02, and `pyproject.toml` declares the SPDX identifier `AGPL-3.0-only`. No decision record sets out the reasoning for that choice; decisions 0007 and 0008 refer to the license only in passing.

The choice has become load-bearing. Macro Evidence's contributor-rights system ([governance decision 0009](https://github.com/macro-evidence/governance/blob/main/decisions/0009-adopt-a-harmony-based-contributor-rights-system.md)) licenses each accepted contribution to Macro Evidence and requires that Macro Evidence also license the contribution under the license or licenses the project uses on the Submission Date (Individual Contributor License Agreement §2.4). The license a repository carries is therefore part of what a contributor agrees to, and it should be stated and justified before external contributions are accepted.

MDO is the flagship and foundational macro-data platform of Macro Evidence. It acquires, validates, structures, and maintains macroeconomic data, and it provides the shared foundation for Macro Evidence products and interfaces ([Organization & Platform Charter](https://github.com/macro-evidence/governance/blob/main/ORGANIZATION_CHARTER.md) §2). Software of this kind can be run as a service that other people use over a network, not only distributed as copies. Macro Evidence's institutional posture is public-good, open-source stewardship of its public core.

Three license families were considered for the MDO software:

- **Permissive licenses (for example Apache-2.0 or MIT).** They maximize adoption and place almost no obligations on users. They also allow anyone to run a modified version as a hosted service, or to fold it into proprietary software, without sharing their changes.
- **GPL-3.0 without the network clause.** It requires source to be offered when copies are distributed, but a modified version that is only run as a network service is not distributed, so no source obligation arises.
- **AGPL-3.0.** It adds a network clause (§13): an operator who runs a modified version must offer its remote users the corresponding source. Hosted derivatives therefore remain as open as the original.

This decision concerns the license of the MDO repository. It does not alter the terms under which upstream providers publish the source data that MDO ingests, it does not govern other Macro Evidence repositories, which are licensed under their own documented decisions, and it grants no rights in Macro Evidence's names or visual identity ([Trademarks Policy](https://github.com/macro-evidence/governance/blob/main/TRADEMARKS.md) §2).

## Decision

MDO is licensed under the GNU Affero General Public License, version 3 only (`AGPL-3.0-only`). This decision confirms the license the repository already carries and records the reasons for it.

The reasons are:

- Reciprocity for network use. Software of this kind can be operated as a service that others use remotely. AGPL §13 keeps hosted derivatives open, which a permissive license or GPL-3.0 would not.
- Preservation of the public core. Keeping hosted and distributed derivatives open is consistent with Macro Evidence's public-good stewardship posture.
- Acceptance of the adoption cost. Some organizations restrict or avoid AGPL-licensed software, which can reduce adoption and contribution from them. That cost is accepted in exchange for reciprocity.
- The declared identifier is `AGPL-3.0-only`. The project does not accept later versions of the license automatically.

The contributor agreement preserves Macro Evidence's ability to license contributions on additional terms ([Contribution Policy](https://github.com/macro-evidence/governance/blob/main/CONTRIBUTION_POLICY.md) §4 and §7). This decision neither describes nor relies on any such arrangement, and it does not narrow rights already granted to the public under AGPL-3.0.

## Consequences

- Each contribution accepted into MDO is also licensed under `AGPL-3.0-only`, as the contributor agreement requires.
- Runtime dependencies were checked against this decision. The runtime packages resolved in the project's environment when this decision was made declare MIT, BSD-family, Apache-2.0, LGPL-3.0-only, MPL-2.0, PSF-2.0, 0BSD, Zlib, and CC0-1.0 licenses, and no license incompatible with AGPL-3.0 was identified. Development-only tools were not part of this check. The check reads the licenses that packages declare in their metadata; it is not a legal opinion and does not examine each package's full license text.
- Adding a runtime dependency whose license is incompatible with AGPL-3.0 would require reopening this decision.
- Organizations that cannot adopt AGPL-licensed software may choose not to use or contribute to MDO. This is accepted.
- A future change of license would be a new decision. It would not revoke rights already granted under AGPL-3.0 for versions already published.
