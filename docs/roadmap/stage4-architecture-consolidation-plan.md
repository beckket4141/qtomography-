# Stage 4: Analysis & Infrastructure Consolidation Plan

> **Revision**: 2025-10-08  
> **Owner**: Core Platform Team (Stage 4)  
> **Context**: Builds directly on Stage 3 metrics/reporting enhancements. Focus shifts to harmonising the analysis layer and completing the infrastructure split introduced in Stage 3.

---

## 1. Background & Motivation

- Stage 3 delivered richer metrics, CLI reporting, and explicit persistence/visualization infrastructure.
- The `qtomography.analysis` package still mixes post-processing logic with domain imports, and several utilities (metrics, comparisons) live inside the controller/CLI layers.
- Legacy namespaces (`qtomography.visualization`, `qtomography.domain.persistence`) are now shims; we should finish the migration story and prevent future drift.

**Strategic goals**:
1. Establish *Analysis Layer* conventions (inputs, outputs, persistence contracts).
2. Finalise *Infrastructure Layer* seams (shared utilities, logging, caching).
3. Prepare the codebase for Stage 5 (GUI/API unification) by exposing service-style APIs.

---

## 2. Scope Overview

| Area | Current Pain | Stage 4 Outcome |
|------|--------------|-----------------|
| Analysis module | Single `bell.py`; CLI owns comparison/stat helpers; metrics scattered | Modular analysis package (`bell`, `metrics`, `comparisons`, `validators`) with cohesive interfaces |
| Infrastructure | Persistence utilities aware of analysis data but no common adapters | Shared infrastructure helpers (e.g. dataset loader, caching, logging) usable by analysis & app layers |
| Documentation | Stage 3 docs mention pending migration; roadmap still references legacy dirs | Updated architecture diagrams, migration guide, and cookbook examples aligned with new namespaces |
| Testing | No dedicated analysis layer tests; controller/CLI tests cover behaviour indirectly | Targeted unit tests for new analysis modules, integration tests for infra-analysis-app flows |

Out-of-scope: new reconstruction algorithms, GUI rendering, distributed execution (punted to later stages).

---

## 3. Detailed Objectives

1. **Analysis Layer Harmonisation**
   - Create `qtomography.analysis.metrics` with purity/entropy/condition-number helpers currently inside controller.
   - Introduce `qtomography.analysis.comparison` for Linear vs MLE diff logic (used by CLI).
   - Add `qtomography.analysis.schemas` (pydantic/dataclass) describing standard summary payloads.

2. **Infrastructure Enhancements**
   - Add `qtomography.infrastructure.common` package for shared adapters (file resolution, logging, numpy encoders).
   - Implement `ResultRepository` extension points (hooks/events) to accommodate analysis outputs.
   - Provide caching utilities (configurable TTL/LRU) for projector sets & expensive metrics.

3. **CLI & Controller Integration**
   - Refactor controller to consume analysis helpers rather than inlining metrics.
   - CLI `summarize` to rely on new comparison API; ensure backwards-compatible output.
   - Allow exporting consolidated analysis payloads (JSON schema from `analysis.schemas`).

4. **Documentation & Tooling**
   - Update README architecture section and diagrams with final layers.
   - Author “Analysis Layer Cookbook” under `docs/teach/analysis实战.md`.
  - Extend NEXT_STEPS & roadmap files with Stage 4 execution checkpoints.

---

## 4. Milestones & Timeline

| Milestone | Target Date | Key Deliverables | Owner |
|-----------|-------------|------------------|-------|
| M4.1 – Analysis module scaffolding | 2025-10-12 | New packages (`metrics`, `comparison`, `schemas`); migration of existing helpers | Core dev |
| M4.2 – Infrastructure common utilities | 2025-10-15 | `infrastructure.common` with logging, caching, IO helpers; repository hook design | Infra dev |
| M4.3 – Controller/CLI adoption | 2025-10-18 | Controller refactor, CLI summarise relying on analysis API; updated tests | App dev |
| M4.4 – Docs & Release Notes | 2025-10-20 | Cookbook, README/roadmap updates, migration guide | Tech writer |
| M4.5 – Stage 4 QA Gate | 2025-10-21 | Extended unit & integration suites, risk review, publish Stage4 completion report | QA |

---

## 5. Dependencies & Risks

- **Dependencies**
  - Metrics calculations from Stage 3 (ensure re-use, maintain compatibility).
  - Pytest coverage for controller/CLI (will need updates when refactoring).
  - Pending decision on analysis data schemas (JSON vs pandas vs parquet).

- **Risks**
  - Potential regression in CLI output formatting when switching to new APIs.
  - Additional package restructuring may break external imports; mitigation via compatibility shims.
  - Increased test matrix length; must budget time for pipeline updates.

**Mitigations**: Introduce transitional adapters, stage multi-step PRs, maintain backwards compatibility through Stage 4.

---

## 6. Acceptance Criteria

- Controller & CLI rely exclusively on new analysis modules; no metrics logic duplicated in `app/controller.py`.
- Infrastructure layer contains reusable utilities and persistence hooks referenced in docs.
- README, roadmap, NEXT_STEPS mention Stage 4 structure & status.
- Unit tests cover metrics/comparison modules; integration tests validate end-to-end summarise output.
- Stage 4 completion report drafted with lessons learned and Stage 5 proposals.

---

## 7. Deliverables Checklist

- [ ] `docs/roadmap/stage4-architecture-consolidation-plan.md` (this document)
- [ ] Analysis module scaffolding + migrations
- [ ] Infrastructure common utilities module
- [ ] Updated controller/CLI integration
- [ ] Enhanced documentation (cookbook + revised architecture diagrams)
- [ ] Stage 4 QA report & release notes

---

## 8. Tracking & Reporting

- Progress tracked via `STAGE4_PROGRESS.md` (to be created alongside execution).
- Weekly syncs with app/infra owners; summary posted to `docs/implemented/project-status-2025-10-07.md`.
- Status badges updated in README upon milestone completion (tests, docs).

> **Next Action**: Initialise analysis scaffolding (create module directories/tests) and update roadmap/next steps to reference this plan.

