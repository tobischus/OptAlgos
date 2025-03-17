from copy import deepcopy
import random

class GeometryBasedNeighbor:
    """
    Verbesserte geometriebasierte Nachbarschaft:
      - Shift & Rotate einzelner Rechtecke
      - Bottom-Left-Boxwechsel
      - Auflösen fast leerer Boxen
      - Partielles Mergen zweier Boxen (Re-Packing via Bottom-Left)
    """

    def __init__(self, max_shift=5, neighbor_count=5, max_box_pairs=2):
        """
        :param max_shift: Max. Verschiebung bei SHIFT.
        :param neighbor_count: Wieviele SHIFT/ROTATE/BOXMOVE-Versuche pro Rechteck.
        :param max_box_pairs: Wieviele zufällige Box-Paare sollen pro Iteration gemerged werden?
        """
        self.max_shift = max_shift
        self.neighbor_count = neighbor_count
        self.max_box_pairs = max_box_pairs

    # --------------------------------------------------------------------------
    #   Schnittstelle nach außen
    # --------------------------------------------------------------------------

    def get_neighbors(self, problem, solution):
        # Erzeuge Nachbarn basierend auf ALLEN Rechtecken + extra Box-Merges
        nbrs = self._create_neighbors(problem, solution, all_rects=True, sample_size=0)
        return nbrs

    def get_neighbors_subset(self, problem, solution, sample_size):
        # Erzeuge Nachbarn nur für sample_size Rechtecke + extra Box-Merges
        nbrs = self._create_neighbors(problem, solution, all_rects=False, sample_size=sample_size)
        return nbrs

    # --------------------------------------------------------------------------
    #   Kernmethode
    # --------------------------------------------------------------------------

    def _create_neighbors(self, problem, solution, all_rects, sample_size):
        neighbors = []
        if not solution.boxes:
            return neighbors

        # 1) SHIFT/ROTATE/BOXMOVE einzelner Rechtecke
        neighbors += self._rect_based_moves(problem, solution, all_rects, sample_size)

        # 2) Auflösen fast leerer Boxen
        neighbors += self._try_merge_small_boxes(problem, solution)

        # 3) Box-Paar-Merging (reduziert die Boxenanzahl oft stark!)
        neighbors += self._try_merge_box_pairs(problem, solution)

        return neighbors

    # --------------------------------------------------------------------------
    #   1) SHIFT/ROTATE/BOXMOVE einzelner Rechtecke
    # --------------------------------------------------------------------------

    def _rect_based_moves(self, problem, solution, all_rects, sample_size):
        neighbors = []
        all_items = []
        for b_idx, box_content in enumerate(solution.boxes):
            for r_idx, _ in enumerate(box_content):
                all_items.append((b_idx, r_idx))

        if not all_items:
            return neighbors

        # Falls sample_size > 0, wähle Zufallsmenge
        if all_rects:
            chosen_items = all_items
        else:
            sample_size = max(1, min(sample_size, len(all_items)))
            chosen_items = random.sample(all_items, sample_size)

        for (box_idx, rect_idx) in chosen_items:
            # Prüfen, ob Index noch gültig
            if box_idx >= len(solution.boxes) or rect_idx >= len(solution.boxes[box_idx]):
                continue

            rect, (x, y), rotated = solution.boxes[box_idx][rect_idx]

            # SHIFT
            for _ in range(self.neighbor_count):
                dx = random.randint(-self.max_shift, self.max_shift)
                dy = random.randint(-self.max_shift, self.max_shift)
                if dx == 0 and dy == 0:
                    continue

                new_sol = deepcopy(solution)
                w = rect.width if not rotated else rect.height
                h = rect.height if not rotated else rect.width

                new_x = max(0, min(problem.L - w, x + dx))
                new_y = max(0, min(problem.L - h, y + dy))

                new_sol.boxes[box_idx][rect_idx] = (rect, (new_x, new_y), rotated)

                if self._is_valid_position(problem, new_sol, box_idx, rect_idx):
                    neighbors.append(new_sol)

            # ROTATE
            new_rot = not rotated
            w = rect.width if not new_rot else rect.height
            h = rect.height if not new_rot else rect.width
            if x + w <= problem.L and y + h <= problem.L:
                new_sol = deepcopy(solution)
                new_sol.boxes[box_idx][rect_idx] = (rect, (x, y), new_rot)
                if self._is_valid_position(problem, new_sol, box_idx, rect_idx):
                    neighbors.append(new_sol)

            # BOXMOVE (mit Bottom-Left-Platzierung)
            if len(solution.boxes) > 1:
                for target_box_idx in range(len(solution.boxes)):
                    if target_box_idx == box_idx:
                        continue
                    new_sol = deepcopy(solution)
                    # Rechteck entfernen
                    del new_sol.boxes[box_idx][rect_idx]
                    # Versuchen, in target_box_idx per Bottom-Left einzufügen
                    if self._try_bottom_left_placement(problem, new_sol, target_box_idx, rect, consider_rotation=True):
                        # Box ggf. leeren -> löschen
                        new_sol.boxes = [b for b in new_sol.boxes if len(b) > 0]
                        neighbors.append(new_sol)

        return neighbors

    # --------------------------------------------------------------------------
    #   2) (Fast) leere Boxen komplett auflösen
    # --------------------------------------------------------------------------

    def _try_merge_small_boxes(self, problem, solution, threshold=3):
        """
        Versucht, Boxen mit <= threshold Rechtecken aufzulösen,
        indem man alle Rechtecke in andere Boxen einfügt (via Bottom-Left).
        Gelingt das, wird die Box gelöscht.
        """
        neighbors = []
        for b_idx, box_content in enumerate(solution.boxes):
            if len(box_content) <= threshold and len(solution.boxes) > 1:
                new_sol = deepcopy(solution)
                rects_to_move = new_sol.boxes[b_idx][:]
                new_sol.boxes[b_idx].clear()

                moved_all = True
                for (r, (ox, oy), rot) in rects_to_move:
                    placed = False
                    for tb_idx in range(len(new_sol.boxes)):
                        if tb_idx == b_idx:
                            continue
                        if self._try_bottom_left_placement(problem, new_sol, tb_idx, r, consider_rotation=True):
                            placed = True
                            break
                    # Falls nirgends Platz, neue Box
                    if not placed:
                        new_sol.boxes.append([])
                        nb_idx = len(new_sol.boxes) - 1
                        if not self._try_bottom_left_placement(problem, new_sol, nb_idx, r, consider_rotation=True):
                            moved_all = False
                            break
                if moved_all:
                    # Lösche leere Boxen
                    new_sol.boxes = [b for b in new_sol.boxes if len(b) > 0]
                    neighbors.append(new_sol)
        return neighbors

    # --------------------------------------------------------------------------
    #   3) Box-Paar-Merging
    # --------------------------------------------------------------------------

    def _try_merge_box_pairs(self, problem, solution):
        """
        Versucht, einige Paare von Boxen auszuwählen und deren Inhalt
        gemeinsam (neu) zu packen, um ggf. eine Box einzusparen.
        """
        neighbors = []
        box_count = len(solution.boxes)
        if box_count < 2:
            return neighbors

        # Falls wir sehr viele Boxen haben, wählen wir nur einige zufällige Paare aus
        pairs = []
        max_pairs = min(self.max_box_pairs, (box_count * (box_count - 1)) // 2)
        all_pairs = []
        for i in range(box_count):
            for j in range(i+1, box_count):
                all_pairs.append((i, j))

        # Ziehe zufällig max_pairs Paare
        random.shuffle(all_pairs)
        pairs = all_pairs[:max_pairs]

        for (i, j) in pairs:
            new_sol = self._merge_two_boxes(problem, solution, i, j)
            if new_sol is not None:
                neighbors.append(new_sol)

        return neighbors

    def _merge_two_boxes(self, problem, solution, box_idx1, box_idx2):
        """
        Nimmt die beiden Boxen box_idx1 und box_idx2, kombiniert alle Rechtecke,
        versucht sie in EINE Box (via Bottom-Left) zu packen. Gelingt das nicht,
        wird versucht, sie so kompakt wie möglich in ZWEI Boxen zu verteilen.
        Gibt ggf. eine neue Solution zurück oder None, falls keine Verbesserung.
        """
        if box_idx1 >= len(solution.boxes) or box_idx2 >= len(solution.boxes):
            return None

        # Falls dieselbe Box doppelt ausgewählt wurde (durch random Fehler), abbrechen
        if box_idx1 == box_idx2:
            return None

        # Kopie der Lösung
        new_sol = deepcopy(solution)

        # Sortiere Indizes absteigend, damit wir beim Entfernen keinen Indexshift kriegen
        if box_idx1 < box_idx2:
            i1, i2 = box_idx2, box_idx1
        else:
            i1, i2 = box_idx1, box_idx2

        # Hole alle Rechtecke aus den beiden Boxen
        boxA = new_sol.boxes[i1]
        boxB = new_sol.boxes[i2]
        combined_rects = []
        for (r, _, _) in boxA:
            combined_rects.append(r)
        for (r, _, _) in boxB:
            combined_rects.append(r)

        # Entferne die beiden Boxen aus new_sol
        del new_sol.boxes[i1]
        del new_sol.boxes[i2]

        # --- 1) Versuche, alle combined_rects in EINE Box zu packen (Bottom-Left-Greedy) ---
        one_box = []
        if self._try_pack_all_in_one_box(problem, combined_rects, one_box):
            # Hat geklappt -> wir haben 1 neue Box
            new_sol.boxes.append(one_box)
        else:
            # --- 2) Packe die combined_rects so kompakt wie möglich in 2 Boxen ---
            # Einfache Variante: Sortiere die Rects absteigend nach Fläche und packe
            # nacheinander. Wenn sie nicht in Box1 passen, versuche Box2, ansonsten erstelle Box2.
            # (Man kann hier auch ein ausgefeilteres 2-Box-Packing machen, z.B. "erst
            #  versuchen in Box1 so viel wie möglich, Rest in Box2" etc.)
            box1 = []
            box2 = []
            for r in sorted(combined_rects, key=lambda rr: rr.width*rr.height, reverse=True):
                if not self._try_bottom_left_placement(problem, new_sol, None, r, consider_rotation=True, custom_box=box1):
                    # Falls in box1 nicht passt, versuche box2
                    if not self._try_bottom_left_placement(problem, new_sol, None, r, consider_rotation=True, custom_box=box2):
                        # Falls auch in box2 nicht passt, wir brauchen 3. Box => Abbruch
                        return None
            # Box1 & Box2 an new_sol anhängen
            if box1:
                new_sol.boxes.append(box1)
            if box2:
                new_sol.boxes.append(box2)

        # Fertig. Wir geben new_sol zurück, *wenn* sich dadurch überhaupt was ändern kann.
        # (Man könnte hier noch checken, ob new_sol wirklich weniger Boxen hat, oder
        #  ob die Overlaps / Strafen besser sind.)
        return new_sol

    def _try_pack_all_in_one_box(self, problem, rects, target_box):
        """
        Versucht, alle rects in EINER Box (Dimension LxL) per Bottom-Left-Greedy zu platzieren.
        target_box ist eine Liste von (rect, (x,y), rotated).
        Gibt True zurück, wenn alles reinpasst, sonst False.
        """
        # Sortiere absteigend nach Fläche
        sorted_rects = sorted(rects, key=lambda r: r.width*r.height, reverse=True)
        for r in sorted_rects:
            if not self._try_bottom_left_placement_single(r, target_box, problem.L):
                return False
        return True

    def _try_bottom_left_placement_single(self, rect, box, L):
        """
        Versucht, rect per Bottom-Left in 'box' zu platzieren.
        Gibt True/False zurück.
        box ist eine Liste (rect, (x,y), rotated).
        """
        candidates = [(0, 0)]
        for (r2, (rx, ry), rot2) in box:
            rw = r2.width if not rot2 else r2.height
            rh = r2.height if not rot2 else r2.width
            candidates.append((rx+rw, ry))
            candidates.append((rx, ry+rh))
        # Sortieren
        candidates = list(set(candidates))
        candidates.sort(key=lambda c: (c[1], c[0]))

        # Zwei Orientierungen
        for (rot_flag, w, h) in [(False, rect.width, rect.height),
                                 (True, rect.height, rect.width)]:
            for (cx, cy) in candidates:
                if cx + w <= L and cy + h <= L:
                    # Overlap-Check
                    if not self._overlaps_any(cx, cy, w, h, box):
                        box.append((rect, (cx, cy), rot_flag))
                        return True
        return False

    # --------------------------------------------------------------------------
    #   Hilfsfunktionen (Bottom-Left-Platzierung, Overlap-Check etc.)
    # --------------------------------------------------------------------------

    def _try_bottom_left_placement(self, problem, solution, box_idx, rect,
                                   consider_rotation=False, custom_box=None):
        """
        Platziert 'rect' in solution.boxes[box_idx] (oder in custom_box, wenn angegeben)
        via Bottom-Left. Gibt True zurück, wenn erfolgreich, sonst False.
        Wenn consider_rotation=True, wird auch gedreht versucht.
        """
        if custom_box is not None:
            # Platzierung in gegebener Box-Liste (z.B. beim 2-Box-Merge)
            return self._try_bottom_left_placement_single_extended(rect, custom_box, problem.L, consider_rotation)
        else:
            # Platzierung in solution.boxes[box_idx]
            if box_idx is None or box_idx >= len(solution.boxes):
                return False
            return self._try_bottom_left_placement_single_extended(rect, solution.boxes[box_idx], problem.L, consider_rotation)

    def _try_bottom_left_placement_single_extended(self, rect, box_list, L, consider_rotation):
        """
        Erweiterte Variante, testet ggf. Rotation.
        """
        candidates = [(0, 0)]
        for (r2, (rx, ry), rot2) in box_list:
            rw = r2.width if not rot2 else r2.height
            rh = r2.height if not rot2 else r2.width
            candidates.append((rx + rw, ry))
            candidates.append((rx, ry + rh))
        candidates = list(set(candidates))
        candidates.sort(key=lambda c: (c[1], c[0]))

        # Mögliche Orientierungen
        orientations = [(False, rect.width, rect.height)]
        if consider_rotation:
            orientations.append((True, rect.height, rect.width))

        for (rot_flag, w, h) in orientations:
            for (cx, cy) in candidates:
                if cx + w <= L and cy + h <= L:
                    if not self._overlaps_any(cx, cy, w, h, box_list):
                        box_list.append((rect, (cx, cy), rot_flag))
                        return True
        return False

    def _overlaps_any(self, x, y, w, h, box_list):
        """Prüft, ob (x,y,w,h) mit irgendeinem Rechteck in box_list überlappt."""
        for (r, (rx, ry), rot) in box_list:
            rw = r.width if not rot else r.height
            rh = r.height if not rot else r.width
            # Offen disjunkt => KEINE Overlap, wenn:
            # x+w <= rx oder rx+rw <= x oder y+h <= ry oder ry+rh <= y
            if not (x + w <= rx or rx + rw <= x or y + h <= ry or ry + rh <= y):
                return True
        return False

    def _is_valid_position(self, problem, solution, box_idx, rect_idx):
        """
        Prüft, ob das Rechteck solution.boxes[box_idx][rect_idx] noch
        innerhalb der Box LxL liegt und keine Overlaps in box_idx verursacht.
        """
        if box_idx >= len(solution.boxes) or rect_idx >= len(solution.boxes[box_idx]):
            return False

        rect, (x, y), rotated = solution.boxes[box_idx][rect_idx]
        w = rect.width if not rotated else rect.height
        h = rect.height if not rotated else rect.width

        # Grenzen
        if x < 0 or y < 0 or x + w > problem.L or y + h > problem.L:
            return False

        # Overlaps
        for i, (r2, (rx, ry), rot2) in enumerate(solution.boxes[box_idx]):
            if i == rect_idx:
                continue
            rw = r2.width if not rot2 else r2.height
            rh = r2.height if not rot2 else r2.width
            if not (x + w <= rx or rx + rw <= x or y + h <= ry or ry + rh <= y):
                return False

        return True
