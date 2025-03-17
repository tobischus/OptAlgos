def local_search(problem, current_solution, neighbor_generator, max_iter=1000, max_time=10.0, partial_sample_size=5, snapshot_callback=None):
    """
    Generischer lokaler Suchalgorithmus:
    - Beginnt mit einer (schlechten) Startlösung
    - Erzeugt Nachbarn mit neighbor_generator
    - Wählt den besten Nachbarn und wiederholt
    """
    import time
    
    best_solution = current_solution
    best_value = problem.evaluate_solution(best_solution)
    
    start_time = time.time()
    elapsed_time = 0
    iter_count = 0
    
    # FIRST IMPROVEMENT Strategie
    # Speichere den aktuellen besten Wert
    while iter_count < max_iter and elapsed_time < max_time:
        # Optional: Nur einen Teil der möglichen Nachbarn durchsuchen
        if partial_sample_size > 0:
            neighbors = neighbor_generator.get_neighbors_subset(problem, best_solution, partial_sample_size)
        else:
            neighbors = neighbor_generator.get_neighbors(problem, best_solution)
        
        # Wenn keine Nachbarn gefunden wurden, breche ab
        if not neighbors:
            break
            
        # Finde den besten Nachbarn
        best_neighbor = None
        best_neighbor_value = float('inf')
        
        for neighbor in neighbors:
            neighbor_value = problem.evaluate_solution(neighbor)
            if neighbor_value < best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = neighbor_value
        
        # Wenn der beste Nachbar besser ist als die aktuelle Lösung, aktualisiere
        if best_neighbor_value < best_value:
            best_solution = best_neighbor
            best_value = best_neighbor_value
            
            # Optional: Snapshot für die Visualisierung speichern
            elapsed_time = time.time() - start_time
            if snapshot_callback:
                snapshot_callback(best_solution, iter_count, best_value, elapsed_time)
        else:
            # Kein besserer Nachbar gefunden, Lokales Optimum erreicht
            break
            
        iter_count += 1
        elapsed_time = time.time() - start_time
    
    return best_solution