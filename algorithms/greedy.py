def greedy(problem, strategy):
    """
    Generischer Greedy-Algorithmus:
    - Sortiere die Elemente (Rechtecke) gem. strategy.get_ordered_rectangles.
    - Platziere nacheinander jedes Rechteck in der (Teil-)Lösung, z.B. per
      strategy.place_rectangle_in_solution(...).
    """
    sorted_rects = strategy.get_ordered_rectangles(problem.rectangles)
    solution = problem.create_empty_solution()
    for rect in sorted_rects:
        solution = strategy.place_rectangle_in_solution(rect, solution, problem)
    return solution
