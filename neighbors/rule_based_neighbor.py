from copy import deepcopy
import random

class RuleBasedNeighbor:
    """
    Regelbasierte Nachbarschaft mit Permutationsänderungen.
    Auch hier: wir implementieren get_neighbors() und get_neighbors_subset().
    Die Shelf-Platzierung passiert, indem wir alle Rechtecke in Reihenfolge packen.
    """

    def __init__(self, swaps_per_call=5):
        self.swaps_per_call = swaps_per_call

    def get_neighbors(self, problem, solution):
        return self._create_neighbors(problem, solution, all_rects=True, sample_size=0)

    def get_neighbors_subset(self, problem, solution, sample_size):
        return self._create_neighbors(problem, solution, all_rects=False, sample_size=sample_size)

    def _create_neighbors(self, problem, solution, all_rects, sample_size):
        neighbors = []
        rect_list = []
        for box in solution.boxes:
            for (r,_,_) in box:
                rect_list.append(r)
        n = len(rect_list)
        if n<2:
            return neighbors

        # Um partial sampling zu simulieren, können wir sample_size swaps generieren.
        # all_rects ignorieren wir hier, weil "regelbasiert" = wir behandeln immer
        # die gesamte Permutation. Aber wir limitieren die Anzahl an generierten Permutationen
        total_swaps = self.swaps_per_call
        if not all_rects:
            total_swaps = sample_size

        for _ in range(total_swaps):
            new_order = rect_list[:]
            if random.random()<0.5:
                i,j = random.sample(range(n),2)
                new_order[i], new_order[j] = new_order[j], new_order[i]
            else:
                i = random.randrange(n)
                j = random.randrange(n)
                if i!=j:
                    rtemp = new_order.pop(i)
                    new_order.insert(j, rtemp)

            new_sol = problem.create_empty_solution()
            for r in new_order:
                problem.place_rectangle_shelf(r, new_sol)
            neighbors.append(new_sol)

        return neighbors
