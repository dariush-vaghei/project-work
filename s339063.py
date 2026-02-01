# s339063.py
from __future__ import annotations

from typing import Dict, List, Tuple
import heapq
import numpy as np
import networkx as nx

from Problem import Problem

EPS = 1e-9


def solution(p: Problem) -> List[Tuple[int, float]]:
    G: nx.Graph = p.graph
    n = G.number_of_nodes()

    alpha = float(p.alpha)
    beta = float(p.beta)
    gold = np.array([float(G.nodes[i].get("gold", 0.0)) for i in range(n)], dtype=float)

    # "Customers" are non-base cities with positive gold
    customers = [i for i in range(1, n) if gold[i] > EPS]
    if not customers:
        return [(0, 0.0)]

    # -------------------------
    # Precompute shortest paths (by distance) from 0 and from all gold cities
    # -------------------------
    sources = [0] + customers

    # lengths[s][t] = shortest distance from s to t
    lengths: Dict[int, Dict[int, float]] = {}

     # paths[s][t] = list of nodes on a shortest path from s to t
    paths: Dict[int, Dict[int, List[int]]] = {}
    
    for s in sources:
        d, sp = nx.single_source_dijkstra(G, source=s, weight="dist")
        lengths[s] = {k: float(v) for k, v in d.items()}
        paths[s] = sp

    # Convert node path [u..v] into action steps, picking only at the final node.
    def expand_path(path_nodes: List[int], pickup_at_end: float) -> List[Tuple[int, float]]:
        out: List[Tuple[int, float]] = [(int(v), 0.0) for v in path_nodes[1:]]
        if out:
            out[-1] = (out[-1][0], float(pickup_at_end))
        return out

    # Exact simulation cost. Also validates feasibility.
    def plan_cost(actions: List[Tuple[int, float]]) -> float:
        cur = 0
        carried = 0.0
        total = 0.0

        # Remaining gold per node
        rem = gold.copy()

        for city, take in actions:
            city = int(city)
            take = float(take)

            # Movement cost
            if city != cur:
                if not G.has_edge(cur, city):
                    return float("inf")
                total += float(p.cost([cur, city], carried))

            # Pickup validity
            if take < -1e-9 or take > rem[city] + 1e-6:
                return float("inf")

            # Apply pickup
            rem[city] -= take
            carried += take
            cur = city

            # Unload at base
            if cur == 0:
                carried = 0.0

        # Must end at base
        if cur != 0:
            return float("inf")
        
        # Must have collected all gold from non-base cities
        if float(rem[1:].sum()) > 1e-5:
            return float("inf")
        
        return float(total)

    # -------------------------
    # Candidate A: Merge trips (Clarke-Wright-style savings heuristic)
    # -------------------------
    """
    Idea:
    - Start with one trip per city: 0 -> c -> 0.
    - Consider merging two trips into one multi-stop trip.
    - If merging reduces total cost (positive saving), do it.
    - Use a max-heap on savings to greedily apply best merges first.
    """
    def trip_cost(order: List[int]) -> float:
        # Exact cost of one trip 0->order...->0, picking ALL gold at visited cities.
        cur = 0
        carried = 0.0
        total = 0.0

        # Visit each city in 'order'
        for city in order:
            path_nodes = paths[cur][city]
            for u, v in zip(path_nodes, path_nodes[1:]):
                total += float(p.cost([u, v], carried))
            carried += float(gold[city])
            cur = city

        # Return to base
        back = paths[cur][0]
        for u, v in zip(back, back[1:]):
            total += float(p.cost([u, v], carried))
        return float(total)

    # Build a plan by repeatedly merging trips whenever it reduces cost.
    def candidate_merge_trips() -> List[Tuple[int, float]]:

        # Each route is a list of customer cities visited in order in ONE trip
        routes: Dict[int, List[int]] = {i: [c] for i, c in enumerate(customers)}

        # rcost[rid] = trip_cost(routes[rid])
        rcost: Dict[int, float] = {i: trip_cost(r) for i, r in routes.items()}

        # Merge two routes a and b by connecting endpoints.
        # The code tests 4 combinations.
        # and chooses the one with minimum trip_cost.
        def best_merge(a: List[int], b: List[int]) -> Tuple[float, List[int]]:
            cands = [a + b, a + b[::-1], a[::-1] + b, a[::-1] + b[::-1]]
            best_c = float("inf")
            best_o: List[int] = []
            for o in cands:
                c = trip_cost(o)
                if c < best_c:
                    best_c, best_o = c, o
            return best_c, best_o

        # Max-heap of (-saving, route_id_a, route_id_b)
        heap: List[Tuple[float, int, int]] = []
        ids = list(routes.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                merged_c, _ = best_merge(routes[a], routes[b])
                saving = rcost[a] + rcost[b] - merged_c
                if saving > 1e-9:
                    heapq.heappush(heap, (-saving, a, b))

        next_id = max(routes.keys(), default=-1) + 1

        # Greedily apply best savings
        while heap:
            _, a, b = heapq.heappop(heap)
             # If either route got merged already, skip
            if a not in routes or b not in routes or a == b:
                continue
            merged_c, best_o = best_merge(routes[a], routes[b])
            saving = rcost[a] + rcost[b] - merged_c
            if saving <= 1e-9:
                continue

            # Create a new merged route
            new_id = next_id
            next_id += 1
            routes[new_id] = best_o
            rcost[new_id] = merged_c

            # Delete old routes
            del routes[a], routes[b]
            del rcost[a], rcost[b]

            # Evaluate merging the new route with every other remaining route
            for other in list(routes.keys()):
                if other == new_id:
                    continue
                mc, _ = best_merge(routes[new_id], routes[other])
                s2 = rcost[new_id] + rcost[other] - mc
                if s2 > 1e-9:
                    heapq.heappush(heap, (-s2, new_id, other))

        # Decode final routes into action list
        rem = gold.copy()
        actions: List[Tuple[int, float]] = []
        for r in routes.values():
            cur = 0
            for c in r:
                take = float(rem[c]) # pick everything remaining at c
                rem[c] = 0.0
                actions += expand_path(paths[cur][c], pickup_at_end=take)
                cur = c
            # Return to base after finishing the route
            actions += expand_path(paths[cur][0], pickup_at_end=0.0)

        # Ensure plan ends with (0,0)
        if not actions:
            return [(0, 0.0)]
        if actions[-1][0] != 0:
            actions.append((0, 0.0))
        else:
            actions[-1] = (0, 0.0)
        return actions

    # -------------------------
    # Candidate B: Split-load (partial pickups), capacity-based
    # -------------------------
    """
    Idea:
    - When beta is high, carrying large loads is expensive.
    - Do repeated trips, each collecting at most 'cap' gold total.
    - Within each trip, greedily choose next city that gives best
      (distance_to_city + distance_back_to_base) per unit gold taken.
    """

    def cap_candidates() -> List[float]:
        """
        Create a small set of plausible caps to try (portfolio).
        Heuristics depend on:
        - alpha (stronger penalty -> smaller cap)
        - median gold size (to avoid caps incredibly larger than typical city gold)
        - beta: if near 1, try fewer caps; else try more.
        """
        g = gold[customers]
        med = float(np.median(g)) if len(g) else 50.0
        base = max(15.0, min(250.0, 80.0 / max(alpha, 1e-6)))
        base = min(base, max(30.0, med))
        cands = sorted({float(max(10.0, c)) for c in (base / 2, base, base * 2, base * 3)})
        return cands[:2] if beta <= 1.05 else cands[:4]

    # Build a plan using a capacity cap (max gold per trip).
    def candidate_split(cap: float) -> List[Tuple[int, float]]:
        rem = {c: float(gold[c]) for c in customers}
        active = {c for c in customers if rem[c] > EPS}
        actions: List[Tuple[int, float]] = []

        while active:
            cur = 0
            load = 0.0
            trip: List[Tuple[int, float]] = []

            # Fill this trip up to cap
            while load + 1e-6 < cap and active:
                best_city = None
                best_take = 0.0
                best_score = float("inf")

                # Evaluate every active city as next pickup
                for c in active:
                    take = min(rem[c], cap - load)
                    if take <= EPS:
                        continue
                    score = (lengths[cur].get(c, float("inf")) + lengths[c].get(0, float("inf"))) / take
                    if score < best_score:
                        best_score = score
                        best_city = c
                        best_take = float(take)

                if best_city is None:
                    break

                # Commit the best choice
                trip.append((int(best_city), best_take))
                rem[best_city] -= best_take
                load += best_take
                cur = int(best_city)
                if rem[best_city] <= EPS:
                    active.remove(best_city)

            # Decode this trip into step-by-step actions
            cur = 0
            for c, take in trip:
                actions += expand_path(paths[cur][c], pickup_at_end=take)
                cur = c
            actions += expand_path(paths[cur][0], pickup_at_end=0.0)

        # Ensure plan ends with (0,0)
        if not actions:
            return [(0, 0.0)]
        if actions[-1][0] != 0:
            actions.append((0, 0.0))
        else:
            actions[-1] = (0, 0.0)
        return actions


    # Portfolio selection: generate candidate plans and pick the cheapest
    candidates: List[List[Tuple[int, float]]] = [
        candidate_merge_trips(),
    ]

    # Only try split-load if beta suggests carrying is sufficiently penalized
    if beta > 0.85:
        for cap in cap_candidates():
            candidates.append(candidate_split(cap))

    # Pick the best by exact simulation + validity checks
    best_plan = candidates[0]
    best_c = float("inf")
    for plan in candidates:
        c = plan_cost(plan)
        if c < best_c:
            best_c, best_plan = c, plan

    # Ensure last is (0,0)
    if best_plan[-1][0] != 0:
        best_plan.append((0, 0.0))
    else:
        best_plan[-1] = (0, 0.0)

    return best_plan