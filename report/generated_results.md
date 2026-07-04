# Generated Report Assets

This file is generated from the latest CSV results. It is intended to
help copy tables and figure references into the project report.

## Default Scenario Results

| Strategy | Avg. latency (ms) | P95 latency (ms) | Cache hit ratio | Backhaul load ratio | Avg. wireless rate (Mbps) |
| --- | --- | --- | --- | --- | --- |
| Random caching + equal BW | 1257.58 | 2866.95 | 0.167 | 0.833 | 5.60 |
| Popularity caching + equal BW | 1210.70 | 2801.55 | 0.505 | 0.495 | 5.60 |
| Local popularity caching + equal BW | 1208.96 | 2802.35 | 0.526 | 0.474 | 5.60 |
| Greedy caching + equal BW | 1206.02 | 2823.16 | 0.579 | 0.421 | 5.60 |
| Greedy caching + demand-aware BW | 1204.33 | 3230.34 | 0.579 | 0.421 | 7.07 |

## Multi-Seed Results at Default Cache Capacity

| Strategy | Avg. latency mean +/- std (ms) | Cache hit ratio mean +/- std | Mean backhaul load ratio |
| --- | --- | --- | --- |
| Greedy caching + demand-aware BW | 1162.75 +/- 83.11 | 0.572 +/- 0.015 | 0.428 |
| Greedy caching + equal BW | 1176.65 +/- 87.15 | 0.572 +/- 0.015 | 0.428 |
| Local popularity caching + equal BW | 1177.44 +/- 86.98 | 0.554 +/- 0.021 | 0.446 |
| Popularity caching + equal BW | 1177.57 +/- 87.30 | 0.554 +/- 0.024 | 0.446 |
| Random caching + equal BW | 1226.41 +/- 90.15 | 0.176 +/- 0.034 | 0.824 |

## Figure References

- Network topology: `docs/figures/network_topology.png`
- Zipf content popularity: `docs/figures/content_popularity_zipf.png`
- Latency vs cache capacity: `docs/figures/latency_vs_cache_capacity.png`
- Multi-seed latency trend: `docs/figures/multi_seed_latency_vs_cache_capacity.png`
- Backhaul sensitivity: `docs/figures/latency_vs_backhaul_latency.png`
- Bandwidth sensitivity: `docs/figures/latency_vs_bandwidth.png`
- File-size variability sensitivity: `docs/figures/latency_vs_file_size_variability.png`
- P95 latency by strategy: `docs/figures/main_p95_latency.png`

## Suggested Discussion Sentence

In the default simulation, caching-aware strategies improve cache hit ratio and reduce backhaul load compared with random caching. The demand-aware bandwidth allocation variant achieves the lowest average latency in the default scenario, while the reported 95th percentile latency helps check whether this average gain also improves tail performance. The multi-seed experiment shows that the same trend remains visible across random network realizations.
