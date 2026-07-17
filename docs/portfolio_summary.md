# Project Portfolio Summary

**Author:** Erfei Zha

## Project Overview

**Edge Caching and Resource Allocation for Latency Reduction in 5G/6G Wireless
Networks**

This repository is a reproducible undergraduate-level research simulation at
the intersection of wireless communications, edge computing, and lightweight
network optimization. It studies how limited edge storage and shared downlink
bandwidth affect content-delivery latency when user requests follow global and
server-local popularity patterns.

The scope is deliberately transparent: this is an engineering research
exploration, not a novel 6G algorithm, a 3GPP-compliant system-level model, or a
production network simulator.

## What Was Built

- A configurable wireless edge network with 50 heterogeneous files, static
  users, multiple edge servers, nearest-server association, and limited caches.
- A channel-model interface with deterministic distance-based path loss and an
  optional seed-controlled fading snapshot.
- Shannon-based wireless rates using bandwidth, transmit power, channel gain,
  thermal noise, noise figure, and simplified inter-cell interference.
- End-to-end latency combining wireless transmission and cache-miss backhaul
  delay.
- Random, prior-informed popularity, local popularity, greedy latency-aware,
  and UCB-style MAB caching policies.
- Equal and demand-aware bandwidth allocation with Jain fairness diagnostics.
- Controlled cache, demand, network-scale, backhaul, bandwidth, file-size, and
  wireless-channel sensitivity experiments.
- A chronological 60/40 train/evaluation protocol and a final five-seed
  comparison with within-seed differences from random caching.
- Reproducible CSV outputs, figures, run metadata, generated findings, and 43
  standard-library unit tests.

## Research Workflow

The project follows a compact research cycle:

1. Define a tractable system model and state its limitations.
2. Translate communications concepts into equations and testable Python code.
3. Select understandable baselines before adding a learning-based extension.
4. Separate training requests from held-out evaluation requests.
5. Run parameter sweeps and fixed-seed robustness checks.
6. Report mean, tail, backhaul, hit-ratio, rate, and fairness outcomes together.
7. Interpret negative or mixed findings without overstating significance.

## Evidence-Based Findings

All values below come from generated repository CSV files.

- In the seed-42 default scenario, greedy caching with demand-aware bandwidth
  lowers average latency by 4.2% relative to random caching, increases cache hit
  ratio by 41.2 percentage points, and reduces backhaul traffic by 44.7%.
- The same demand-aware policy changes Jain bandwidth fairness from 0.981 to
  0.755 and raises P95 latency from 2823.16 ms under greedy plus equal bandwidth
  to 3230.34 ms. The project therefore reports a latency/fairness tradeoff.
- In the held-out seed-42 comparison, UCB-style MAB records 1234.346 ms average
  latency versus 1283.899 ms for random and 1231.400 ms for greedy caching.
- Across seeds 11, 22, 33, 44, and 55, MAB records
  `1183.254 +/- 75.278 ms`. Its paired same-seed latency difference from random
  is `-45.051 +/- 5.966 ms`.
- Prior-informed popularity has the lowest mean latency in the five-seed table,
  so the MAB policy is presented as a useful adaptive baseline rather than the
  best algorithm.

Five seeds are a lightweight robustness check and do not establish statistical
significance across real deployments.

## Engineering Interpretation

Three conclusions are more important than a single policy ranking. First,
caching can substantially reduce backhaul use while producing a smaller change
in end-to-end latency when wireless transmission remains the bottleneck.
Second, an allocation rule that improves request-weighted mean latency may
worsen P95 latency and fairness, so these metrics must be read together. Third,
a learning-based policy does not automatically outperform simpler informed
heuristics; held-out evaluation is necessary before making that claim.

## Scope Boundaries

- No claim of algorithmic novelty or state-of-the-art performance.
- No claim of 3GPP compliance or prediction for a real operator deployment.
- No deep reinforcement learning, large optimization solver, or measured trace.
- No statistical-significance claim from five fixed seeds.
- No claim that demand-aware allocation is uniformly better, because fairness
  and P95 latency can worsen.

## Repository Evidence Map

- Project overview and reproduction: [`README.md`](../README.md)
- Final research report: [`report/project_report_final.md`](../report/project_report_final.md)
- Model scope: [`docs/model_assumptions.md`](model_assumptions.md)
- Experiment design: [`docs/experiment_plan_v2.md`](experiment_plan_v2.md)
- Generated tables: [`report/generated_results.md`](../report/generated_results.md)
- Generated findings: [`results/data/key_findings.md`](../results/data/key_findings.md)
- Final figures: [`docs/figures/`](figures/)
- Tests: [`tests/`](../tests/)

## Reproduction

From the repository root with dependencies installed:

```bash
python run_all_experiments.py
python -m unittest discover -s tests
python check_project.py
```

The continuous-integration workflow repeats strict tests and the complete
project health check on Python 3.11 and 3.12.
