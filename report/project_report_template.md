# Edge Caching and Resource Allocation for Latency Reduction in 5G/6G Wireless Networks

**Author:** Your Name  
**Program Interest:** Electrical Engineering / Communications Engineering  
**Date:** YYYY-MM-DD

## Abstract

This project investigates a simplified wireless edge network where mobile users
request content from a finite library and edge servers cache a limited number of
files. The objective is to reduce average content delivery latency by comparing
several caching and resource allocation strategies, including random caching,
global popularity-based caching, local popularity-based caching, greedy
latency-aware caching, and greedy caching with demand-aware bandwidth
allocation. User requests are generated according to a Zipf distribution,
wireless rates are modeled using a Shannon capacity formula, and cache misses
incur additional backhaul delay. Simulation results are used to evaluate average
latency, cache hit ratio, backhaul traffic, and wireless transmission rate under
varying cache capacities, user densities, and popularity parameters. The project
demonstrates an undergraduate-level research exploration of edge computing and
wireless network optimization for 5G/6G systems.

## 1. Introduction

The rapid growth of mobile data traffic has increased the importance of low
latency content delivery in wireless networks. Applications such as video
streaming, augmented reality, industrial monitoring, and connected vehicles may
require both high data rates and fast response times. In conventional network
architectures, requested content may need to be fetched from a remote cloud or
core network, which adds backhaul delay and increases network load.

Edge caching is a promising technique for reducing latency by storing popular
content near users at edge base stations or edge servers. When requested content
is available locally, the network can avoid fetching it from the cloud. However,
edge servers have limited storage capacity, so caching decisions must be made
carefully. At the same time, radio bandwidth is limited and must be allocated
among users. This creates a joint problem involving content popularity, cache
capacity, wireless transmission rate, and user demand.

This project builds a Python simulation framework to study this problem in a
simplified but interpretable setting. The goal is not to develop a highly novel
algorithm, but to demonstrate the ability to formulate a communications problem,
implement simulation models, compare baselines, and analyze performance trends.

## 2. Background on 5G/6G Edge Caching

In 5G and future 6G networks, multi-access edge computing places computing and
storage resources closer to end users. This can reduce traffic through the core
network and improve latency-sensitive services. Edge caching is especially
useful when content popularity is skewed, meaning that a small fraction of files
accounts for a large fraction of requests.

Content popularity is often represented by a Zipf distribution. Under this
distribution, the most popular files are requested much more frequently than
less popular files. This property creates an opportunity: if edge servers cache
popular files, many requests can be served locally. However, the benefit depends
on cache size, request distribution, user association, and wireless resource
allocation.

## 3. System Model

The simulated network consists of:

- `N` files in a content library
- `M` mobile users randomly distributed in a square area
- `K` edge servers placed on a grid
- A limited cache capacity of `C` files at each edge server
- A sequence of `Q` user content requests

Each user is associated with the nearest edge server. If the requested file is
stored at the associated edge server, the request is a cache hit and avoids
backhaul transmission. If not, the file must be fetched through the backhaul or
core network.

Insert `results/figures/network_topology.png` here to illustrate the simulated
user positions, edge server positions, and nearest-server association rule.

Wireless transmission rate depends on allocated bandwidth, transmit power,
channel gain, noise, and simplified interference. The system model is
implemented in the `src/` directory of the repository.

## 4. Problem Formulation

### 4.1 Content Popularity

Let the content library contain `N` files. File popularity follows a Zipf
distribution:

```math
p_f = \frac{f^{-\alpha}}{\sum_{j=1}^{N} j^{-\alpha}}, \quad f = 1, 2, ..., N.
```

Here, `p_f` is the probability that file `f` is requested and `alpha` controls
the skewness of the popularity distribution. A larger `alpha` means that a small
number of popular files dominate the request traffic.

Insert `results/figures/content_popularity_zipf.png` here to show the long-tail
request distribution used in the simulation.

### 4.2 Cache Placement

Let

```math
x_{k,f} =
\begin{cases}
1, & \text{if file } f \text{ is cached at edge server } k, \\
0, & \text{otherwise}.
\end{cases}
```

The cache capacity constraint is:

```math
\sum_{f=1}^{N} x_{k,f} \le C, \quad \forall k.
```

For request `i`, let `a_i` denote the associated edge server and `f_i` denote
the requested file. The cache hit indicator is:

```math
h_i = x_{a_i,f_i}.
```

The cache hit ratio is:

```math
H = \frac{1}{Q}\sum_{i=1}^{Q} h_i.
```

### 4.3 Wireless Rate Model

The downlink transmission rate of user `u` is modeled using Shannon capacity:

```math
R_u = B_u \log_2(1 + \mathrm{SINR}_u),
```

where `B_u` is the bandwidth allocated to user `u`. A simplified SINR model is:

```math
\mathrm{SINR}_u =
\frac{P g_{u,a_u}}{\sigma^2 B_u + I_u},
```

where `P` is transmit power, `g_{u,a_u}` is the channel gain from the serving
edge server, `sigma^2 B_u` represents thermal noise over the allocated
bandwidth, and `I_u` is simplified inter-cell interference.

### 4.4 Latency Model

For request `i` generated by user `u`, the total latency is:

```math
L_i = \frac{S}{R_u} + (1 - h_i)\left(T_{\mathrm{bh}} + \frac{S}{R_{\mathrm{bh}}}\right).
```

Here, `S` is file size, `T_bh` is fixed backhaul latency, and `R_bh` is backhaul
transmission rate. If the request is a cache hit, the backhaul term is zero.

The optimization objective is:

```math
\min_x \frac{1}{Q}\sum_{i=1}^{Q} L_i
```

subject to the cache capacity constraints. Since this is a combinatorial
problem, this project compares practical heuristic strategies instead of solving
the full optimization exactly.

## 5. Caching Strategies

### 5.1 Random Caching

Random caching is used as a baseline. Each edge server randomly selects `C`
files from the library. This method does not use content popularity or user
location information.

### 5.2 Popularity-Based Caching

Popularity-based caching stores the globally most popular `C` files at every
edge server. This strategy is simple and effective when the popularity
distribution is strongly skewed. However, it does not adapt to local differences
in user demand near different edge servers.

### 5.3 Local Popularity-Based Caching

Local popularity-based caching uses the simulated request trace to estimate the
most frequently requested files among users associated with each edge server.
Each edge server then caches its own local top `C` files. This remains a simple
heuristic, but it captures the idea that edge servers may observe different
local demand patterns.

### 5.4 Greedy Latency-Aware Caching

The greedy caching strategy estimates the backhaul latency saved by placing each
candidate file at each edge server. It then iteratively chooses the server-file
pair that provides the largest latency reduction until all cache capacities are
filled. This makes the policy local-demand-aware while remaining easy to
understand and implement.

## 6. Resource Allocation Strategies

Two bandwidth allocation methods are compared:

1. **Equal bandwidth allocation:** Each edge server divides its total bandwidth
   equally among associated users.
2. **Demand-aware bandwidth allocation:** Each edge server allocates more
   bandwidth to users that generate more requests in the simulated trace.

The second method is a simple heuristic rather than a full radio resource
optimization solver. Its purpose is to show how demand information can be used
to improve request-weighted latency.

## 7. Experimental Setup

The default simulation uses the following general setup:

- A square service area with randomly placed users
- Grid-placed edge servers
- Zipf-distributed content requests
- Distance-based path loss
- Shannon-rate wireless transmission
- Fixed file size and backhaul latency
- Reproducible random seed

Three parameter sweeps are performed:

1. **Cache capacity experiment:** evaluates latency and cache hit ratio as cache
   capacity increases.
2. **User density experiment:** evaluates latency and wireless rate as the
   number of users increases.
3. **Zipf experiment:** evaluates latency and cache hit ratio as content
   popularity becomes more or less concentrated.

In addition, a multi-seed cache capacity experiment repeats the simulation over
several random seeds. This reports the mean and standard deviation of the main
metrics, which helps distinguish stable performance trends from artifacts of a
single random network realization.

The main metrics are average latency, cache hit ratio, backhaul traffic, and
average wireless transmission rate.

## 8. Results and Discussion

After running the simulation, insert the generated figures from
`results/figures/` into this section.

The script `summarize_results.py` can be used to generate
`results/data/key_findings.md`, which provides a short numerical summary of the
default simulation and multi-seed experiment. Use those values to support the
discussion below, while noting that they depend on the simplified simulation
configuration.

The script `generate_report_assets.py` can also generate
`report/generated_results.md`, including Markdown tables and figure references
that can be copied into the report.

### 8.1 Average Latency

Discuss how average latency differs among random caching, popularity-based
caching, local popularity-based caching, greedy caching, and greedy caching with
demand-aware bandwidth allocation. A reasonable expected result is that random
caching performs worst, while popularity-based, local popularity-based, and
greedy caching reduce latency by increasing cache hit ratio and reducing
backhaul delay. If using the multi-seed experiment, discuss whether the standard
deviation bands are small enough to support the observed trend.

### 8.2 Cache Hit Ratio

Discuss how cache hit ratio changes with cache capacity. The hit ratio should
generally increase as each edge server can store more files. When the Zipf alpha
is high, popular files dominate the request process, so caching the top files
can produce a larger benefit.

### 8.3 Backhaul Traffic

Backhaul traffic is directly related to cache misses. As cache hit ratio
increases, the amount of content fetched from the cloud or core network should
decrease. This demonstrates the network-level benefit of edge caching beyond
individual user latency.

### 8.4 Wireless Rate and User Density

As the number of users increases, each edge server must share bandwidth among
more users. Therefore, average wireless rate may decrease and wireless
transmission delay may increase. This illustrates why resource allocation is an
important part of latency reduction.

## 9. Limitations

This simulation intentionally simplifies many aspects of real 5G/6G systems:

- Users are static during one simulation run.
- File size is fixed for all content.
- Channel fading is not modeled in detail.
- Interference is represented by a simplified factor.
- Backhaul delay is modeled as a fixed term plus transfer time.
- The greedy caching method is heuristic and does not guarantee global
  optimality.

These simplifications keep the project understandable and reproducible while
still preserving the main engineering tradeoffs.

## 10. Future Work

Future improvements could include:

- User mobility and time-varying association
- Small-scale fading and more realistic path-loss models
- Heterogeneous file sizes and content update dynamics
- Multi-armed bandit or reinforcement learning based caching
- Fairness-aware bandwidth allocation
- Energy consumption analysis
- Comparison with exact optimization for small problem instances

## 11. Conclusion

This project presents a Python-based simulation framework for studying edge
caching and resource allocation in simplified 5G/6G wireless networks. The
results can help illustrate how caching popular content at edge servers reduces
backhaul traffic and latency, and how bandwidth allocation affects wireless
transmission delay. Although the model is simplified, it provides a clear
research-oriented foundation for understanding the interaction between edge
computing, wireless communication, and network optimization.

For a graduate school application, this project can be presented as evidence of
interest in wireless networks, ability to implement reproducible simulations,
and motivation to study advanced communication systems.

## References

[1] M. A. Maddah-Ali and U. Niesen, "Fundamental Limits of Caching," *IEEE
Transactions on Information Theory*, vol. 60, no. 5, pp. 2856-2867, 2014.
DOI: 10.1109/TIT.2014.2306938.

[2] Y. Mao, C. You, J. Zhang, K. Huang, and K. B. Letaief, "A Survey on Mobile
Edge Computing: The Communication Perspective," *IEEE Communications Surveys &
Tutorials*, vol. 19, no. 4, pp. 2322-2358, 2017.
DOI: 10.1109/COMST.2017.2745201.

[3] G. S. Paschos, E. Bastug, I. Land, G. Caire, and M. Debbah, "Wireless
Caching: Technical Misconceptions and Business Barriers," *IEEE Communications
Magazine*, vol. 54, no. 8, pp. 16-22, 2016. DOI: 10.1109/MCOM.2016.7537172.

[4] L. Breslau, P. Cao, L. Fan, G. Phillips, and S. Shenker, "Web Caching and
Zipf-like Distributions: Evidence and Implications," *Proceedings of IEEE
INFOCOM*, 1999.

[5] A. Goldsmith, *Wireless Communications*. Cambridge University Press, 2005.
