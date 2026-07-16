# Codex Iteration State

Project: `edge-caching-resource-allocation`

Last updated: 2026-07-16

## Current Status

- Current completed iteration: Iteration 14
- Next iteration to run: None - v2.0 plan complete
- Total target iterations: 14
- Execution rule: all planned iterations are complete; future work should use a
  separately scoped maintenance or extension plan
- Iteration 1 documentation supplement completed before starting Iteration 2.

## Iteration Checklist

- [x] Iteration 1: Project health check and iteration state setup.
- [x] Iteration 2: Repository structure cleanup and reproducibility baseline.
- [x] Iteration 3: Design wireless channel model interface.
- [x] Iteration 4: Implement path loss wireless channel model.
- [x] Iteration 5: Implement optional fading and tests.
- [x] Iteration 6: Add wireless channel experiment.
- [x] Iteration 7: Design Multi-Armed Bandit caching policy.
- [x] Iteration 8: Implement Multi-Armed Bandit caching policy.
- [x] Iteration 9: Add MAB comparison experiment.
- [x] Iteration 10: Add multi-seed v2 experiment runner.
- [x] Iteration 11: Generate final figures and result summaries.
- [x] Iteration 12: Update README and model assumptions.
- [x] Iteration 13: Write final mini research report.
- [x] Iteration 14: Final reproduction check, cleanup, and portfolio summary.

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

## Iteration 8 Notes

Scope completed:

- Added a deterministic UCB-style combinatorial semi-bandit policy with one
  independent learner per edge server.
- Implemented epoch-based selected-arm reward updates, seeded tie handling,
  score-per-Mbit capacity packing, and a fixed exploitation cache for later
  held-out evaluation.
- Added diagnostics for arm selection counts, estimated mean rewards, completed
  epochs, and explored-arm fraction.
- Added focused validation and tests covering reproducibility, heterogeneous
  cache budgets, oversized files, empty demand, a controlled learnable trace,
  the incremental mean update, and invalid hyperparameters.
- Kept the policy out of the default comparison so Iteration 9 can apply the
  documented 60/40 chronological split consistently to every request-aware
  strategy.

Validation commands:

```bash
python -m unittest discover -s tests
python -W error -m unittest discover -s tests
python -m compileall config.py src experiments tests
python check_project.py
```

Validation result:

- Unit tests: 32 tests passed.
- Warning-strict unit tests: 32 tests passed.
- Compilation check: passed.
- Default-scale MAB smoke check: passed with all cache budgets respected and
  finite learning diagnostics.
- Health check: passed and verified 26 expected output files.

Next iteration:

- Iteration 9: Add MAB comparison experiment.

## Iteration 9 Notes

Scope completed:

- Added a reusable chronological request splitter that keeps a non-empty
  training prefix and held-out evaluation suffix without shuffling.
- Added a dedicated five-policy caching comparison using one common network,
  request trace, file-size profile, 60/40 split, and equal bandwidth allocation.
- Limited local popularity, greedy, and UCB-style MAB learning to the training
  prefix; every fixed cache is evaluated only on the common suffix.
- Recorded policy information sources and separate MAB diagnostics, including
  seeds, epoch count, explored-arm fraction, selected-arm updates, and final
  cache utilization.
- Added CSV, metadata, and two figure outputs, then integrated the experiment
  into the all-experiments runner and project health check.
- Added focused tests for exact chronological splitting, reproducibility,
  capacity feasibility, common bandwidth conditions, and evaluation leakage.

Validation commands:

```bash
python -m unittest tests.test_mab_comparison_experiment
python -m unittest discover -s tests
python -W error -m unittest discover -s tests
python -m compileall config.py src experiments tests run_all_experiments.py check_project.py
python experiments/run_mab_comparison_experiment.py
python run_all_experiments.py
python check_project.py
```

Validation result:

- Focused tests: 3 tests passed.
- Unit tests: 35 tests passed.
- Warning-strict unit tests: 35 tests passed.
- Compilation check: passed.
- Standalone MAB comparison and all-experiments reproduction: passed.
- Health check: passed and verified 31 expected output files.

Single-seed observation:

- With seed 42, UCB-style MAB produced 1234.346 ms average latency and a 0.555
  cache hit ratio on the held-out suffix. Greedy caching produced 1231.400 ms
  and 0.5815 under the same equal-bandwidth conditions.
- MAB completed 15 epochs, explored all cache-feasible arms in this run, and
  used 97.31% of the average cache budget.
- These values are a reproducible single-seed observation, not a stability or
  superiority claim.

Next iteration:

- Iteration 10: Add multi-seed v2 experiment runner.

## Iteration 10 Notes

Scope completed:

- Added a reusable multi-seed runner for the final five-policy held-out strategy
  set using fixed seeds 11, 22, 33, 44, and 55.
- Preserved all 25 strategy/seed metric rows and summarized average latency,
  median latency, P95 latency, cache hit ratio, backhaul traffic/load, and
  wireless rate with means and sample standard deviations (`ddof=1`).
- Added within-seed metric differences relative to random caching so network
  realization variation can be separated from policy variation.
- Saved raw and summary MAB learning diagnostics across seeds, including arm
  coverage, selected updates, epoch count, and final cache utilization.
- Added five data/metadata outputs and integrated them into the all-experiments
  runner and health check. Final v2 figures remain Iteration 11 work.
- Added focused tests for exact aggregation, paired differences, reproducibility,
  common wireless conditions, and seed-list validation.

Validation commands:

```bash
python -m unittest tests.test_multi_seed_v2_experiment
python -m unittest discover -s tests
python -W error -m unittest discover -s tests
python -m compileall config.py src experiments tests run_all_experiments.py check_project.py
python experiments/run_multi_seed_v2_experiment.py
python run_all_experiments.py
python check_project.py
```

Validation result:

- Focused tests: 3 tests passed.
- Unit tests: 38 tests passed.
- Warning-strict unit tests: 38 tests passed.
- Compilation check: passed.
- Standalone multi-seed v2 and all-experiments reproduction: passed.
- Health check: passed and verified 36 expected output files.

Five-seed observation:

- UCB-style MAB average latency was 1183.254 ms with a 75.278 ms cross-seed
  sample standard deviation.
- Relative to the same-seed random baseline, MAB changed average latency by
  -45.051 +/- 5.966 ms and cache hit ratio by +0.3628 +/- 0.0233.
- MAB explored all cache-feasible arms for every seed and used 98.69% of the
  cache budget on average.
- These five seeds provide a lightweight robustness check, not general evidence
  across all wireless deployments.

Next iteration:

- Iteration 11: Generate final figures and result summaries.

## Iteration 11 Notes

Scope completed:

- Added a final figure generator for five-seed latency mean/std, cache-hit-ratio
  mean/std, and paired average-latency differences relative to random caching.
- Used horizontal error-bar plots with concise labels, explicit sample standard
  deviation semantics, and a zero reference line for paired differences.
- Mirrored the three final figures from `results/figures/` to `docs/figures/`
  so the next README iteration can display them directly on GitHub.
- Expanded `results/data/key_findings.md` into source-backed default, single-seed
  MAB, five-seed v2, sensitivity, and interpretation-boundary sections.
- Expanded `report/generated_results.md` with held-out and five-seed strategy
  tables, MAB diagnostics, final figure references, and cautious discussion text.
- Curated the final default/MAB/v2 CSV files, findings, and three result figures
  for Git tracking while leaving transient experiment files ignored.
- Added focused tests for data validation, figure generation/mirroring, and
  findings derived from synthetic CSV inputs.

Validation commands:

```bash
python -m unittest tests.test_final_results_generation
python -m unittest discover -s tests
python -W error -m unittest discover -s tests
python -m compileall config.py src experiments tests main.py run_all_experiments.py check_project.py summarize_results.py generate_report_assets.py generate_final_figures.py
python generate_final_figures.py
python summarize_results.py
python generate_report_assets.py
python run_all_experiments.py
python check_project.py
```

Validation result:

- Focused tests: 3 tests passed.
- Unit tests: 41 tests passed.
- Warning-strict unit tests: 41 tests passed.
- Compilation check: passed.
- All-experiments reproduction: passed.
- Visual inspection: all three final figures passed without clipping or overlap.
- Health check: passed and verified 43 expected output files.

Interpretation note:

- Absolute latency error bars overlap substantially because topology/request
  realization affects every policy in a seed.
- The paired figure therefore reports within-seed differences from random
  caching, where MAB records -45.051 +/- 5.966 ms across the five fixed seeds.
- The summary explicitly states that MAB improves on random caching but does not
  have the lowest mean latency among informed policies.

Next iteration:

- Iteration 12: Update README and model assumptions.

## Iteration 12 Notes

Scope completed:

- Updated the README with the implemented UCB-style score, separated default,
  held-out, and five-seed evidence, and linked every numerical claim to
  generated repository outputs.
- Added the three final v2 figures, final result-generation commands, current
  project structure, and a focused set of realistic future improvements.
- Expanded the model assumptions with a default parameter table, precise
  interference abstraction, held-out policy information boundaries, paired
  multi-seed comparison semantics, and reproducibility limits.
- Removed one stale README image reference whose target was not tracked, then
  verified that every remaining local README link and image exists.
- Kept this iteration documentation-only; no core simulation source or result
  values were changed.

Validation commands:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe check_project.py
```

Validation result:

- Unit tests: 41 tests passed.
- README local-link check: passed.
- Health check: passed and verified 43 expected output files.
- The system `python` command resolved to an inactive WindowsApps placeholder;
  the repository virtual environment used Python 3.12.13 successfully.

Next iteration:

- Iteration 13: Write final mini research report.

## Iteration 13 Notes

Scope completed:

- Created `report/project_report_final.md` as the final academic-style project
  report while preserving the earlier draft and template.
- Covered motivation, related background, system and mathematical models,
  caching/resource-allocation methods, UCB-style MAB design, experimental
  protocol, source-backed results, limitations, future work, and references.
- Integrated seven tracked figures and exact default, held-out, sensitivity,
  and five-seed values generated by repository scripts.
- Discussed the P95-latency and bandwidth-fairness costs of demand-aware
  allocation instead of reporting only favorable average-latency values.
- Kept the tone at undergraduate research level and explicitly avoided novelty,
  statistical-significance, 3GPP-compliance, and deployment claims.

Validation commands:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests
```

Validation result:

- Unit tests: 41 tests passed.
- Final report size: 3,628 words.
- All seven final-report figure links resolved to tracked repository assets.
- Markdown structure and figure-link checks: passed.

Next iteration:

- Iteration 14: Final reproduction check, cleanup, and portfolio summary.

## Iteration 14 Notes

Scope completed:

- Created `docs/portfolio_summary.md` with a concise project explanation,
  evidence-based findings, application-ready CV/SOP/interview material, honest
  scope boundaries, and an evidence map.
- Added final report and portfolio links to the README without placing CV text
  directly in the repository front page.
- Expanded `check_project.py` from output-only checks to a 49-file final
  artifact manifest covering core results and application documents.
- Marked the v2 roadmap complete and removed legacy Markdown trailing
  whitespace while preserving its content.
- Reproduced the complete experiment suite and confirmed that tracked generated
  outputs remained deterministic.

Validation commands:

```bash
.venv\Scripts\python.exe run_all_experiments.py
.venv\Scripts\python.exe -W error -m unittest discover -s tests
.venv\Scripts\python.exe -m compileall -q config.py src experiments tests main.py run_all_experiments.py check_project.py summarize_results.py generate_report_assets.py generate_final_figures.py
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe check_project.py
```

Validation result:

- Full experiment reproduction: passed.
- Unit tests in warning-strict mode: 41 tests passed.
- Compilation check: passed.
- Dependency check: no broken requirements.
- Health check: passed and verified 49 artifact files.
- README, final-report, and portfolio-summary local-link checks: passed.
- Trailing-whitespace and Git diff checks: passed.

Remaining research limitations:

- Five fixed seeds are a lightweight robustness check, not statistical proof.
- Channel, mobility, traffic, backhaul, and scheduling models remain simplified.
- MAB is an educational adaptive baseline and is not the best informed policy
  in the reported mean-latency table.

Completion status:

- All 14 planned iterations are complete.
