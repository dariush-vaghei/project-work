# Computational Intelligence Project — Gold Collection Optimization

This repository contains my solver and benchmarking code for the Computational Intelligence course project.

---

## Project Overview

This project implements an intelligent agent designed to solve a complex logistics optimization problem. The scenario involves a set of cities scattered across a grid, each containing a specific amount of gold. The agent must start from a central base, visit cities to collect gold, and return all collected resources to the base.

The core challenge lies not just in finding the shortest path (like a standard Traveling Salesperson Problem), but in minimizing a **non-linear cost function** where the "weight" of the gold carried exponentially increases the movement cost.

### The Environment
* **World:** A unit square grid $(0, 1) \times (0, 1)$.
* **Nodes:** $N$ cities, with City 0 serving as the "Base".
* **Resources:** Variable amounts of gold $g_i$ located at each city $i$.
* **Connectivity:** The cities are connected by a graph with variable edge density (not fully connected). The base edge weights are geometric distances.

---

## The Mathematical Model

The problem introduces a weighted cost function that makes standard pathfinding algorithms (like pure BFS or A*) insufficient on their own.

The cost $c$ to move between city $i$ and city $j$ is defined as:

$$
c = d_{ij} + (\alpha \cdot d_{ij} \cdot g)^\beta
$$

Where:
* $d_{ij}$ is the Euclidean distance between the cities.
* $g$ is the current amount of gold being carried by the agent.
* $\alpha$ represents a weight coefficient.
* $\beta$ represents the "fatigue" or non-linearity factor.

### The Optimization Trade-off
The optimal strategy relies heavily on the parameter $\beta$:
1.  **If $\beta \approx 1$ (Linear):** The problem behaves similarly to a Vehicle Routing Problem (VRP). The goal is to minimize total distance; carrying gold is "cheap."
2.  **If $\beta > 1$ (Non-Linear):** Carrying heavy loads over long distances becomes exponentially expensive. The optimal strategy shifts from "visiting many cities" to "making frequent short trips" to keep the carried weight $g$ low.

---

## Solution Strategy (`s339063.py`)

Since the problem parameters ($\alpha, \beta$) vary significantly between test instances, a single heuristic cannot solve all cases optimally. Therefore, my solution implements a **Portfolio Strategy**.

The agent generates multiple valid execution plans using distinct algorithms and simulates them against the exact cost function to select the best one.

### 1. Preprocessing: Shortest Path Calculation
Because the graph is not fully connected, the Euclidean distance is not always the valid movement path. The solution first runs **Dijkstra’s Algorithm** from the base and all gold-containing cities to compute the true shortest path distance matrix for the underlying graph topology.

### 2. Strategy A: Clarke-Wright Savings Heuristic (Merge-Trips)
* **Target Scenario:** Low $\beta$ (Carrying cost is manageable).
* **Logic:**
    1.  Start with a naive plan where every city is served by a dedicated trip: `Base -> City -> Base`.
    2.  Calculate the "savings" achieved by merging two trips (e.g., `Base -> A -> B -> Base` instead of two separate trips).
    3.  Store potential merges in a Max-Heap.
    4.  Greedily apply the merges that offer the highest cost reduction until no further improvements are possible.
* **Why it works:** This effectively solves the routing aspect, minimizing the distance traveled when the penalty for weight is not severe.

### 3. Strategy B: Capacity-Constrained Split-Load
* **Target Scenario:** High $\beta$ (Carrying cost is prohibitive).
* **Logic:**
    1.  The algorithm simulates an artificial "Capacity Cap" on the agent. Even though the problem allows infinite carrying capacity, the algorithm voluntarily limits the load to prevent the cost function from exploding.
    2.  It uses a greedy selection heuristic:
        $$Score = \frac{Distance(Current, Next) + Distance(Next, Base)}{GoldAmount(Next)}$$
    3.  The agent picks the city with the best score, adds it to the current trip, and returns to base immediately once the "Capacity Cap" is reached.
* **Adaptability:** Since the ideal capacity is unknown, the solution tests a portfolio of caps (derived from median gold amounts and $\alpha$) and picks the one that yields the lowest total cost.

### 4. Final Selection
The solution simulates the full path for the *Savings Heuristic* and several variations of the *Split-Load Heuristic*. The plan with the absolute lowest numeric cost is returned.

---

## Repository Structure

| File | Description |
| :--- | :--- |
| `s339063.py` | **The Solution.** Contains the pathfinding logic, heuristics, and the main `solution(p)` function. |
| `Problem.py` | **The Problem Class.** Generates random instances, defines the graph, and calculates the official cost. |
| `src/compare_benchmark.py` | **Benchmarking Tool.** Runs the solution against 50 random seeds to verify performance and stability. |

---

### 2. Running the Benchmark
To verify the solution's performance against the baseline (simple single-trip strategy), run the benchmark script:

```bash
python compare_benchmark.py
```

## Performance & Results
The solution was tested against **50 random instances** with varying $N$ (20-100), $\alpha$ (0.5-5.0), and $\beta$ (0.5-5.0).


### Full Benchmark Results
| Test# | N | Alpha | Beta | Density | Baseline Cost | Solution Cost | Improvement% |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | 21 | 0.742 | 1.492 | 0.388 | 66576.003611 | 20128.804775 | +69.77 |
| 02 | 47 | 4.154 | 4.655 | 0.457 | 6762476696689536.000000 | 1223640903.984473 | +100.00 |
| 03 | 83 | 4.505 | 2.808 | 0.434 | 25337749114.867619 | 12246484.731935 | +99.95 |
| 04 | 39 | 1.462 | 3.837 | 0.722 | 255266281025.192383 | 28156975.606054 | +99.99 |
| 05 | 55 | 1.544 | 4.096 | 0.639 | 2799603152140.458496 | 93849508.800982 | +100.00 |
| 06 | 84 | 1.247 | 2.740 | 0.687 | 492121095.797849 | 2296331.988688 | +99.53 |
| 07 | 53 | 0.567 | 2.620 | 0.796 | 11485674.256740 | 366777.966935 | +96.81 |
| 08 | 40 | 3.315 | 4.627 | 0.899 | 5167872403009502.000000 | 1195999466.664819 | +100.00 |
| 09 | 57 | 4.398 | 3.788 | 0.458 | 34604535740616.984375 | 190921047.572920 | +100.00 |
| 10 | 53 | 4.393 | 1.847 | 0.645 | 12874306.352452 | 410655.136833 | +96.81 |
| 11 | 63 | 3.125 | 1.571 | 0.824 | 1770096.470313 | 192774.561151 | +89.11 |
| 12 | 94 | 1.907 | 0.565 | 0.274 | 3547.503911 | 2827.446089 | +20.30 |
| 13 | 50 | 2.607 | 1.075 | 0.443 | 41381.484579 | 33013.657777 | +20.22 |
| 14 | 50 | 2.215 | 3.091 | 0.570 | 16412776474.271305 | 8257501.746997 | +99.95 |
| 15 | 60 | 3.274 | 1.697 | 0.858 | 3551929.488762 | 227976.818199 | +93.58 |
| 16 | 47 | 3.915 | 3.047 | 0.578 | 83158272003.835968 | 14372530.582574 | +99.98 |
| 17 | 95 | 0.600 | 2.612 | 0.718 | 31583131.475854 | 745440.512955 | +97.64 |
| 18 | 64 | 2.459 | 2.685 | 0.639 | 1580166542.895169 | 2778685.035096 | +99.82 |
| 19 | 61 | 3.105 | 0.817 | 0.616 | 10892.349557 | 10405.168970 | +4.47 |
| 20 | 50 | 3.847 | 2.434 | 0.477 | 796179116.497384 | 1844923.303356 | +99.77 |
| 21 | 58 | 3.904 | 0.849 | 0.617 | 17110.145550 | 16376.135144 | +4.29 |
| 22 | 89 | 4.284 | 4.777 | 0.489 | 47686739512078328.000000 | 4412797864.285837 | +100.00 |
| 23 | 46 | 2.019 | 4.155 | 0.849 | 13362686424034.845703 | 159402243.452251 | +100.00 |
| 24 | 86 | 1.529 | 1.120 | 0.568 | 48488.763557 | 35072.796093 | +27.67 |
| 25 | 43 | 4.430 | 1.306 | 0.273 | 389215.309351 | 116770.251137 | +70.00 |
| 26 | 67 | 2.430 | 4.364 | 0.371 | 90216946921587.484375 | 363253446.124658 | +100.00 |
| 27 | 91 | 3.382 | 4.690 | 0.446 | 6924784296909055.000000 | 1152337192.468916 | +100.00 |
| 28 | 81 | 1.171 | 3.831 | 0.470 | 206252107117.750153 | 40447881.941195 | +99.98 |
| 29 | 75 | 1.534 | 2.168 | 0.496 | 26357286.166901 | 552192.148249 | +97.90 |
| 30 | 70 | 2.951 | 3.873 | 0.471 | 7887243289965.791992 | 107816242.903160 | +100.00 |
| 31 | 54 | 2.946 | 3.557 | 0.766 | 840377189274.598877 | 38902538.203435 | +100.00 |
| 32 | 29 | 1.153 | 2.579 | 0.641 | 44379571.496168 | 402333.841974 | +99.09 |
| 33 | 90 | 1.311 | 2.768 | 0.745 | 574447023.684398 | 2668677.109737 | +99.54 |
| 34 | 41 | 1.483 | 4.797 | 0.794 | 284334899020607.562500 | 830137770.527504 | +100.00 |
| 35 | 45 | 4.917 | 0.538 | 0.449 | 1782.317457 | 1592.684453 | +10.64 |
| 36 | 74 | 0.862 | 4.346 | 0.359 | 1420904307520.564209 | 103088175.549894 | +99.99 |
| 37 | 96 | 4.031 | 4.529 | 0.596 | 6413255236437165.000000 | 1464871524.013795 | +100.00 |
| 38 | 59 | 1.919 | 0.569 | 0.512 | 2145.291349 | 1765.152852 | +17.72 |
| 39 | 23 | 1.693 | 3.434 | 0.946 | 27842520520.476048 | 6370582.152879 | +99.98 |
| 40 | 61 | 1.432 | 4.652 | 0.959 | 147003224352582.687500 | 891459321.817837 | +100.00 |
| 41 | 70 | 4.548 | 1.815 | 0.346 | 16703920.282883 | 530986.527028 | +96.82 |
| 42 | 98 | 3.918 | 0.898 | 0.822 | 36138.978757 | 35048.558743 | +3.02 |
| 43 | 91 | 2.385 | 1.144 | 0.740 | 106892.405878 | 65616.068410 | +38.61 |
| 44 | 53 | 2.272 | 4.121 | 0.594 | 12974536207255.714844 | 107454640.496887 | +100.00 |
| 45 | 78 | 4.019 | 3.267 | 0.971 | 510593337008.630127 | 31449682.230117 | +99.99 |
| 46 | 81 | 1.486 | 2.938 | 0.433 | 3295180675.927108 | 5226931.452174 | +99.84 |
| 47 | 84 | 3.904 | 1.690 | 0.485 | 6749446.810486 | 396340.858011 | +94.13 |
| 48 | 88 | 2.303 | 2.486 | 0.940 | 487472706.592609 | 2271149.409718 | +99.53 |
| 49 | 51 | 4.368 | 2.608 | 0.409 | 3931619781.762527 | 4548896.578013 | +99.88 |
| 50 | 37 | 0.859 | 1.116 | 0.452 | 14326.474985 | 11225.190623 | +21.65 |


### Key Findings
* **Overall Average Improvement:** +81.36%
* **High Beta ($\beta \ge 1.5$) Improvement:** +98.94%
  * In high beta cases, the baseline strategy often results in costs exceeding $10^{15}$ due to the exponential penalty. The optimized solution effectively mitigates this by splitting loads and/or smart trip merging.
* **Low Beta ($\beta < 1.5$) Improvement:** +25.70%
  * In low beta cases, improvements are smaller because load penalty is weaker and the baseline becomes closer to reasonable.

### Full Summary Statistics

```text
========== SUMMARY (50 tests) ==========
Average Improvement:           +81.36%
Best Improvement:              +100.00%
Worst Improvement:             +3.02%
Avg Improvement (β ≥ 1.5):     +98.94%  (count=38)
Avg Improvement (β < 1.5):     +25.70%  (count=12)

Best Case (High Beta):
  N=89, alpha=4.284, beta=4.777
  Baseline: 47,686,739,512,078,328.00
  Solution:      4,412,797,864.00
  Improvement: +100.00%

Worst Case (Low Beta):
  N=98, alpha=3.918, beta=0.898
  Baseline: 36,138.97
  Solution: 35,048.55
  Improvement: +3.02%
```

---
Student ID: s339063
