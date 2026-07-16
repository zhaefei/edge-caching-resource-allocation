# Key Findings

All numerical findings below are generated from repository CSV outputs.

## Default Scenario

- Compared with random caching, greedy caching with demand-aware bandwidth allocation reduces average latency by 4.2%.
- Local popularity caching reduces average latency by 3.9% compared with random caching.
- Cache hit ratio improves by 41.2 percentage points compared with random caching.
- Backhaul traffic decreases by 44.7%, showing the benefit of serving popular content at the edge.
- Demand-aware bandwidth allocation increases the request-weighted average wireless rate by 26.3% in this default scenario.
- Under the same greedy cache placement, demand-aware bandwidth allocation changes Jain's bandwidth fairness index from 0.981 to 0.755 (-0.226).

## Held-Out MAB Comparison (Seed 42)

- Under the common 60/40 chronological split and equal bandwidth, UCB-style MAB records 1234.346 ms average latency and a 0.555 cache hit ratio.
- The corresponding random and greedy average latencies are 1283.899 ms and 1231.400 ms, respectively. MAB improves on random caching but is not the lowest-latency policy in this single-seed run.
- MAB completes 15 training epochs, explores 1.000 of cache-feasible arms, and uses 97.31% of cache capacity on average.

## Five-Seed V2 Summary

- Across seeds 11, 22, 33, 44, and 55, UCB-style MAB records 1183.254 +/- 75.278 ms average latency (mean +/- sample standard deviation).
- Relative to the same-seed random baseline, MAB changes average latency by -45.051 +/- 5.966 ms and cache hit ratio by +0.3628 +/- 0.0233.
- Prior-informed popularity caching + equal BW has the lowest mean average latency in this five-seed table at 1179.949 ms; the small differences among informed policies should not be presented as proof of universal ranking.
- Across the five seeds, mean MAB arm coverage is 1.000, and mean final cache utilization is 98.69%.

## Sensitivity and Robustness Checks

- In the multi-seed experiment at the default cache budget equivalent to 8 average-size files, Greedy caching + demand-aware BW reduces mean latency by 5.2% relative to random caching.

- In the file-size variability sweep at sigma 1.0, Greedy caching + demand-aware BW achieves the lowest average latency.

- In the spatial-locality sweep at strength 0.8, local popularity caching outperforms global popularity caching by 3.3 hit-ratio percentage points and 0.2% lower latency.

- In the user-activity sweep at alpha 1.2, demand-aware bandwidth allocation under the same greedy cache placement reduces latency by 3.5% relative to equal bandwidth, while changing Jain's fairness index by -0.836.

## Interpretation Boundary

- The simulator is an undergraduate-level research model, not a 3GPP-compliant system-level simulator or a production optimizer.
- Five fixed seeds provide a lightweight robustness check. They do not establish statistical significance across real deployments.
- The UCB-style policy is a teaching-oriented adaptive baseline, not a novel or guaranteed-optimal caching algorithm.
