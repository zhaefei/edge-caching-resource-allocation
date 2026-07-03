# Generated Report Assets

This file is generated from the latest CSV results. It is intended to
help copy tables and figure references into the project report.

## Default Scenario Results

| Strategy | Avg. latency (ms) | Cache hit ratio | Backhaul load ratio | Avg. wireless rate (Mbps) |
| --- | --- | --- | --- | --- |
| Random caching + equal BW | 1251.89 | 0.181 | 0.819 | 5.59 |
| Popularity caching + equal BW | 1204.49 | 0.546 | 0.454 | 5.59 |
| Local popularity caching + equal BW | 1204.26 | 0.548 | 0.452 | 5.59 |
| Greedy caching + equal BW | 1204.26 | 0.548 | 0.452 | 5.59 |
| Greedy caching + demand-aware BW | 1198.24 | 0.548 | 0.452 | 7.00 |

## Multi-Seed Results at Default Cache Capacity

| Strategy | Avg. latency mean +/- std (ms) | Cache hit ratio mean +/- std | Mean backhaul load ratio |
| --- | --- | --- | --- |
| Greedy caching + demand-aware BW | 1182.81 +/- 39.48 | 0.555 +/- 0.005 | 0.445 |
| Greedy caching + equal BW | 1200.02 +/- 55.44 | 0.555 +/- 0.005 | 0.445 |
| Local popularity caching + equal BW | 1200.02 +/- 55.44 | 0.555 +/- 0.005 | 0.445 |
| Popularity caching + equal BW | 1200.25 +/- 55.37 | 0.554 +/- 0.005 | 0.446 |
| Random caching + equal BW | 1253.27 +/- 54.41 | 0.146 +/- 0.050 | 0.854 |

## Figure References

- Network topology: `docs/figures/network_topology.png`
- Zipf content popularity: `docs/figures/content_popularity_zipf.png`
- Latency vs cache capacity: `docs/figures/latency_vs_cache_capacity.png`
- Multi-seed latency trend: `docs/figures/multi_seed_latency_vs_cache_capacity.png`
- Backhaul sensitivity: `docs/figures/latency_vs_backhaul_latency.png`
- Bandwidth sensitivity: `docs/figures/latency_vs_bandwidth.png`

## Suggested Discussion Sentence

In the default simulation, caching-aware strategies improve cache hit ratio and reduce backhaul load compared with random caching. The demand-aware bandwidth allocation variant achieves the lowest average latency in the default scenario, while the multi-seed experiment shows that the same trend remains visible across random network realizations.
