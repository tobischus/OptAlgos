# strategies/guillotine_strategy.py

import math

class StrategyGuillotine:
    """
    Guillotine-Verfahren, das "free_rects" nicht an der Box-Liste selbst,
    sondern in solution.guillotine_data[box_idx] verwaltet.
    """

    def __init__(self, sort_by="area-desc"):
        self.sort_by = sort_by

    def get_ordered_rectangles(self, rectangles):
        if self.sort_by == "area-desc":
            return sorted(rectangles, key=lambda r: r.width*r.height, reverse=True)
        elif self.sort_by == "maxside-desc":
            return sorted(rectangles, key=lambda r: max(r.width, r.height), reverse=True)
        else:
            return rectangles

    def place_rectangle_in_solution(self, rect, solution, problem):
        """
        Sucht einen freien Bereich in einer vorhandenen Box, in den rect (ggf. rotiert) passt.
        Falls keiner passt, wird eine neue Box angelegt.
        """
        # Falls wir dieses Dictionary noch nicht angelegt haben, erstellen wir es:
        if not hasattr(solution, 'guillotine_data'):
            solution.guillotine_data = {}  # dict: box_idx -> list of (x, y, w, h)

        import math
        best_box_idx = None
        best_free_idx = None
        best_rotated = False
        best_score = math.inf  # minimal leftover area

        # 1) Über alle existierenden Boxen iterieren
        for b_idx, box_content in enumerate(solution.boxes):
            # Falls wir für diese Box noch keine free_rects haben, anlegen
            if b_idx not in solution.guillotine_data:
                solution.guillotine_data[b_idx] = [(0, 0, problem.L, problem.L)]

            free_rects = solution.guillotine_data[b_idx]
            # Jede freie Fläche durchgehen
            for f_idx, (fx, fy, fw, fh) in enumerate(free_rects):
                # Prüfe normal
                if rect.width <= fw and rect.height <= fh:
                    leftover = (fw*fh) - (rect.width*rect.height)
                    if leftover < best_score:
                        best_score = leftover
                        best_box_idx = b_idx
                        best_free_idx = f_idx
                        best_rotated = False
                # Prüfe rotiert
                if rect.height <= fw and rect.width <= fh:
                    leftover = (fw*fh) - (rect.width*rect.height)
                    if leftover < best_score:
                        best_score = leftover
                        best_box_idx = b_idx
                        best_free_idx = f_idx
                        best_rotated = True

        # 2) Wenn wir eine passende Box gefunden haben:
        if best_box_idx is not None:
            free_rects = solution.guillotine_data[best_box_idx]
            (fx, fy, fw, fh) = free_rects[best_free_idx]

            if best_rotated:
                w_used, h_used = rect.height, rect.width
            else:
                w_used, h_used = rect.width, rect.height

            # Füge in die Box (rect, (fx, fy), best_rotated)
            solution.boxes[best_box_idx].append((rect, (fx, fy), best_rotated))

            # Guillotine-Schnitt
            del free_rects[best_free_idx]
            remainder_w = fw - w_used
            remainder_h = fh - h_used

            # Reste anlegen
            # Rechts vom platzierten Rechteck
            if remainder_w > 0:
                free_rects.append((fx + w_used, fy, remainder_w, fh))
            # Oberhalb des platzierten Rechtecks
            if remainder_h > 0:
                free_rects.append((fx, fy + h_used, w_used, remainder_h))

            self._cleanup_free_rects(free_rects)
            return solution

        else:
            # 3) Falls in keiner Box Platz war -> Neue Box
            new_box_idx = len(solution.boxes)
            # Platziere zunächst eine leere Liste der Rechtecke
            solution.boxes.append([])

            # und lege den freien Bereich (0,0,L,L) an
            if not hasattr(solution, 'guillotine_data'):
                solution.guillotine_data = {}
            solution.guillotine_data[new_box_idx] = [(0, 0, problem.L, problem.L)]

            # Rekursiver Aufruf, jetzt passt es sicher in die neue Box
            return self.place_rectangle_in_solution(rect, solution, problem)

    def _cleanup_free_rects(self, free_rects):
        # Hier kannst du optional doppelte oder überlappende Freiräume entfernen/mergen
        unique = []
        for fr in free_rects:
            if fr not in unique:
                unique.append(fr)
        free_rects[:] = unique