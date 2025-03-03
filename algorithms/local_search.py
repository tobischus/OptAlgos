import time
from copy import deepcopy

def local_search(problem, current_solution, neighbor_generator,
                 max_iter=100, max_time=10.0, partial_sample_size=5,
                 snapshot_callback=None):
    """
    Verbesserte Lokale Suche (First-Improve) mit:
    - Zeitgrenze (max_time)
    - max_iter
    - partial_sample_size (Sampling in get_neighbors_subset())
    - snapshot_callback für GUI (optional).
    """
    start_time = time.time()
    best_solution = deepcopy(current_solution)
    best_value = problem.evaluate_solution(best_solution)

    iteration = 0

    while iteration < max_iter:
        elapsed = time.time() - start_time
        if elapsed > max_time:
            break  # Zeitlimit

        # Erzeuge nur für eine Teilmenge der Rechtecke Nachbarn:
        neighbors = neighbor_generator.get_neighbors_subset(problem, best_solution, partial_sample_size)

        improved = False
        for neigh_sol in neighbors:
            val = problem.evaluate_solution(neigh_sol)
            if val < best_value:
                best_solution = neigh_sol
                best_value = val
                improved = True
                iteration += 1
                if snapshot_callback:
                    snapshot_callback(best_solution, iteration, best_value, elapsed)
                break  # First-Improve

        if not improved:
            # keine Verbesserung in dieser Iteration
            iteration += 1

    return best_solution
