# Codex Iteration State

Project: `edge-caching-resource-allocation`

Last updated: 2026-07-14

## Current Status

- Current completed iteration: Iteration 7
- Next iteration to run: Iteration 8
- Total target iterations: 14
- Execution rule: complete exactly one iteration per run
- Iteration 1 documentation supplement completed before starting Iteration 2.

## Iteration Checklist

- [x] Iteration 1: Project health check and iteration state setup.
- [x] Iteration 2: Repository structure cleanup and reproducibility baseline.
- [x] Iteration 3: Design wireless channel model interface.
- [x] Iteration 4: Implement path loss wireless channel model.
- [x] Iteration 5: Implement optional fading and tests.
- [x] Iteration 6: Add wireless channel experiment.
- [x] Iteration 7: Design Multi-Armed Bandit caching policy.
- [ ] Iteration 8: Implement Multi-Armed Bandit caching policy.
- [ ] Iteration 9: Add MAB comparison experiment.
- [ ] Iteration 10: Add multi-seed v2 experiment runner.
- [ ] Iteration 11: Generate final figures and result summaries.
- [ ] Iteration 12: Update README and model assumptions.
- [ ] Iteration 13: Write final mini research report.
- [ ] Iteration 14: Final reproduction check, cleanup, and portfolio summary.

## Iteration 1 Notes

Scope completed:

- Confirmed that no previous `docs/codex_iteration_state.md` existed.
- Established this file as the source of truth for future iteration selection.
- Ran the existing unit test suite.
- Ran the existing project health check.
- Confirmed that generated result summaries are reproducible from the current scripts.
- Added the missing Iteration 1 documentation deliverables:
  `docs/v2_roadmap.md` and `docs/experiment_plan_v2.md`.

Validation commands:

```bash
python -m unittest discover -s tests
python check_project.py
```

Validation result:

- Unit tests: 12 tests passed in the final post-change test run.
- Health check: passed and verified 16 output files.

Repository note:

- During Iteration 1, unrelated uncommitted working-tree changes were observed for a user-activity experiment and related reporting hooks.
- These changes were not created as part of Iteration 1 and were not modified by the iteration-state setup.
- The extra user-activity work appears to add one test, so the final post-change unit test count is 12.
- Future iterations should inspect the working tree before editing overlapping files.

## Iteration 2 Notes

Scope completed:

- Extended reproducibility metadata so run-specific JSON files can include sweep
  parameters and generated output filenames.
- Updated every experiment entry point to emit a matching metadata file in
  `results/data/`, including the multi-seed cache-capacity workflow.
- Tightened `check_project.py` to verify key metadata artifacts alongside the
  CSV and figure outputs.
- Added a unit test covering custom metadata fields in the JSON output.

Validation commands:

```bash
python -m unittest discover -s tests
python check_project.py
```

Validation result:

- Unit tests: 12 tests passed in the final post-change test run.
- Health check: passed and verified 22 output files.

## Iteration 3 Notes

Scope completed:

- Added `src/wireless_channel.py` with a minimal `WirelessChannelModel`
  abstraction and a default `BaselineDistanceChannelModel`.
- Refactored network generation and user-rate calculation so the simulator
  resolves the wireless channel model through one configuration entry point.
- Preserved the existing rate behavior while making later channel extensions
  isolated from caching and experiment code.
- Added tests for default model resolution and invalid model names.

Validation commands:

```bash
python -m unittest discover -s tests
python check_project.py
```

Validation result:

- Unit tests: 14 tests passed in the final post-change test run.
- Health check: passed and verified 22 output files.

## Iteration 4 Notes

Scope completed:

- Replaced the ambiguous default wireless model name with the explicit
  `path_loss` model in `SimulationConfig`.
- Parameterized the default gain calculation by reference-distance gain and
  path-loss exponent while preserving the previous numerical behavior.
- Kept `baseline_distance` as a compatibility alias so older configs still
  resolve cleanly.
- Added tests for the default model, the legacy alias, and the path-loss gain
  formula.

Validation commands:

```bash
python -m unittest discover -s tests
python check_project.py
```

Validation result:

- Unit tests: 16 tests passed in the final post-change test run.
- Health check: passed and verified 22 output files.

## Iteration 5 Notes

Scope completed:

- Added an optional `path_loss_fading` wireless channel model that reuses the
  same path-loss baseline and applies a bounded per-link fading power factor.
- Kept `path_loss` as the default model so earlier figures and baseline
  behavior remain stable unless the new model is explicitly selected.
- Made fading realizations deterministic from the main simulation seed plus a
  small config offset so repeated runs stay reproducible.
- Added focused tests for model resolution, deterministic and seed-dependent
  fading behavior, parameter validation, bounded factors, and positive rates.
- Corrected report text that still described fading as unimplemented future
  work.

Validation commands:

```bash
python -m unittest discover -s tests
python -W error -m unittest discover -s tests
python -m compileall config.py src experiments tests
python -m pip check
python check_project.py
```

Validation result:

- Unit tests: 22 tests passed in the final post-change test run.
- Health check: passed and verified 22 output files.
- Dependency check: no broken requirements found.
- Optional fading scenario: repeated runs were identical and all reported
  numerical metrics were finite.

## Iteration 6 Notes

Scope completed:

- Added a controlled wireless channel experiment that sweeps path-loss exponent
  for deterministic path loss and optional snapshot fading.
- Preserved all five caching/resource-allocation strategies in the generated
  CSV while using one fixed focal strategy for readable channel comparison
  figures.
- Integrated the experiment into the all-experiments runner and project health
  check.
- Added tests for experiment structure, reproducibility, finite metrics, and
  channel-model plot labels.

Validation commands:

```bash
python -m unittest discover -s tests
python -m compileall config.py src experiments tests run_all_experiments.py check_project.py
python experiments/run_wireless_channel_experiment.py
python run_all_experiments.py
python check_project.py
```

Validation result:

- Unit tests: 24 tests passed.
- Compilation check: passed.
- Standalone channel experiment: passed and produced 50 metric rows plus two
  non-empty figures.
- All-experiments runner: passed with the channel experiment included.
- Health check: passed and verified 26 expected output files.

## Iteration 7 Notes

Scope completed:

- Specified an independent per-server UCB-style combinatorial semi-bandit with
  capacity-aware file selection.
- Defined the avoided-backhaul-latency reward, UCB exploration term, reward per
  Mbit ranking, online mean update, and final exploitation cache.
- Defined a 60/40 chronological training/evaluation split that prevents MAB and
  request-aware baselines from learning from evaluation requests.
- Documented the proposed implementation interface, reproducibility parameters,
  Iteration 8 tests, Iteration 9 comparison, and explicit limitations.
- Kept this iteration documentation-only; no MAB source code or numerical
  performance claim was added.

Validation commands:

```bash
python -m unittest discover -s tests
python check_project.py
```

Validation result:

- Unit tests: 24 tests passed.
- Health check: passed and verified 26 expected output files.
- Core source code: unchanged in this design-only iteration.
