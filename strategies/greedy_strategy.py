class StrategyLargestAreaFirst:
    """
    Sortiere Rechtecke nach absteigender Fläche, platziere sie dann shelf-basiert.
    """
    def get_ordered_rectangles(self, rectangles):
        return sorted(rectangles, key=lambda r: r.width*r.height, reverse=True)

    def place_rectangle_in_solution(self, rect, solution, problem):
        return problem.place_rectangle_shelf(rect, solution)


class StrategyMaxSideFirst:
    """
    Sortiere Rechtecke nach ihrer maximalen Seitenlänge absteigend.
    """
    def get_ordered_rectangles(self, rectangles):
        return sorted(rectangles, key=lambda r: max(r.width, r.height), reverse=True)
    
    def place_rectangle_in_solution(self, rect, solution, problem):
        return problem.place_rectangle_shelf(rect, solution)
