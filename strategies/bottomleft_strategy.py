
class StrategyBottomLeft:
    """
    Bottom-Left-Fill Greedy-Strategie:
    
    - Die Rechtecke werden zuerst (zum Beispiel absteigend nach Fläche) sortiert.
    - Für jedes Rechteck wird in jeder existierenden Box nach Kandidatenpositionen gesucht:
      Neben (0,0) werden alle Positionen in Betracht gezogen, die sich aus den rechten oder oberen
      Rändern bereits platzierter Rechtecke ergeben.
    - Es wird die Position gewählt, die als erstes (d.h. mit minimalem y und bei Gleichstand minimalem x)
      gefunden wird, an der das Rechteck ohne Überlappung und innerhalb der Box (Dimension L) passt.
    - Kann das Rechteck in keiner bestehenden Box platziert werden, wird eine neue Box eröffnet.
    
    Diese Methode ist grundlegend anders als der Guillotine-Ansatz und arbeitet ausschließlich
    nach dem Prinzip der lokal bestmöglichen Platzierung.
    """
    def get_ordered_rectangles(self, rectangles):
        # Sortierung absteigend nach Fläche (du kannst auch andere Kriterien wählen)
        return sorted(rectangles, key=lambda r: r.width * r.height, reverse=True)
    
    def place_rectangle_in_solution(self, rect, solution, problem):
        # Versuche in allen existierenden Boxen das Rechteck zu platzieren
        for box in solution.boxes:
            pos, rotated = self._find_position_for_rect(rect, box, problem.L)
            if pos is not None:
                box.append((rect, pos, rotated))
                return solution
        # Falls in keiner Box Platz ist: Neue Box anlegen
        new_box = []
        new_box.append((rect, (0, 0), False))  # Da r.width, r.height ≤ L ist, passt es immer
        solution.boxes.append(new_box)
        return solution
    
    def _find_position_for_rect(self, rect, box, L):
        """
        Sucht in einer Box mittels Bottom-Left-Fill-Strategie eine Platzierung.
        Ermittelt Kandidatenpositionen: (0,0) sowie (x+width, y) und (x, y+height)
        für jedes bereits platzierte Rechteck. Gibt die erste Position zurück, an der
        das Rechteck (ggf. rotiert) ohne Überlappung und innerhalb des LxL-Quadrats passt.
        """
        candidates = [(0, 0)]
        for (r, (rx, ry), rot) in box:
            w = r.width if not rot else r.height
            h = r.height if not rot else r.width
            candidates.append((rx + w, ry))
            candidates.append((rx, ry + h))
        # Duplikate entfernen
        candidates = list(set(candidates))
        # Sortiere Kandidaten: Zuerst nach y (kleinster y-Wert zuerst), dann nach x
        candidates.sort(key=lambda p: (p[1], p[0]))
        
        for (cx, cy) in candidates:
            if self._can_place(rect, (cx, cy), box, L, rotated=False):
                return (cx, cy), False
            if self._can_place(rect, (cx, cy), box, L, rotated=True):
                return (cx, cy), True
        return None, False  # Kein passender Platz gefunden
    
    def _can_place(self, rect, pos, box, L, rotated=False):
        """
        Prüft, ob das Rechteck in der angegebenen Position (pos) in der Box platziert werden kann.
        Berücksichtigt dabei die Box-Grenzen (Dimension L) und überprüft, ob es zu keiner Überlappung kommt.
        """
        cx, cy = pos
        w = rect.width if not rotated else rect.height
        h = rect.height if not rotated else rect.width
        # Prüfe, ob Rechteck in die Box passt
        if cx + w > L or cy + h > L:
            return False
        # Prüfe auf Überlappungen mit bereits platzierten Rechtecken
        for (r, (rx, ry), rot) in box:
            rw = r.width if not rot else r.height
            rh = r.height if not rot else r.width
            if self._overlap(cx, cy, w, h, rx, ry, rw, rh):
                return False
        return True
    
    def _overlap(self, x1, y1, w1, h1, x2, y2, w2, h2):
        """
        Liefert True, wenn die beiden Rechtecke sich im Inneren überlappen.
        Es ist erlaubt, dass sie an den Rändern anstoßen (offen disjunkt).
        """
        # Überlappung existiert, wenn sich die inneren Bereiche schneiden:
        if x1 >= x2 + w2 or x2 >= x1 + w1:
            return False
        if y1 >= y2 + h2 or y2 >= y1 + h1:
            return False
        return True
