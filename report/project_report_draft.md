# Edge Caching and Resource Allocation for Latency Reduction in 5G/6G Wireless Networks

**Author:** Your Name  
**Program Interest:** Electrical Engineering / Communications Engineering  
**Project Type:** Undergraduate-level simulation and research exploration  
**Date:** YYYY-MM-DD

## Abstract

This project studies a simplified wireless edge network in which mobile users
request files from a content library and edge servers have limited cache
capacity. The objective is to reduce average content delivery latency by
comparing caching and bandwidth allocation strategies under Zipf-distributed
content requests. The implemented strategies include random caching, global
popularity-based caching, local popularity-based caching, greedy latency-aware
caching, and greedy caching with demand-aware bandwidth allocation. Wireless
rates are computed using a simplified Shannon capacity model, and cache misses
incur additional backhaul delay. The simulation evaluates average latency,
cache hit ratio, backhaul load, and wireless transmission rate under different
cache capacities, user densities, and content popularity parameters. The results
show that simple edge caching heuristics can reduce backhaul traffic and
latency in the simplified model, while demand-aware bandwidth allocation can
further improve request-weighted wireless performance.

## 1. Introduction

The growth of mobile data traffic creates an important challenge for future
wireless networks: how to deliver popular content with low latency while using
limited wireless and backhaul resources efficiently. In a conventional cloud
delivery architecture, content requested by mobile users may need to be fetched
from a remote server through the core network. This can increase backhaul load
and add delay, especially when many users repeatedly request popular content.

Edge caching is a practical idea in 5G and future 6G networks. By storing
frequently requested files at edge base stations or edge servers, the network
can serve cache hits locally and avoid repeated cloud retrieval. However, edge
storage is limited, so a key question is which files should be cached. Wireless
bandwidth is also limited, so resource allocation affects the final user
latency.

This project builds a Python-based simulation framework to explore these
tradeoffs. The goal is not to propose a new state-of-the-art algorithm. Instead,
the project demonstrates the ability to define a system model, implement
baseline and heuristic strategies, generate reproducible experiments, and
interpret results in the context of wireless communications and edge computing.

## 2. Background

Multi-access edge computing places storage and computation closer to users. In
wireless content delivery, edge caching can reduce latency when content
popularity is skewed. A common model for content popularity is the Zipf
distribution, where a small number of highly ranked files account for a large
fraction of requests. This long-tail behavior makes simple caching policies,
such as caching the most popular files, useful as baselines.

Resource allocation is another important aspect of wireless systems. Even if a
requested file is cached at the edge, it still needs to be transmitted over a
wireless link. Therefore, user latency depends on both cache placement and
wireless rate. This project combines these two ideas in a simplified simulation
so that the relationship between caching, backhaul delay, and wireless bandwidth
can be studied clearly.

## 3. System Model

The simulated network contains:

- `N` files in a content library
- `M` mobile users randomly distributed in a square service area
- `K` edge servers placed on a simple grid
- Cache capacity of `C` files at each edge server
- A sequence of `Q` user requests
- Nearest-server user association
- Wireless transmission rate based on a simplified SINR model
- Additional backhaul delay when content is not cached locally

The following figure illustrates the generated topology and nearest-server
association rule:

![Simulated wireless edge network topology](../docs/figures/network_topology.png)

Users generate file requests according to a Zipf distribution. The following
figure shows the long-tail request pattern used in the default simulation:

![Zipf content popularity distribution](../docs/figures/content_popularity_zipf.png)

## 4. Mathematical Formulation

### 4.1 Content Popularity

For a content library with `N` files, the request probability of file `f` is
modeled as:

```math
p_f = \frac{f^{-\alpha}}{\sum_{j=1}^{N} j^{-\alpha}}, \quad f = 1,2,\ldots,N.
```

The parameter `alpha` controls the skewness of the distribution. A larger
`alpha` means that requests are more concentrated on a few popular files.

### 4.2 Cache Placement Constraint

Let `x_{k,f}` indicate whether file `f` is cached at edge server `k`:

```math
x_{k,f} =
\begin{cases}
1, & \text{if file } f \text{ is cached at edge server } k, \\
0, & \text{otherwise}.
\end{cases}
```

Each edge server can store at most `C` files:

```math
\sum_{f=1}^{N} x_{k,f} \le C, \quad \forall k.
```

For request `i`, let `a_i` be the associated edge server and `f_i` be the
requested file. The cache hit indicator is:

```math
h_i = x_{a_i,f_i}.
```

The cache hit ratio is:

```math
H = \frac{1}{Q}\sum_{i=1}^{Q} h_i.
```

### 4.3 Wireless Rate Model

The downlink rate of user `u` is modeled using Shannon capacity:

```math
R_u = B_u \log_2(1 + \mathrm{SINR}_u),
```

where `B_u` is the bandwidth allocated to user `u`. A simplified SINR model is:

```math
\mathrm{SINR}_u =
\frac{P g_{u,a_u}}{\sigma^2 B_u + I_u}.
```

Here `P` is transmit power, `g_{u,a_u}` is the channel gain from the serving
edge server, `sigma^2 B_u` is noise power over the allocated bandwidth, and
`I_u` is a simplified interference term.

### 4.4 Latency Model

For request `i` generated by user `u`, the total latency is:

```math
L_i =
\frac{S}{R_u}
+ (1-h_i)\left(T_{\mathrm{bh}} + \frac{S}{R_{\mathrm{bh}}}\right).
```

The first term represents wireless transmission delay. The second term is paid
only when the request is a cache miss and the content must be fetched through
the backhaul.

The high-level objective is to reduce average latency:

```math
\min_x \frac{1}{Q}\sum_{i=1}^{Q} L_i,
```

subject to the cache capacity constraint. This project uses heuristic
strategies rather than solving the full combinatorial optimization problem.

## 5. Algorithms

### 5.1 Random Caching

Random caching selects cached files uniformly at random for each edge server.
It is used as a baseline because it does not use content popularity or local
demand information.

### 5.2 Global Popularity-Based Caching

Global popularity-based caching stores the most popular files at every edge
server according to the Zipf distribution. This strategy is simple and effective
when the same popular content is requested across the network.

### 5.3 Local Popularity-Based Caching

Local popularity-based caching estimates which files are requested most often
by users associated with each edge server. Each edge server then caches its own
local top files. This is still a simple heuristic, but it captures the idea that
different edge regions may observe different demand patterns.

### 5.4 Greedy Latency-Aware Caching

The greedy strategy estimates how much backhaul latency can be avoided by
caching each candidate file at each edge server. It then iteratively chooses
the server-file placement with the largest estimated latency reduction until
all caches are filled.

### 5.5 Bandwidth Allocation

Two bandwidth allocation methods are implemented:

- **Equal allocation:** each edge server divides bandwidth equally among its
  associated users.
- **Demand-aware allocation:** users that generate more requests receive a
  larger share of bandwidth, while every user still receives a small baseline
  share.

## 6. Experimental Setup

The default simulation uses 50 files, 100 users, 4 edge servers, and 5,000
content requests. The default cache capacity is 8 files per edge server.
Requests follow a Zipf distribution with `alpha = 0.9`. Each edge server has
20 MHz total bandwidth. Results are generated with a fixed random seed for
reproducibility.

The project includes the following experiments:

- Cache capacity sweep
- Number of users sweep
- Zipf popularity parameter sweep
- Backhaul latency sensitivity sweep
- Bandwidth sensitivity sweep
- Multi-seed cache capacity sweep with mean and standard deviation

The main metrics are average latency, cache hit ratio, backhaul load, average
wireless rate, wireless delay, and backhaul delay.

## 7. Results and Discussion

Report-ready tables are generated in `report/generated_results.md`. The tables
can be copied into this section after rerunning the experiments.

### 7.1 Default Scenario

In the default scenario, random caching has the highest average latency because
it often stores files that are not requested frequently. Global popularity,
local popularity, and greedy caching all improve performance by increasing the
cache hit ratio and reducing backhaul traffic.

Compared with random caching, greedy caching with demand-aware bandwidth
allocation reduces average latency by **4.3%** in the default configuration.
The cache hit ratio improves by **36.6 percentage points**, and backhaul traffic
decreases by **44.8%**. These results should be interpreted within the simplified
simulation assumptions rather than as universal 5G/6G performance guarantees.

### 7.2 Latency vs Cache Capacity

The following figure shows how latency changes as edge cache capacity increases:

![Latency vs cache capacity](../docs/figures/latency_vs_cache_capacity.png)

The general trend is that larger cache capacity reduces average latency because
more requests can be served from the edge. Random caching improves more slowly
because it does not prioritize popular content. Popularity-based, local
popularity-based, and greedy caching show better latency performance.

### 7.3 Multi-Seed Robustness

The multi-seed experiment repeats the cache capacity sweep over multiple random
network and request realizations:

![Multi-seed latency vs cache capacity](../docs/figures/multi_seed_latency_vs_cache_capacity.png)

At the default cache capacity of 8 files, the same best strategy reduces mean
latency by **5.6%** relative to random caching across the multi-seed experiment.
The shaded regions show that random placement and request traces introduce
variation, but the overall trend remains consistent.

### 7.4 Interpretation

The results support three main observations. First, edge caching is useful when
content popularity is skewed because popular files account for many requests.
Second, local demand information can be useful, although in this simplified
setting local popularity and greedy caching are often similar because both are
driven mainly by local request counts. Third, bandwidth allocation can further
improve latency when user demand is uneven.

The backhaul latency sensitivity experiment provides an additional way to
interpret the system. When backhaul latency is low, a cache miss is less
expensive, so the gap between random caching and caching-aware strategies is
smaller. When backhaul latency is high, avoiding cloud or core-network retrieval
becomes more important, so cache placement has a clearer impact on latency.

The bandwidth sensitivity experiment focuses on the wireless resource side of
the system. When bandwidth is limited, wireless transmission delay dominates a
larger share of total latency. As bandwidth increases, wireless delay decreases,
and the remaining latency difference among strategies is more strongly related
to cache misses and backhaul delay.

## 8. Limitations

This project intentionally simplifies many aspects of real 5G/6G networks:

- Users are static during one simulation run.
- File sizes are fixed.
- The wireless channel uses a simplified path-loss and interference model.
- Backhaul latency is modeled with a fixed component and transfer time.
- The greedy caching algorithm is heuristic and does not guarantee optimality.
- The demand-aware bandwidth policy is simple and does not solve a full radio
  resource optimization problem.

These limitations are acceptable for an undergraduate-level simulation project,
but they should be clearly stated in any application or presentation.

## 9. Future Work

Possible future improvements include:

- Adding user mobility and time-varying association
- Modeling heterogeneous file sizes
- Adding small-scale fading in the channel model
- Comparing with exact optimization on small problem instances
- Studying fairness among users
- Adding a simple multi-armed bandit caching extension

## 10. Conclusion

This project demonstrates a reproducible simulation framework for studying edge
caching and resource allocation in simplified 5G/6G wireless edge networks. It
connects wireless rate modeling, content popularity, cache placement, backhaul
delay, and bandwidth allocation into one coherent simulation workflow. The
project is appropriate as an undergraduate research exploration and can support
a graduate school application by showing interest in communications, edge
computing, and network optimization.

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
