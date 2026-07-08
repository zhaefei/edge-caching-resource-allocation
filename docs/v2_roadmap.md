# Version 2.0 Roadmap

This roadmap defines the planned upgrade path for turning the existing edge
caching simulation into a polished graduate-school application portfolio
project. The goal is to improve research clarity, reproducibility, and
communication value without rewriting the repository or overstating novelty.

## Final v2.0 Project Target

The v2.0 target is a reproducible undergraduate-level research simulation on
latency reduction in wireless edge networks. The final project should connect
three themes:

- Edge caching under Zipf-distributed and spatially local content demand
- Wireless channel modeling with path loss and optional lightweight fading
- Lightweight learning-based or adaptive resource/caching decisions, including a
  simple Multi-Armed Bandit caching baseline

The final repository should be suitable for a graduate application portfolio. It
should present the work as a solid simulation and research exploration, not as a
novel 5G/6G standard, production system, or state-of-the-art optimizer.

## 14-Iteration Upgrade Plan

1. **Project health check and iteration state setup**  
   Establish iteration tracking, run the current tests, and confirm the project
   has a clean reproducible baseline.

2. **Repository structure cleanup and reproducibility baseline**  
   Review project organization, result directories, health checks, and metadata
   so later experiments remain easy to reproduce.

3. **Design wireless channel model interface**  
   Introduce a small channel-model abstraction so the network model can support
   different channel assumptions without rewriting the simulator.

4. **Implement path loss wireless channel model**  
   Move the existing path-loss behavior into the channel interface and keep the
   default model transparent and beginner-friendly.

5. **Implement optional fading and tests**  
   Add optional lightweight fading with fixed seeds and tests, while keeping path
   loss as the default baseline.

6. **Add wireless channel experiment**  
   Compare latency and rate behavior under different channel assumptions or
   parameters.

7. **Design Multi-Armed Bandit caching policy**  
   Document a simple, understandable MAB caching design and how it fits into the
   existing caching strategy interface.

8. **Implement Multi-Armed Bandit caching policy**  
   Add the MAB policy with deterministic seeds and focused tests.

9. **Add MAB comparison experiment**  
   Compare MAB caching against random, popularity, local popularity, and greedy
   caching in a controlled experiment.

10. **Add multi-seed v2 experiment runner**  
    Extend multi-seed evaluation to cover the final v2 strategy set and report
    mean/std trends.

11. **Generate final figures and result summaries**  
    Regenerate final CSV outputs, figures, generated tables, and key findings
    from scripts.

12. **Update README and model assumptions**  
    Make README and `docs/model_assumptions.md` consistent with the final v2
    model and experiments.

13. **Write final mini research report**  
    Create `report/project_report_final.md` with academic but undergraduate-level
    tone, including equations, experiments, results, limitations, and references.

14. **Final reproduction check, cleanup, and portfolio summary**  
    Run the full reproduction workflow, verify final deliverables, and write
    `docs/portfolio_summary.md`.

## Scope Control

The roadmap intentionally avoids heavy dependencies, deep learning frameworks,
full 3GPP system-level simulation, and claims of algorithmic novelty. Each
iteration should make a small, reviewable change and run the relevant tests.

