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
- Distance-based channel gain with path loss.
- A simplified SINR model with thermal noise and a coarse interference term.
- Shannon-capacity-based wireless transmission rate.
- Backhaul delay when requested content is not cached locally.
- Heuristic caching and bandwidth allocation strategies.

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
- The channel model uses large-scale path loss without detailed fading.
- Interference is represented by a simple scaling factor.
- Backhaul latency is modeled with a fixed component and transfer delay.
- Bandwidth allocation is heuristic rather than solved as a full optimization
  problem.

## How to Discuss the Project

The safest way to present this project is:

> I built a reproducible Python simulation framework to study how edge caching
> and simple bandwidth allocation heuristics affect latency in a simplified
> wireless edge network.

Avoid presenting it as a new 6G algorithm or a production-grade network
simulator. Its value is in system modeling, reproducible experiments, algorithm
comparison, and honest interpretation of results.
