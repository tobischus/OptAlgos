import time
from problem.instance_generator import generate_instances
from problem.rectangle_packing_problem import RectanglePackingProblem
from algorithms.greedy import greedy
from algorithms.local_search import local_search
from strategies.guillotine_strategy import StrategyGuillotine
from strategies.bottomleft_strategy import StrategyBottomLeft
from neighbors.geometry_based_neighbor import GeometryBasedNeighbor
from neighbors.rule_based_neighbor import RuleBasedNeighbor
from neighbors.overlapping_neighbor import OverlappingNeighbor

def run_tests(test_cases):
    """
    test_cases: Liste von Tupeln (count, num_rect, min_side1, max_side1, min_side2, max_side2, L).
    Für jedes Tupel werden Instanzen generiert und anschließend
    - Greedy (Guillotine und BottomLeft)
    - LocalSearch (verschiedene Nachbarschaften)
    angewendet.
    """
    results = []
    for (count, nr, mn1, mx1, mn2, mx2, L) in test_cases:
        instances = generate_instances(count, nr, mn1, mx1, mn2, mx2, L)
        for inst_idx, rects in enumerate(instances):
            problem = RectanglePackingProblem(L, rects)

            # GREEDY: Nur Guillotine und BottomLeft testen
            greedy_strats = [
                ("Guillotine", StrategyGuillotine(sort_by="area-desc")),
                ("BottomLeft", StrategyBottomLeft())
            ]
            for (sname, s) in greedy_strats:
                start_time = time.process_time()
                sol = greedy(problem, s)
                end_time = time.process_time()
                val = problem.evaluate_solution(sol)
                results.append(("Greedy", sname, nr, L, val, end_time-start_time))

            # Lokale Suche wie bisher
            neighs = [
                ("Geometry", GeometryBasedNeighbor(max_shift=5, neighbor_count=5)),
                ("Rule", RuleBasedNeighbor(swaps_per_call=5)),
                ("Overlap", OverlappingNeighbor(initial_overlap_ratio=100, decrement=10))
            ]
            bad_sol = problem.create_empty_solution()
            for r in rects:
                bad_sol.boxes.append([(r, (0,0), False)])
            for (nname, nobj) in neighs:
                start_time = time.process_time()
                best_sol = local_search(problem, bad_sol, nobj, max_iter=100)
                end_time = time.process_time()
                val = problem.evaluate_solution(best_sol)
                results.append(("LocalSearch", nname, nr, L, val, end_time-start_time))

    # Ausgabe
    print("Alg;Variante;RectCount;L;ObjVal;Time")
    for r in results:
        print(";".join(map(str, r)))
    
def main():
    test_cases = [
        (3, 50, 1, 20, 1, 20, 50),
        (3, 100, 1, 25, 1, 25, 50)
    ]
    run_tests(test_cases)

if __name__ == "__main__":
    main()
