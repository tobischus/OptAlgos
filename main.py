import random
from algorithms.local_search import local_search
from algorithms.greedy import greedy
from neighbors.geometry_based_neighbor import GeometryBasedNeighbor
from neighbors.rule_based_neighbor import RuleBasedNeighbor
from neighbors.overlapping_neighbor import OverlappingNeighbor
from strategies.greedy_strategy import StrategyLargestAreaFirst, StrategyMaxSideFirst
from problem.rectangle_packing_problem import RectanglePackingProblem, RectangleSolution
from problem.instance_generator import generate_instances
from gui.gui import PackingGUI

def main():
    random.seed(42)

    # Kleines Beispiel zum Direktstart in der Konsole
    L = 20
    num_rectangles = 15
    min_side1, max_side1 = 1, 9
    min_side2, max_side2 = 1, 9

    # Erzeuge 1 Instanz
    rects = generate_instances(
        count=1,
        num_rectangles=num_rectangles,
        min_side1=min_side1,
        max_side1=max_side1,
        min_side2=min_side2,
        max_side2=max_side2,
        L=L
    )[0]

    problem = RectanglePackingProblem(L, rects)

    print("Starte GREEDY tests:")
    # Greedy
    strat1 = StrategyLargestAreaFirst()
    sol_g1 = greedy(problem, strat1)
    val_g1 = problem.evaluate_solution(sol_g1)
    print(f"Greedy(LargestArea): {len(sol_g1.boxes)} Boxen, Zielfunktion={val_g1}")

    strat2 = StrategyMaxSideFirst()
    sol_g2 = greedy(problem, strat2)
    val_g2 = problem.evaluate_solution(sol_g2)
    print(f"Greedy(MaxSide): {len(sol_g2.boxes)} Boxen, Zielfunktion={val_g2}")

    print("Starte LOKALE SUCHE tests:")
    # Schlechte Startlösung
    bad_start = RectangleSolution()
    for r in rects:
        bad_start.boxes.append([(r,(0,0),False)])

    # Geometry
    geom = GeometryBasedNeighbor(max_shift=5, neighbor_count=5)
    best_sol_geom = local_search(
        problem=problem,
        current_solution=bad_start,
        neighbor_generator=geom,
        max_iter=1000,
        max_time=5.0,
        partial_sample_size=5
    )
    val_geom = problem.evaluate_solution(best_sol_geom)
    print(f"LocalSearch(Geometry): {len(best_sol_geom.boxes)} Boxen, val={val_geom}")

    # Rule
    rule = RuleBasedNeighbor(swaps_per_call=5)
    best_sol_rule = local_search(
        problem=problem,
        current_solution=bad_start,
        neighbor_generator=rule,
        max_iter=1000,
        max_time=5.0,
        partial_sample_size=5
    )
    val_rule = problem.evaluate_solution(best_sol_rule)
    print(f"LocalSearch(Rule): {len(best_sol_rule.boxes)} Boxen, val={val_rule}")

    # Overlap
    overlap = OverlappingNeighbor(initial_overlap_ratio=100, decrement=10, neighbor_count=5)
    best_sol_overlap = local_search(
        problem=problem,
        current_solution=bad_start,
        neighbor_generator=overlap,
        max_iter=1000,
        max_time=5.0,
        partial_sample_size=5
    )
    val_overlap = problem.evaluate_solution(best_sol_overlap)
    print(f"LocalSearch(Overlap): {len(best_sol_overlap.boxes)} Boxen, val={val_overlap}")

    # Starte GUI
    gui = PackingGUI()
    gui.run()

if __name__ == "__main__":
    main()
