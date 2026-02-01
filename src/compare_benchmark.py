import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Problem import Problem
from s339063 import solution


def score_solution(problem, actions):
    # Simulate the returned action list and compute total cost, while enforcing validity.
    G = problem.graph
    cur = 0              # start at base
    carried = 0.0        # current carried gold
    total = 0.0          # accumulated cost

    # Track remaining gold at each node
    remaining = {i: float(G.nodes[i].get("gold", 0.0)) for i in G.nodes}

    for city, take in actions:
        city = int(city)
        take = float(take)

        # Movement validity + movement cost
        if city != cur:
            if not G.has_edge(cur, city):
                raise ValueError(f"Invalid move: {cur}->{city} is not an edge.")           
            total += float(problem.cost([cur, city], carried))

        # Pickup validity
        if take < -1e-9:
            raise ValueError(f"Negative pickup at city {city}: {take}")
        if take > remaining[city] + 1e-6:
            raise ValueError(f"Too much pickup at {city}: took {take}, remaining {remaining[city]}")

        # Apply pickup
        remaining[city] -= take
        carried += take
        cur = city

        # Unload at base
        if cur == 0:
            carried = 0.0

    # Must end at base
    if cur != 0:
        raise ValueError("Solution does not end at base (0).")

    # Must collect all gold from non-base cities
    leftover = sum(v for i, v in remaining.items() if i != 0)
    if leftover > 1e-5:
        raise ValueError(f"Gold left uncollected: {leftover}")

    return float(total)


# Generate many random instances and compare baseline cost vs my solution
def run_benchmark(num_tests=50, seed=123):
    rng = np.random.default_rng(seed)

    improvements = []  # list of improvement percentages
    hi = []            # improvements for high-beta (>=1.5)
    lo = []            # improvements for low-beta (<1.5)

    # Track best and worst improvement cases with parameters
    best = (-1e18, None)
    worst = (1e18, None)

    print("Test#, N, Alpha, Beta, Density, BaselineCost, SolutionCost, Improvement%")
    for t in range(1, num_tests + 1):
        N = int(rng.integers(20, 101))
        alpha = float(rng.uniform(0.5, 5.0))
        beta = float(rng.uniform(0.5, 5.0))
        density = float(rng.uniform(0.25, 1.0))
        case_seed = int(rng.integers(1, 10_000_000))

        p = Problem(num_cities=N, alpha=alpha, beta=beta, density=density, seed=case_seed)

        base = float(p.baseline())
        plan = solution(p)
        my = float(score_solution(p, plan))

        impr = (base - my) / base * 100.0
        improvements.append(impr)
        (hi if beta >= 1.5 else lo).append(impr)

        print(f"{t:02d}, {N:3d}, {alpha:.3f}, {beta:.3f}, {density:.3f}, {base:.6f}, {my:.6f}, {impr:+.2f}")

        # Track best/worst
        if impr > best[0]:
            best = (impr, (N, alpha, beta, density, case_seed, base, my))
        if impr < worst[0]:
            worst = (impr, (N, alpha, beta, density, case_seed, base, my))

    # Summary stats
    avg = float(np.mean(improvements))
    best_i = float(np.max(improvements))
    worst_i = float(np.min(improvements))
    avg_hi = float(np.mean(hi)) if hi else float("nan")
    avg_lo = float(np.mean(lo)) if lo else float("nan")

    print("\n========== SUMMARY (50 tests) ==========")
    print(f"Average Improvement:           {avg:+.2f}%")
    print(f"Best Improvement:              {best_i:+.2f}%")
    print(f"Worst Improvement:             {worst_i:+.2f}%")
    print(f"Avg Improvement (β ≥ 1.5):     {avg_hi:+.2f}%  (count={len(hi)})")
    print(f"Avg Improvement (β < 1.5):     {avg_lo:+.2f}%  (count={len(lo)})")

    print("\nBest case details:")
    N, a, b, d, s, base, my = best[1]
    print(f"  N={N}, alpha={a:.3f}, beta={b:.3f}, density={d:.3f}, seed={s}")
    print(f"  baseline={base:.6f}, my={my:.6f}, improvement={best[0]:+.2f}%")

    print("\nWorst case details:")
    N, a, b, d, s, base, my = worst[1]
    print(f"  N={N}, alpha={a:.3f}, beta={b:.3f}, density={d:.3f}, seed={s}")
    print(f"  baseline={base:.6f}, my={my:.6f}, improvement={worst[0]:+.2f}%")


if __name__ == "__main__":
    run_benchmark(num_tests=50, seed=123)
