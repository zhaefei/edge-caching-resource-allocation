# Edge Caching and Resource Allocation for Latency Reduction in 5G/6G Wireless Networks

- **Author:** Erfei Zha
- **Field:** Electrical Engineering and Communications Engineering
- **Project type:** Undergraduate-level reproducible simulation study
- **Version:** 2.0
- **Date:** July 2026

## Abstract

Future wireless networks must deliver increasingly data-intensive content while
operating with limited radio, storage, and backhaul resources. Edge caching can
reduce repeated transfers from the core network by storing frequently requested
files near users, but its benefit depends on content popularity, cache size,
local demand, wireless channel quality, and bandwidth allocation. This project
develops a reproducible Python simulation for studying these interactions in a
simplified 5G/6G wireless edge network. Users request heterogeneous files under
a Zipf popularity model with optional server-specific spatial locality. Users
associate with their nearest edge server, and wireless rates follow a Shannon
capacity expression with distance-dependent path loss, thermal noise, coarse
inter-cell interference, and optional seed-controlled snapshot fading. Cache
misses add fixed backhaul latency and transfer delay.

The study compares random, prior-informed popularity, local popularity, greedy
latency-aware, and lightweight upper-confidence-bound (UCB) caching. Equal and
demand-aware bandwidth allocation are also evaluated. A chronological 60/40
training/evaluation split is used for the learning-based comparison, followed
by a five-seed robustness study. In the default scenario, greedy caching with
demand-aware bandwidth reduces average latency by 4.2% and backhaul traffic by
44.7% relative to random caching, but its Jain bandwidth-fairness index falls
from 0.981 to 0.755 and its 95th-percentile latency increases. Across five
held-out runs, UCB-style caching records `1183.254 +/- 75.278 ms` average
latency and a same-seed improvement of `45.051 +/- 5.966 ms` over random
caching. It does not achieve the lowest mean latency among informed policies.
The results demonstrate system-modeling and experimental skills without
claiming a novel optimizer or production-level network fidelity.

**Keywords:** edge caching, wireless communications, 5G/6G, Zipf popularity,
resource allocation, multi-armed bandit, reproducible simulation

## 1. Introduction

Mobile networks carry repeated requests for video segments, software objects,
sensor data, and other reusable content. If every request is served from a
remote cloud, the same files may repeatedly traverse the core and backhaul
network. This increases traffic and adds a latency component that cannot be
removed by improving the radio link alone. Multi-access edge computing brings
storage and computation closer to users, making local content delivery a useful
mechanism for reducing this repeated traffic [2], [3].

Edge storage is nevertheless limited. A base station cannot cache an entire
content library, so cache placement must decide which files are most valuable.
The answer depends on how often a file is requested, where those requests
occur, how large the file is, and how much delay a cache hit avoids. Wireless
resources create a second constraint: a local cache hit still requires radio
transmission, and users associated with the same server share finite bandwidth.
Caching and resource allocation should therefore be studied within one latency
model rather than as completely separate decisions.

This project investigates three research questions:

1. How do simple request-aware caching strategies compare with random caching
   in latency, hit ratio, and backhaul load?
2. How do cache capacity, user density, content popularity, spatial locality,
   and wireless channel assumptions change the observed tradeoffs?
3. Can a lightweight UCB-style caching policy learn a useful cache from a
   training prefix, and how does it compare with understandable static
   heuristics on held-out requests?

The work is intentionally scoped as an undergraduate simulation study. Its
contribution is not a new 6G algorithm. Instead, it integrates a transparent
wireless model, storage-constrained caching, resource allocation, held-out
learning evaluation, sensitivity experiments, and reproducible result
generation in one codebase. This scope makes every assumption inspectable and
every numerical statement traceable to a generated CSV file.

## 2. Background

Caching research studies how limited storage can reduce future communication
cost. Coded caching establishes fundamental theoretical tradeoffs between
storage and delivery rate [1], while practical wireless caching also depends on
deployment constraints, demand estimation, and business considerations [3].
This project focuses on uncoded file placement because the aim is to expose the
basic engineering relationships clearly.

Content popularity is commonly represented by a Zipf distribution. Measurements
of web requests have shown approximately Zipf-like behavior, in which a small
set of high-ranked objects receives a large share of requests [4]. Such a
long-tail distribution creates an intuitive baseline: storing globally popular
files should be more useful than selecting files uniformly at random. Real
networks may also have regional preferences, motivating a local-popularity
policy for each edge server.

Caching does not remove the wireless transmission stage. Shannon's capacity
expression provides a compact connection between allocated bandwidth, signal
quality, and achievable rate [5]. Although a full cellular simulator would
model scheduling, frequency reuse, mobility, beamforming, and standardized
channel profiles, a path-loss and SINR abstraction is sufficient for the
controlled comparisons in this study.

Finally, online learning offers a way to adapt cache placement when popularity
is not supplied directly. A multi-armed bandit (MAB) balances exploration of
uncertain choices and exploitation of choices with high estimated reward. The
implemented UCB-style policy is a teaching-oriented combinatorial semi-bandit:
each server-file pair is an arm, several arms are selected under a storage
budget, and only selected arms receive reward updates. It is included to compare
a simple adaptive mechanism with static heuristics, not to claim methodological
novelty.

## 3. System Model

### 3.1 Network Topology and Association

The network contains `M` users and `K` edge servers in a square area. Servers
are placed on a grid, users are placed uniformly at random, and each user
associates with the nearest server. Users remain static during one simulation
run. The default topology contains 100 users and four edge servers in a
`500 m x 500 m` region.

![Simulated network topology](../docs/figures/network_topology.png)

### 3.2 Content and Requests

The library contains `N = 50` files. File sizes follow a seed-controlled,
bounded lognormal profile with a 5 Mbit nominal mean and bounds of 1 to 12 Mbit.
The cache budget at each server is 40 Mbit, equivalent to eight nominal files,
although the number of files that fits varies because sizes are heterogeneous.

The global request probability of rank-`f` content follows

```math
p_f = \frac{f^{-\alpha}}{\sum_{j=1}^{N}j^{-\alpha}},
\quad f \in \{1,\ldots,N\},
```

where the default Zipf parameter is `alpha = 0.9`. A configurable mixture adds
server-specific preference boosts, providing synthetic spatial locality while
preserving the global long-tail pattern.

![Default Zipf content popularity](../docs/figures/content_popularity_zipf.png)

### 3.3 Wireless Channel and Rate

For distance `d_{u,k}` between user `u` and server `k`, deterministic path-loss
gain is

```math
g_{u,k}=g_0\left(
\frac{d_{\mathrm{ref}}}{\max(d_{u,k},d_{\min})}
\right)^{\eta}.
```

The default parameters are reference gain `g_0 = 10^{-3}`, reference distance
`d_ref = 1 m`, minimum distance `d_min = 1 m`, path-loss exponent `eta = 3.4`,
and transmit power `P = 0.2 W`. An optional fading model multiplies each link by
a clipped, unit-mean exponential power sample. This represents one reproducible
Rayleigh-fading snapshot, not temporal fading.

The simulator approximates interference as 0.15 times the sum of received
powers from non-serving servers. With bandwidth `B_u`, thermal-noise density
`sigma^2`, and noise figure `F`, the rate is

```math
R_u = B_u\log_2(1+\mathrm{SINR}_u),
```

```math
\mathrm{SINR}_u =
\frac{P g_{u,a_u}}
{\sigma^2 F B_u + I_u}.
```

Each edge server has 20 MHz downlink bandwidth shared among its associated
users. This abstraction keeps signal, interference, noise, and allocation
effects visible without representing a complete 3GPP physical layer.

### 3.4 Latency and Backhaul

Let `x_{k,f}` indicate whether server `k` stores file `f`, and let `a_i` and
`f_i` be the server and file for request `i`. The hit indicator is

```math
h_i=x_{a_i,f_i}.
```

For file size `s_{f_i}`, the end-to-end request latency is

```math
L_i = \frac{s_{f_i}}{R_{u_i}} +
(1-h_i)\left(T_{\mathrm{bh}}+
\frac{s_{f_i}}{R_{\mathrm{bh}}}\right).
```

The default backhaul has 80 ms fixed latency and 100 Mbit/s transfer rate.
Therefore, caching changes the second term, while channel quality and bandwidth
allocation primarily change the first term.

## 4. Problem Formulation and Metrics

The cache at every server must satisfy

```math
\sum_{f=1}^{N}s_f x_{k,f}\leq S_{\mathrm{cache}},
\quad x_{k,f}\in\{0,1\}.
```

The high-level goal is

```math
\min_x\;\bar{L}=\frac{1}{Q}\sum_{i=1}^{Q}L_i,
```

subject to the storage constraint and the selected bandwidth allocation rule.
Rather than solve this joint combinatorial problem exactly, the project compares
transparent heuristics. This choice keeps implementation and interpretation
appropriate for the project scope.

The main outcome metrics are average, median, and 95th-percentile latency;
cache hit ratio; backhaul traffic and load ratio; average wireless rate; average
wireless and backhaul delays; and Jain's fairness indices. For per-user
bandwidths `b_u`, Jain's index is

```math
J(b)=\frac{(\sum_u b_u)^2}{M\sum_u b_u^2}.
```

Values near one indicate a more uniform allocation. Fairness is reported as a
diagnostic rather than included in the optimization objective.

## 5. Compared Strategies

### 5.1 Static Caching Heuristics

**Random caching** uses a seeded random file order for each server and packs
feasible files until no additional file fits. It is the uninformed baseline.

**Prior-informed popularity caching** ranks files using the known Zipf
probabilities and applies the same ranking at every server. Its access to the
generating prior is stated explicitly in the held-out comparison.

**Local popularity caching** counts training requests from users associated
with each server and builds a separate file ranking for each region.

**Greedy latency-aware caching** estimates the local request-weighted backhaul
delay avoided by each file. Candidates are ranked by estimated saving per
cached Mbit, so both heterogeneous size and expected miss penalty influence
placement.

### 5.2 Bandwidth Allocation

Equal allocation divides each server's 20 MHz evenly among associated users.
Demand-aware allocation assigns a baseline share to every user and distributes
the remainder according to request count. The latter targets request-weighted
mean latency and is not intended to maximize fairness.

### 5.3 UCB-Style MAB Caching

At server `k`, each file is treated as an arm. During training epoch `e`, the
observed reward for a selected file is its local request frequency multiplied
by the backhaul delay a hit would avoid:

```math
r_{k,f,e}=\frac{n_{k,f,e}}{\max(1,n_{k,e})}
\left(T_{\mathrm{bh}}+\frac{s_f}{R_{\mathrm{bh}}}\right).
```

For previously selected arms, the UCB score is

```math
U_{k,f,e}=\bar{r}_{k,f}+
\beta\sqrt{\frac{\ln(e+1)}{N_{k,f}}},
```

where `N_{k,f}` is the selection count and `beta = 1.0`. Unseen feasible arms
receive exploration priority. Files are ranked by `U_{k,f,e}/s_f` and packed
under the cache budget. Training uses epochs of 200 requests and deterministic
seeded tie handling. After training, the final cache ranks learned mean reward
per Mbit and remains fixed during evaluation.

## 6. Experimental Method

### 6.1 Default Configuration

| Parameter | Value |
| --- | ---: |
| Files / users / edge servers | 50 / 100 / 4 |
| Requests | 5,000 |
| Service area | 500 m x 500 m |
| Cache budget per server | 40 Mbit |
| Zipf alpha | 0.9 |
| Spatial-locality strength | 0.35 |
| Server bandwidth | 20 MHz |
| Path-loss exponent | 3.4 |
| Backhaul latency / rate | 80 ms / 100 Mbit/s |
| Default random seed | 42 |

The experiment suite varies cache capacity, user count, Zipf alpha, spatial
locality, backhaul latency, server bandwidth, user-activity skew, file-size
variability, path-loss exponent, and optional snapshot fading. A multi-seed
cache-capacity sweep reports broad sensitivity to random topology and requests.

### 6.2 Held-Out Learning Protocol

The MAB comparison uses one common network and request trace for all policies.
The first 60% of requests is the chronological training prefix, and the final
40% is the held-out evaluation suffix. Local popularity, greedy, and MAB caches
use only the prefix. Random caching is seeded, while the global popularity
policy uses the known Zipf prior. All final caches are fixed on the suffix and
all strategies use equal bandwidth, isolating cache placement from allocation.

The final v2 experiment repeats this protocol for seeds 11, 22, 33, 44, and 55.
It reports arithmetic means, sample standard deviations (`ddof=1`), and paired
differences from the random policy within each seed. This is a modest robustness
check, not a statistical significance study.

### 6.3 Reproducibility

NumPy random generators receive explicit seeds for topology, requests, file
sizes, fading, random caching, and MAB tie order. Each experiment saves raw CSV
data and local metadata describing configuration, Python version, Git commit,
and output files. Final figures and Markdown findings are generated from saved
tables. The standard-library test suite checks probability normalization,
cache feasibility, bandwidth conservation, channel reproducibility, held-out
separation, multi-seed aggregation, and final result generation.

## 7. Results and Discussion

All numbers in this section are generated by repository scripts and are also
available in `report/generated_results.md` and
`results/data/key_findings.md`.

### 7.1 Default Joint Caching and Allocation Comparison

| Strategy | Avg. latency (ms) | P95 latency (ms) | Hit ratio | Backhaul load | Avg. rate (Mbit/s) | BW fairness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Random + equal BW | 1257.58 | 2866.95 | 0.167 | 0.833 | 5.60 | 0.981 |
| Global popularity + equal BW | 1210.70 | 2801.55 | 0.505 | 0.495 | 5.60 | 0.981 |
| Local popularity + equal BW | 1208.96 | 2802.35 | 0.526 | 0.474 | 5.60 | 0.981 |
| Greedy + equal BW | 1206.02 | 2823.16 | 0.579 | 0.421 | 5.60 | 0.981 |
| Greedy + demand-aware BW | 1204.33 | 3230.34 | 0.579 | 0.421 | 7.07 | 0.755 |

Greedy caching with demand-aware bandwidth has the lowest average latency in
the default table. Relative to random caching, average latency falls by 4.2%,
hit ratio rises by 41.2 percentage points, and backhaul traffic falls by 44.7%.
The much larger hit-ratio change than latency change indicates that wireless
transmission remains the dominant latency component in this configuration.

The result also reveals a tradeoff. Under the same greedy cache, demand-aware
allocation raises request-weighted average wireless rate by 26.3%, but Jain's
bandwidth-fairness index decreases from 0.981 to 0.755. Its P95 latency is
3230.34 ms, compared with 2823.16 ms under equal bandwidth. Therefore, the
small improvement in mean latency should not be described as an unqualified
improvement for every user or every request.

![Default bandwidth fairness](../docs/figures/main_bandwidth_fairness.png)

![Default wireless and backhaul latency components](../docs/figures/main_latency_breakdown.png)

### 7.2 Sensitivity Results

The cache-capacity experiments show the expected direction: increasing storage
raises hit ratio and lowers backhaul load, with request-aware policies improving
faster than random caching. Across the separate multi-seed cache-capacity study,
greedy caching with demand-aware bandwidth reduces mean latency by 5.2% relative
to random caching at the default eight-file-equivalent budget.

Spatial locality tests whether one global ranking is sufficient. At locality
strength 0.8, local popularity caching improves hit ratio by 3.3 percentage
points and lowers latency by 0.2% relative to global popularity caching. The
latency difference is small, which is consistent with wireless delay dominating
the end-to-end value even when hit ratio changes.

At user-activity parameter 1.2, demand-aware allocation lowers average latency
by 3.5% relative to equal allocation under the same greedy cache. The bandwidth
fairness index changes by -0.836, demonstrating that stronger activity skew
makes the latency/fairness tradeoff much sharper. In the file-size variability
sweep at lognormal sigma 1.0, greedy caching with demand-aware bandwidth has the
lowest average latency among the tested strategies, consistent with its
size-aware ranking.

The wireless-channel experiment varies path-loss exponent from 2.6 to 4.2 for
deterministic path loss and snapshot fading. It verifies that channel
assumptions affect both rate and end-to-end latency. The trend need not be
strictly monotonic because a larger exponent attenuates serving signal and
non-serving interference simultaneously in this simplified model. This is an
important interpretation boundary rather than evidence of an unexpected
physical advantage.

### 7.3 Single-Seed Held-Out MAB Comparison

| Caching strategy, equal BW | Avg. latency (ms) | P95 latency (ms) | Hit ratio | Backhaul load |
| --- | ---: | ---: | ---: | ---: |
| Random | 1283.90 | 2967.96 | 0.165 | 0.835 |
| Prior-informed popularity | 1234.58 | 2845.36 | 0.520 | 0.479 |
| Local popularity | 1233.64 | 2845.36 | 0.535 | 0.465 |
| Greedy | 1231.40 | 2910.17 | 0.582 | 0.418 |
| UCB-style MAB | 1234.35 | 2910.17 | 0.555 | 0.445 |

On seed 42, MAB improves substantially over random caching but is not the
lowest-latency strategy. It completes 15 training epochs, selects every
cache-feasible arm at least once, and uses 97.31% of cache capacity on average.
The 0.555 held-out hit ratio indicates that selected-arm feedback can learn a
useful placement. However, greedy caching achieves slightly lower latency and a
higher hit ratio with the same training prefix, so the evidence supports MAB as
an understandable adaptive baseline rather than a superior method.

### 7.4 Five-Seed V2 Comparison

| Strategy, equal BW | Avg. latency mean +/- std (ms) | Hit ratio mean +/- std | Paired latency vs random (ms) |
| --- | ---: | ---: | ---: |
| Random | 1228.31 +/- 78.66 | 0.177 +/- 0.032 | +0.00 +/- 0.00 |
| Prior-informed popularity | 1179.95 +/- 76.26 | 0.552 +/- 0.028 | -48.36 +/- 5.76 |
| Local popularity | 1180.40 +/- 76.01 | 0.548 +/- 0.025 | -47.91 +/- 5.53 |
| Greedy | 1180.53 +/- 73.94 | 0.562 +/- 0.019 | -47.77 +/- 6.45 |
| UCB-style MAB | 1183.25 +/- 75.28 | 0.540 +/- 0.020 | -45.05 +/- 5.97 |

![Five-seed average latency](../docs/figures/v2_strategy_latency_mean_std.png)

Absolute latency error bars overlap because each random seed changes topology,
file sizes, and demand for every policy. The paired comparison subtracts the
random result from each policy within the same seed and better isolates policy
effects.

![Paired latency difference from random caching](../docs/figures/v2_paired_latency_vs_random.png)

MAB records `1183.254 +/- 75.278 ms` mean latency and changes same-seed latency
by `-45.051 +/- 5.966 ms` relative to random. Its hit-ratio improvement over
random is `+0.3628 +/- 0.0233`. Mean arm coverage is 1.000 and mean final cache
utilization is 98.69%. Prior-informed popularity has the lowest mean latency at
1179.949 ms, while greedy has the highest mean hit ratio among the informed
policies. Differences among these informed methods are small compared with
cross-seed variation, so the table does not justify a universal ranking.

![Five-seed cache hit ratio](../docs/figures/v2_strategy_hit_ratio_mean_std.png)

### 7.5 Answers to the Research Questions

First, request-aware caching consistently improves hit ratio and backhaul load
relative to random caching under the simulated Zipf demand. Its effect on total
latency is smaller because radio transmission remains expensive. Second, cache
capacity, local demand, content-size variation, user activity, and channel
assumptions all change which latency component dominates; reporting only one
default run would hide these effects. Third, UCB-style caching successfully
learns a useful fixed cache from selected-arm feedback, but the held-out data do
not show it outperforming simpler informed heuristics. This negative result is
valuable because it prevents overclaiming and identifies non-stationary demand
as a more meaningful setting for future adaptive-policy research.

## 8. Limitations

The simulator deliberately omits many elements of an operational cellular
network:

- Users are static within each run, and association is always nearest-server.
- Traffic and file sizes are synthetic rather than measured traces.
- The path-loss model has no carrier-frequency or shadowing parameter, and
  fading is one bounded snapshot rather than a time-correlated process.
- Interference is a scaled received-power sum without scheduling, beamforming,
  frequency reuse, or inter-cell coordination.
- Shannon rate is an idealized upper-bound expression without modulation,
  coding, retransmission, queueing, or protocol overhead.
- Backhaul delay is fixed latency plus transfer time and has no congestion.
- Cache placement and bandwidth allocation are heuristic and have no global
  optimality guarantee.
- The MAB learner assumes stationary training demand and observes rewards only
  for cached files; five seeds are insufficient for broad statistical claims.
- Fairness is measured but not included in a multi-objective optimization.

Consequently, reported milliseconds should not be interpreted as predictions
for a particular operator or deployment. The reliable conclusions are the
controlled trends under the documented model.

## 9. Future Work

A natural next step is to introduce changing popularity between training and
evaluation. This would create a setting in which online adaptation may offer a
clearer advantage over static popularity and greedy caches. A contextual bandit
could then use server identity, time period, or content category while remaining
lighter than deep reinforcement learning.

For wireless realism, future work could add mobility, time-correlated fading,
shadowing, and a simple round-based scheduler. Measured or public content traces
would help calibrate file sizes and locality. For optimization validation, tiny
instances could be solved exactly with integer programming and used only as a
benchmark for heuristic optimality gaps. Finally, more random seeds,
confidence intervals, and fairness-aware objectives would strengthen the
experimental analysis without turning the project into a production simulator.

## 10. Conclusion

This project implements a complete, reproducible workflow for studying edge
caching and wireless resource allocation. It connects Zipf and local demand,
heterogeneous storage, path loss and optional fading, Shannon-based rate,
backhaul delay, static heuristics, demand-aware allocation, and lightweight MAB
learning. The default and sensitivity experiments show why cache hit ratio,
end-to-end latency, tail latency, and fairness must be considered together.
The held-out and five-seed results show that adaptive MAB caching improves over
random placement but does not automatically outperform simpler informed
policies.

The main outcome is therefore an engineering and research-method contribution:
a transparent model, controlled comparisons, reproducible scripts, tests, and
honest interpretation. This is an appropriate foundation for further study in
wireless communications, edge computing, and network optimization at the
graduate level.

## References

[1] M. A. Maddah-Ali and U. Niesen, "Fundamental Limits of Caching,"
*IEEE Transactions on Information Theory*, vol. 60, no. 5, pp. 2856-2867,
2014. DOI: 10.1109/TIT.2014.2306938.

[2] Y. Mao, C. You, J. Zhang, K. Huang, and K. B. Letaief, "A Survey on Mobile
Edge Computing: The Communication Perspective," *IEEE Communications Surveys
& Tutorials*, vol. 19, no. 4, pp. 2322-2358, 2017.
DOI: 10.1109/COMST.2017.2745201.

[3] G. S. Paschos, E. Bastug, I. Land, G. Caire, and M. Debbah, "Wireless
Caching: Technical Misconceptions and Business Barriers,"
*IEEE Communications Magazine*, vol. 54, no. 8, pp. 16-22, 2016.
DOI: 10.1109/MCOM.2016.7537172.

[4] L. Breslau, P. Cao, L. Fan, G. Phillips, and S. Shenker, "Web Caching and
Zipf-like Distributions: Evidence and Implications," *Proceedings of IEEE
INFOCOM*, 1999.

[5] A. Goldsmith, *Wireless Communications*. Cambridge University Press, 2005.
