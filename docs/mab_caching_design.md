# UCB-Style MAB Caching Design

## Status and Scope

This document specifies the lightweight learning-based caching extension for
Iterations 8 and 9. The policy and focused tests were implemented in Iteration
8. Iteration 9 added the controlled held-out comparison and reproducible output
artifacts. Iteration 10 repeats the same protocol over five fixed seeds and
reports raw values, sample standard deviations, and paired baseline differences.

The implemented policy is a UCB-style combinatorial semi-bandit baseline. It is
intended to demonstrate online learning, exploration versus exploitation, and
storage-aware cache selection at an undergraduate research level. It is not a
new bandit algorithm and is not expected to be optimal.

## Design Goals

- Reuse the existing `CacheState` representation and cache-size constraint.
- Keep each edge server's learning process independent and understandable.
- Learn from a chronological training segment and evaluate on unseen requests.
- Use an explicit random generator and deterministic tie breaking.
- Support heterogeneous file sizes without adding an optimization package.
- Return diagnostics that make the learning behavior inspectable.

## Arms, Rounds, and Cache Actions

For edge server `k`, each content file `f` is one arm. The training request
trace is divided into fixed-size epochs. At the start of epoch `e`, the policy
chooses a set of cached files `A_{k,e}` subject to

```math
\sum_{f \in A_{k,e}} s_f \leq S_{\mathrm{cache}},
```

where `s_f` is the file size and `S_cache` is the storage budget of one edge
server. Selecting several files makes this a small combinatorial semi-bandit
rather than a single-arm bandit.

The implementation ranks files and reuses the project's existing ordered
budget-packing helper. It does not introduce an integer-programming solver.

## Observed Reward

Let `n_{k,f,e}` be the number of requests for file `f` at server `k` during
epoch `e`, and let `n_{k,e}` be the total number of local requests in that
epoch. The backhaul delay avoided by one hit for file `f` is

```math
d_f^{\mathrm{bh}} = D_{\mathrm{bh}} + \frac{s_f}{R_{\mathrm{bh}}} \times 1000.
```

For a selected file, the epoch reward is the avoided backhaul latency per local
request:

```math
r_{k,f,e} =
\frac{n_{k,f,e}}{\max(1, n_{k,e})} d_f^{\mathrm{bh}},
\qquad f \in A_{k,e}.
```

The units are milliseconds saved per local request. Only selected files update
their bandit statistics. Although a practical cache controller can also observe
the identities of missed requests, deliberately using selected-arm feedback
keeps this extension interpretable as a semi-bandit baseline. This limitation
must be stated when discussing results.

## UCB Score and Storage-Aware Ranking

For every server-file arm, maintain:

- `T_{k,f}`: number of epochs in which the file was selected
- `Q_{k,f}`: running mean of its observed epoch reward

At the beginning of epoch `e`, compute

```math
U_{k,f}(e) = Q_{k,f} + \beta
\sqrt{\frac{\ln(e+1)}{T_{k,f}}},
```

where `beta` is the exploration coefficient. An arm with `T_{k,f}=0` receives
priority for exploration. Because files have different sizes, rank them by

```math
\rho_{k,f}(e) = \frac{U_{k,f}(e)}{s_f}.
```

Files are considered in descending score-density order and packed until no
additional file fits. A seeded tie order prevents file identifiers from
silently determining exploration.

After observing the epoch reward for a selected file, update its mean online:

```math
T_{k,f} \leftarrow T_{k,f} + 1,
```

```math
Q_{k,f} \leftarrow Q_{k,f}
+ \frac{r_{k,f,e} - Q_{k,f}}{T_{k,f}}.
```

After training, the final evaluation cache uses `Q_{k,f} / s_f` without the
exploration bonus. This separates learning-time exploration from the fixed
cache placement evaluated on held-out requests.

## Training and Evaluation Protocol

The Iteration 9 experiment uses one reproducible chronological split of the
generated request trace:

- First 60% of requests: cache-policy training
- Final 40% of requests: metric evaluation

The split must happen after generating one common network and request trace.
MAB, local popularity, and greedy latency-aware caching must use only the
training segment. All final caches must be evaluated on the same held-out
segment. Random and global popularity baselines do not need observed local
requests, but they must use the same file sizes, network, and evaluation trace.
Because the current global popularity policy receives the Zipf probabilities
used by the generator, it should be labeled as a static prior-informed baseline
rather than a policy with the same feedback as MAB.

The initial MAB comparison uses equal bandwidth allocation for every
caching policy. Holding bandwidth allocation fixed isolates the effect of cache
learning. A later result may add demand-aware bandwidth as a separate analysis,
but it should not be mixed into the primary MAB caching comparison.

## Implementation Interface

Iteration 8 added a beginner-readable function to
`src/caching_algorithms.py` with this interface:

```python
def mab_ucb_caching(
    config: SimulationConfig,
    network: NetworkState,
    training_user_ids: np.ndarray,
    training_file_ids: np.ndarray,
    file_sizes_mbits: np.ndarray,
    rng: np.random.Generator,
) -> tuple[CacheState, MABCachingDiagnostics]:
    ...
```

The diagnostic object contains the selection counts, estimated mean rewards,
number of completed epochs, and fraction of cache-feasible arms explored.
Oversized files are excluded from the coverage denominator because they cannot
be selected under the configured budget. Cache selection itself remains a
function rather than a large framework or class hierarchy.

The reproducible configuration fields are:

- `mab_training_fraction = 0.60`
- `mab_update_interval = 200`
- `mab_exploration_weight = 1.0`
- `mab_seed_offset = 3000`

These are simulation parameters, not tuned claims of optimal performance.

## Pseudocode

```text
initialize mean rewards Q and selection counts T to zero
create one seeded tie order for each edge server

for each chronological training epoch e:
    for each edge server k:
        compute UCB reward density for every file
        select files in score order under the cache budget
        observe selected-file rewards from this epoch's local requests
        update Q and T for selected files

for each edge server k:
    rank files by learned mean reward per Mbit
    pack the final fixed cache under the same storage budget

return final caches and learning diagnostics
```

## Iteration 8 Verification

- Fixed seeds produce exactly the same caches and diagnostics.
- Every cache respects the heterogeneous file-size budget.
- Every selected file identifier is inside the content library.
- Selection counts and estimated rewards have shape `(K, N)` and remain finite.
- An arm's incremental mean update matches a hand-calculated example.
- Empty local epochs and servers with no requests do not produce NaN values.
- Oversized files are skipped consistently with existing caching policies.
- The learning interface accepts only the caller-provided training arrays;
  the Iteration 9 leakage test confirms that changing evaluation requests does
  not change learned caches or MAB diagnostics.

## Iteration 9 Comparison Implementation

The experiment uses equal bandwidth allocation and compares final held-out
metrics for:

- Random caching
- Global popularity caching
- Local popularity caching trained on the training segment
- Greedy latency-aware caching trained on the training segment
- UCB-style MAB caching trained on the same segment

The output reports average latency, P95 latency, cache hit ratio, backhaul load,
and average wireless rate. It also records MAB arm coverage and epoch count as
learning diagnostics. The MAB policy may underperform a static baseline in a
stationary Zipf trace; that is a valid result and should not be hidden.

## Limitations

- The generated request process is stationary within a run, so adaptivity may
  offer limited benefit over well-estimated popularity.
- Reward feedback intentionally ignores information from uncached-file misses.
- Cache placement changes only between epochs, not after every request.
- Independent server learners do not coordinate duplicate content placement.
- UCB score-density packing is a heuristic for a capacity-constrained action;
  it is not an exact combinatorial-bandit optimizer.
- Hyperparameters are fixed for reproducibility rather than extensively
  tuned on the evaluation data.
- A short training trace may not provide enough epochs to explore every arm;
  arm coverage must therefore be reported rather than assumed.
- The five-seed summary is a lightweight robustness check and does not establish
  general performance across all network deployments.
