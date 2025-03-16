# strategies/greedy_strategy.py

class StrategyLargestAreaFirst:
    """
    Sortiere Rechtecke nach absteigender Fläche, lege sie dann
    per (einfacher) Shelf-Logik ab.
    """
    def get_ordered_rectangles(self, rectangles):
        return sorted(rectangles, key=lambda r: r.width*r.height, reverse=True)

    def place_rectangle_in_solution(self, rect, solution, problem):
        return problem.place_rectangle_shelf(rect, solution)


class StrategyMaxSideFirst:
    """
    Sortiere Rechtecke nach ihrer maximalen Seitenlänge absteigend,
    lege sie dann per (einfacher) Shelf-Logik ab.
    """
    def get_ordered_rectangles(self, rectangles):
        return sorted(rectangles, key=lambda r: max(r.width, r.height), reverse=True)
    
    def place_rectangle_in_solution(self, rect, solution, problem):
        return problem.place_rectangle_shelf(rect, solution)


class StrategyBestFitShelf:
    """
    Erweiterte Shelf-Strategie mit 'Best-Fit' pro Box:
    - Sortierung nach absteigender Fläche (Beispiel, du könntest auch andere Kriterien wählen).
    - Beim Platzieren eines Rechtecks:
        * Iteriere über alle Boxen und über alle 'Shelves' (Zeilen) in dieser Box,
          prüfe normale und rotierte Ausrichtung.
        * Wähle die Shelf-Position, bei der die Breite am knappsten, aber noch passend, ist
          (oder ggf. den minimalen "verschenkten" Platz).
        * Wenn es in keiner bestehenden Box passt, eröffne eine neue Box.
    """

    def get_ordered_rectangles(self, rectangles):
        # Beispiel: absteigende Fläche
        return sorted(rectangles, key=lambda r: r.width*r.height, reverse=True)

    def place_rectangle_in_solution(self, rect, solution, problem):
        # Suche die "beste" Position in allen existierenden Boxen
        best_box_idx = None
        best_coords = None
        best_rot = False
        best_leftover = None  # hier messen wir, wieviel Platz in der Shelf-Breite übrig bliebe

        for b_idx, box_content in enumerate(solution.boxes):
            # Bilde Shelves
            shelves = self._build_shelves(box_content, problem.L)
            for (start_y, shelf_height, current_width) in shelves:
                # Prüfe, ob rect normal passt
                w_normal, h_normal = rect.width, rect.height
                leftover_normal = problem.L - (current_width + w_normal)
                if leftover_normal >= 0 and (start_y + max(h_normal, shelf_height) <= problem.L):
                    # Passt normal
                    # je kleiner leftover_normal, desto besser "Fit"
                    if best_leftover is None or leftover_normal < best_leftover:
                        best_leftover = leftover_normal
                        best_box_idx = b_idx
                        best_coords = (current_width, start_y)
                        best_rot = False

                # Prüfe, ob rect rotiert passt
                w_rot, h_rot = rect.height, rect.width
                leftover_rot = problem.L - (current_width + w_rot)
                if leftover_rot >= 0 and (start_y + max(h_rot, shelf_height) <= problem.L):
                    # Passt rotiert
                    if best_leftover is None or leftover_rot < best_leftover:
                        best_leftover = leftover_rot
                        best_box_idx = b_idx
                        best_coords = (current_width, start_y)
                        best_rot = True

        if best_box_idx is not None and best_coords is not None:
            # Füge das Rechteck in der "besten" Box ein
            solution.boxes[best_box_idx].append((rect, best_coords, best_rot))
            return solution
        else:
            # Wenn es nirgends passt, neue Box
            new_box = []
            solution.boxes.append(new_box)
            # Neue Box: Koordinaten (0,0), ggf. rotieren falls nötig
            if rect.width <= problem.L and rect.height <= problem.L:
                new_box.append((rect, (0,0), False))
            elif rect.height <= problem.L and rect.width <= problem.L:
                new_box.append((rect, (0,0), True))
            else:
                # Sollte laut Aufgabe nicht passieren, da L >= max Seitenlänge
                pass
            return solution

    def _build_shelves(self, box_content, L):
        """
        Baut eine Liste von (start_y, shelf_height, current_width) pro "Shelf" in dieser Box.
        Die Logik ist ähnlich wie in place_rectangle_shelf, nur dass wir
        sie als Datenstruktur aufbereiten, um den best-fit zu ermitteln.
        """
        if not box_content:
            # Noch leer -> "Shelf" beginnt bei y=0, Höhe=0, aktuelle Breite=0
            return [(0, 0, 0)]

        # Sortiere nach Zeilenanfang y
        placed = sorted(box_content, key=lambda x: x[1][1])

        shelves = []
        cy = None
        ch = 0
        cw = 0

        for (r,(rx,ry),rot) in placed:
            w = r.width if not rot else r.height
            h = r.height if not rot else r.width
            if cy is None:
                cy = ry
                ch = h
                cw = w
            else:
                # Gleicher Shelf (selbes y)
                if abs(ry - cy) < 1e-9:
                    cw += w
                    ch = max(ch, h)
                else:
                    # Neuer Shelf
                    shelves.append((cy, ch, cw))
                    cy = ry
                    ch = h
                    cw = w
        # Letzten Shelf anhängen
        if cy is not None:
            shelves.append((cy, ch, cw))

        # shelves ist jetzt Liste von (start_y, shelf_height, current_width)
        return shelves
