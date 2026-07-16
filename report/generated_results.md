# Generated Report Assets

This file is generated from the latest CSV results. It is intended to
help copy tables and figure references into the project report.

## Default Scenario Results

| Strategy | Avg. latency (ms) | P95 latency (ms) | Cache hit ratio | Backhaul load ratio | Avg. wireless rate (Mbps) | Bandwidth fairness |
| --- | --- | --- | --- | --- | --- | --- |
| Random caching + equal BW | 1257.58 | 2866.95 | 0.167 | 0.833 | 5.60 | 0.981 |
| Popularity caching + equal BW | 1210.70 | 2801.55 | 0.505 | 0.495 | 5.60 | 0.981 |
| Local popularity caching + equal BW | 1208.96 | 2802.35 | 0.526 | 0.474 | 5.60 | 0.981 |
| Greedy caching + equal BW | 1206.02 | 2823.16 | 0.579 | 0.421 | 5.60 | 0.981 |
| Greedy caching + demand-aware BW | 1204.33 | 3230.34 | 0.579 | 0.421 | 7.07 | 0.755 |

## Cache-Capacity Multi-Seed Results at Default Budget

| Strategy | Avg. latency mean +/- std (ms) | Cache hit ratio mean +/- std | Mean backhaul load ratio |
| --- | --- | --- | --- |
| Greedy caching + demand-aware BW | 1162.75 +/- 83.11 | 0.572 +/- 0.015 | 0.428 |
| Greedy caching + equal BW | 1176.65 +/- 87.15 | 0.572 +/- 0.015 | 0.428 |
| Local popularity caching + equal BW | 1177.44 +/- 86.98 | 0.554 +/- 0.021 | 0.446 |
| Popularity caching + equal BW | 1177.57 +/- 87.30 | 0.554 +/- 0.024 | 0.446 |
| Random caching + equal BW | 1226.41 +/- 90.15 | 0.176 +/- 0.034 | 0.824 |

## Held-Out MAB Comparison (Seed 42)

| Caching strategy | Avg. latency (ms) | P95 latency (ms) | Cache hit ratio | Backhaul load ratio |
| --- | --- | --- | --- | --- |
| Random caching + equal BW | 1283.90 | 2967.96 | 0.165 | 0.835 |
| Prior-informed popularity caching + equal BW | 1234.58 | 2845.36 | 0.520 | 0.479 |
| Local popularity caching + equal BW | 1233.64 | 2845.36 | 0.535 | 0.465 |
| Greedy caching + equal BW | 1231.40 | 2910.17 | 0.582 | 0.418 |
| UCB-style MAB caching + equal BW | 1234.35 | 2910.17 | 0.555 | 0.445 |

## Five-Seed V2 Strategy Summary

| Caching strategy | Avg. latency mean +/- std (ms) | Hit ratio mean +/- std | Paired latency difference vs random (ms) |
| --- | --- | --- | --- |
| Random caching + equal BW | 1228.31 +/- 78.66 | 0.177 +/- 0.032 | +0.00 +/- 0.00 |
| Prior-informed popularity caching + equal BW | 1179.95 +/- 76.26 | 0.552 +/- 0.028 | -48.36 +/- 5.76 |
| Local popularity caching + equal BW | 1180.40 +/- 76.01 | 0.548 +/- 0.025 | -47.91 +/- 5.53 |
| Greedy caching + equal BW | 1180.53 +/- 73.94 | 0.562 +/- 0.019 | -47.77 +/- 6.45 |
| UCB-style MAB caching + equal BW | 1183.25 +/- 75.28 | 0.540 +/- 0.020 | -45.05 +/- 5.97 |

Negative paired latency differences indicate lower latency than the
same-seed random caching baseline.

## MAB Learning Diagnostics

| Scope | Completed epochs | Explored-arm fraction | Mean cache utilization |
| --- | --- | --- | --- |
| Seed 42 | 15 | 1.000 | 0.973 |
| Five-seed mean +/- std | 15.00 +/- 0.00 | 1.000 +/- 0.000 | 0.987 +/- 0.006 |

## Figure References

- Network topology: `docs/figures/network_topology.png`
- Zipf content popularity: `docs/figures/content_popularity_zipf.png`
- Latency vs cache capacity: `docs/figures/latency_vs_cache_capacity.png`
- Multi-seed latency trend: `docs/figures/multi_seed_latency_vs_cache_capacity.png`
- Spatial locality sensitivity: `docs/figures/latency_vs_spatial_locality.png`
- User activity skew sensitivity: `docs/figures/latency_vs_user_activity.png`
- User activity fairness sensitivity: `docs/figures/fairness_vs_user_activity.png`
- Backhaul sensitivity: `docs/figures/latency_vs_backhaul_latency.png`
- Bandwidth sensitivity: `docs/figures/latency_vs_bandwidth.png`
- File-size variability sensitivity: `docs/figures/latency_vs_file_size_variability.png`
- P95 latency by strategy: `docs/figures/main_p95_latency.png`
- Bandwidth fairness by strategy: `docs/figures/main_bandwidth_fairness.png`
- Latency component breakdown: `docs/figures/main_latency_breakdown.png`
- Final v2 latency mean/std: `docs/figures/v2_strategy_latency_mean_std.png`
- Final v2 hit-ratio mean/std: `docs/figures/v2_strategy_hit_ratio_mean_std.png`
- Final paired latency difference: `docs/figures/v2_paired_latency_vs_random.png`

## Spatial Locality Discussion Sentence

When server-specific demand becomes stronger, local popularity caching benefits more from using nearby request traces instead of one global ranking. At the strongest tested locality setting (0.8), local popularity caching lowers average latency from 1230.55 ms to 1227.80 ms.

## User Activity Skew Discussion Sentence

When user demand becomes more uneven, demand-aware bandwidth allocation becomes easier to justify because a small set of active users account for a larger fraction of requests. At the strongest tested activity skew (1.2), greedy caching with demand-aware bandwidth lowers average latency from 1094.92 ms under equal bandwidth to 1056.81 ms, with bandwidth fairness changing from 0.981 to 0.145.

## Suggested Discussion Sentence

In the default simulation, caching-aware strategies improve cache hit ratio and reduce backhaul load compared with random caching. The demand-aware bandwidth allocation variant achieves the lowest average latency in the default scenario, while the reported 95th percentile latency and Jain's bandwidth fairness index help check whether this average gain also improves tail performance and preserves a balanced resource distribution. The multi-seed experiment shows that the same trend remains visible across random network realizations.

## V2 Learning-Based Discussion Sentence

Across five fixed seeds, UCB-style MAB caching records 1183.25 ms mean latency and changes latency by -45.05 ms relative to the same-seed random baseline. However, it does not have the lowest mean latency among the informed caching policies, so the result supports MAB as an understandable adaptive baseline rather than as a universally superior algorithm.
