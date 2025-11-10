# Bell-State Analysis Plan

_Last updated: 2025-10-07_
_Status: 📝 Draft_

## 1. Background & Goals

- In the original MATLAB workflow, Bell-state analysis is an optional post-processing step: after reconstructing a density matrix, the tool compares it against a predefined Bell basis, computes fidelities, and writes summary reports.
- The Python port already produces stable reconstruction outputs (`ReconstructionController` + `ResultRepository`). The goal is to re-introduce Bell analysis as an **analysis-layer** module that plugs into the existing results pipeline while remaining optional.

## 2. Scope

1. **Core analysis API**
   - Input: `DensityMatrix` or `ReconstructionRecord`, plus system dimension/configuration.
   - Output: fidelity list, summary statistics (max/min/avg), dominant Bell state index, optional raw components.
   - Supported dimensions: 4, 9, 16 (matching MATLAB). The implementation should generalise to perfect-square dimensions.

2. **Ideal-state definitions**
   - Encode the generalized Bell basis (coefficients/phases) for each supported dimension.
   - Provide helper `generate_bell_basis(local_dimension)` so new configurations can be registered easily.

3. **Reporting & persistence**
   - Compute derived metrics (max/min/avg fidelity, dominant index, optional CHSH later).
   - Append metrics into `ResultRepository` records and optionally emit `bell_summary.csv`.

4. **Controller / CLI integration**
   - `qtomography reconstruct … --bell`: run Bell analysis immediately after each reconstruction.
   - `qtomography bell-analyze <records_dir>`: post-process an existing batch of JSON records to produce a summary CSV.

5. **Documentation & examples**
   - Teaching note explaining generalized Bell states and fidelity meaning.
   - Implementation guide covering how to extend with additional target states.

## 3. Implementation Phases

| Phase | Deliverable | Notes |
| --- | --- | --- |
| B1 | Basis definitions & analysis API | Create `qtomography/analysis/bell.py`, implement basis generation and fidelity calculations, add unit tests (pure Bell state → fidelity 1). |
| B2 | Controller / CLI integration | Extend `ReconstructionController` with an `analyze_bell` flag, add `--bell` flag to `reconstruct`, and a `bell-analyze` CLI command. |
| B3 | Reporting polish | Ensure metrics are persisted in JSON records and `summary.csv`, optionally produce a dedicated `bell_summary.csv`. |
| B4 | Docs & samples | Update README/roadmap, add how-to examples, and reference datasets. |

## 4. Test Strategy

- **Unit tests**: fidelity for ideal Bell states equals 1, random states stay within [0, 1], unsupported dimensions raise `ValueError`.
- **Integration tests**: run `qtomography reconstruct … --bell` on a small dataset; verify JSON metrics and summary columns. Test `qtomography bell-analyze <records>` end-to-end.
- **Performance sanity**: small batches should run quickly; heavy batches can be handled later if needed.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Basis definitions are error-prone | Wrong fidelities | Start with the canonical qubit/qutrit/ququart formulas and cover them with unit tests. |
| Tight coupling with reconstruction | Hard to reuse | Keep the analysis layer dependent only on density matrices / records, not on reconstructor internals. |
| Output overload | Users get confused | Add metrics with a consistent `bell_*` prefix and document them clearly. |

## 6. Milestones

- **B1 (week 1)**: basis generation + `compute_bell_fidelities()` API ready with tests.
- **B2 (week 2)**: controller/CLI integration (`--bell`, `bell-analyze`) online.
- **B3–B4 (week 3+)**: reporting polish, documentation updates, align with future GUI/P3 work.

---

**Owner**: TBD (current reconstruction maintainers)

**Dependencies**: `ReconstructionController`, `ResultRepository`, test data fixtures.
