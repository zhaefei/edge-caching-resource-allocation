# Model Assumptions and Scope

This project uses a simplified simulation model. The goal is to demonstrate
undergraduate-level research ability, not to reproduce a full industrial 5G/6G
system simulator.

## What the Model Includes

- A finite content library with Zipf-distributed request popularity.
- Mild server-specific request locality layered on top of the global popularity.
- Bounded heterogeneous file sizes around a configurable mean.
- Randomly placed users in a square service area.
- Grid-placed edge servers with limited cache capacity.
- Nearest-edge-server user association.
- Distance-based channel gain with a configurable path-loss exponent.
- A simplified SINR model with thermal noise and a coarse interference term.
- Shannon-capacity-based wireless transmission rate.
- Backhaul delay when requested content is not cached locally.
- Jain's fairness index as a simple resource-allocation diagnostic.
- Heuristic caching and bandwidth allocation strategies.

## Default Scenario Snapshot

The default values below define the main seed-42 scenario. Experiment scripts
change only the parameter being studied unless their metadata states otherwise.

| Component | Default value | Interpretation |
| --- | ---: | --- |
| Content library | 50 files | Finite catalogue of data/video chunks |
| Users / edge servers | 100 / 4 | Static users and grid-placed servers |
| Service area | 500 m x 500 m | Two-dimensional square region |
| Requests | 5,000 | One reproducible synthetic request trace |
| Zipf alpha | 0.9 | Moderate global popularity concentration |
| Spatial-locality strength | 0.35 | Mixture weight for server-specific demand |
| Mean file size | 5 Mbit | Bounded lognormal sizes from 1 to 12 Mbit |
| Cache budget per server | 40 Mbit | Eight times the mean file size |
| Server bandwidth | 20 MHz | Shared downlink bandwidth per edge server |
| Transmit power | 0.2 W | Common power used for each server link |
| Path-loss exponent | 3.4 | Large-scale distance attenuation |
| Noise figure | 7 dB | Receiver noise penalty |
| Interference factor | 0.15 | Scales non-serving received power |
| Backhaul | 80 ms, 100 Mbit/s | Fixed latency plus transfer time |
| Random seed | 42 | Default network, requests, and file sizes |

These values are illustrative rather than calibrated to one carrier, frequency
band, 3GPP deployment scenario, or measured dataset. The configuration is
centralized in `config.py`, and sweep scripts record their changed values in
run metadata.

## Why These Assumptions Are Reasonable

The model keeps the main engineering tradeoffs visible:

- **Caching tradeoff:** edge servers cannot store all files, so cache placement
  affects hit ratio and backhaul load.
- **Storage tradeoff:** larger files consume more cache budget, so a caching
  rule must balance popularity against content size.
- **Popularity tradeoff:** Zipf-distributed requests make popular-content
  caching meaningful.
- **Locality tradeoff:** nearby users may prefer slightly different subsets of
  content, which creates a reason to compare global and local caching rules.
- **Wireless tradeoff:** limited bandwidth and channel quality affect delivery
  latency even when content is cached.
- **Backhaul tradeoff:** cache misses become more expensive when backhaul
  latency is high.

These are suitable abstractions for a compact research simulation and for
explaining interest in wireless communications, edge computing, and network
optimization.

## What the Model Does Not Claim

This project does not claim:

- A novel caching algorithm.
- State-of-the-art performance.
- 3GPP-compliant system-level simulation.
- Real deployment readiness.
- Accurate modeling of all 5G/6G channel, scheduler, mobility, and protocol
  details.

The results should be interpreted as controlled simulation trends under the
specified assumptions.

## Main Simplifications

- Users are static during each run.
- Spatial locality is modeled with simple server-specific popularity boosts
  rather than a learned or measured traffic dataset.
- File sizes use a simple bounded lognormal profile rather than measured traffic traces.
- The default `path_loss` channel model uses large-scale deterministic path
  loss without detailed fading:
  `gain = path_loss_reference_gain * (d_ref / max(distance, min_distance))^path_loss_exponent`.
- An optional `path_loss_fading` variant multiplies the same path-loss baseline
  by a clipped sample from a unit-mean exponential power distribution. This
  corresponds to one seed-controlled Rayleigh-fading snapshot, not a
  time-varying channel process.
- The simulator now resolves wireless behavior through a small channel-model
  interface so future path-loss and fading variants can be compared without
  changing the caching workflow.
- Interference is the configured factor multiplied by the sum of received
  powers from all non-serving edge servers. It does not model scheduling,
  beamforming, frequency reuse, or correlated interference.
- Backhaul latency is modeled with a fixed component and transfer delay.
- Bandwidth allocation is heuristic rather than solved as a full optimization
  problem.
- Fairness is evaluated as a diagnostic metric, not optimized as a formal
  objective.
- The UCB-style caching extension updates only files selected during each
  training epoch and uses avoided backhaul latency per local request as reward.
- MAB training returns a fixed final cache. The dedicated comparison uses one
  chronological 60/40 split and equal bandwidth for every caching policy.
- The primary MAB comparison uses one fixed seed, while the v2 summary repeats
  the same held-out protocol over five fixed seeds and reports sample standard
  deviations and paired differences relative to random caching.
- Five seeds provide a lightweight robustness check, not exhaustive statistical
  evidence across deployment environments.

## Evaluation Protocols

### Default Five-Strategy Comparison

The original comparison evaluates random, global popularity, local popularity,
greedy, and greedy plus demand-aware bandwidth strategies on the same seed-42
network and request trace. Local popularity, greedy caching, and demand-aware
allocation inspect that trace. This experiment is useful for controlled
strategy comparison, but it is not an out-of-sample learning evaluation.

### Held-Out Caching Comparison

The dedicated MAB experiment divides each chronological request trace into a
60% training prefix and a 40% evaluation suffix. Local popularity and greedy
caching use only the training prefix. MAB also trains only on the prefix and
receives selected-arm feedback. The final caches remain fixed on the evaluation
suffix, and every policy receives equal bandwidth so that the comparison
isolates caching behavior.

The random policy is a seeded baseline. The policy labelled
`Prior-informed popularity caching` uses the known Zipf prior rather than the
training requests; its information advantage is explicit in the label and it
should not be described as a purely data-driven held-out policy.

### Multi-Seed V2 Summary

The final v2 experiment repeats the held-out protocol for seeds 11, 22, 33, 44,
and 55. It reports arithmetic means and sample standard deviations (`ddof=1`).
Paired differences are calculated as each strategy's metric minus the random
baseline metric from the same seed. Pairing reduces confusion from comparing
strategies on different random network realizations, but five fixed seeds are
still too few to support broad statistical or deployment claims.

## Reproducibility Boundary

Network placement, request generation, file sizes, fading snapshots, random
caching, and MAB tie handling use deterministic seeds or deterministic rules.
CSV outputs are the source for every numerical statement in the README and
generated report assets. Environment metadata is retained locally but ignored
by Git because it changes between machines and runs.

## How to Discuss the Project

The safest way to present this project is:

> I built a reproducible Python simulation framework to study how edge caching
> and simple bandwidth allocation heuristics affect latency in a simplified
> wireless edge network.

Avoid presenting it as a new 6G algorithm or a production-grade network
simulator. Its value is in system modeling, reproducible experiments, algorithm
comparison, and honest interpretation of results.
