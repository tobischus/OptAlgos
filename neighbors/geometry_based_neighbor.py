from copy import deepcopy
import random

class GeometryBasedNeighbor:
    """
    Geometriebasierte Nachbarschaft mit Shelf-Logik.
    Hat get_neighbors() und get_neighbors_subset().
    """

    def __init__(self, max_shift=5, neighbor_count=5):
        self.max_shift = max_shift
        self.neighbor_count = neighbor_count

    def get_neighbors(self, problem, solution):
        # Für Vollständigkeit, generiere Moves für alle Rechtecke.
        return self._create_neighbors(problem, solution, all_rects=True, sample_size=0)

    def get_neighbors_subset(self, problem, solution, sample_size):
        # Partielles Sampling
        return self._create_neighbors(problem, solution, all_rects=False, sample_size=sample_size)

    def _create_neighbors(self, problem, solution, all_rects, sample_size):
        neighbors = []
        if not solution.boxes:
            return neighbors

        # Sammle alle (box_idx, rect_idx)
        all_items = []
        for b_idx, box_content in enumerate(solution.boxes):
            for r_idx, _ in enumerate(box_content):
                all_items.append((b_idx, r_idx))

        if not all_items:
            return neighbors

        if all_rects:
            chosen_items = all_items
        else:
            # sample
            if sample_size < 1:
                sample_size = 1
            if sample_size > len(all_items):
                sample_size = len(all_items)
            chosen_items = random.sample(all_items, sample_size)

        for (box_idx, rect_idx) in chosen_items:
            if box_idx >= len(solution.boxes) or rect_idx >= len(solution.boxes[box_idx]):
                continue

            rect, (x, y), rotated = solution.boxes[box_idx][rect_idx]
            box_size = len(solution.boxes[box_idx])
            almost_empty = (box_size <= 2)

            for _ in range(self.neighbor_count):
                move_type = random.choice(["shift","rotate","boxmove","bonus"])

                if move_type=="shift":
                    dx = random.randint(-self.max_shift, self.max_shift)
                    dy = random.randint(-self.max_shift, self.max_shift)
                    if dx==0 and dy==0:
                        continue
                    new_sol = deepcopy(solution)
                    w = rect.width if not rotated else rect.height
                    h = rect.height if not rotated else rect.width
                    new_x = max(0, min(problem.L-w, x+dx))
                    new_y = max(0, min(problem.L-h, y+dy))
                    new_sol.boxes[box_idx][rect_idx] = (rect, (new_x,new_y), rotated)
                    neighbors.append(new_sol)

                elif move_type=="rotate":
                    new_sol = deepcopy(solution)
                    new_sol.boxes[box_idx][rect_idx] = (rect,(x,y), not rotated)
                    neighbors.append(new_sol)

                elif move_type=="boxmove" and len(solution.boxes)>1:
                    new_sol = deepcopy(solution)
                    del new_sol.boxes[box_idx][rect_idx]
                    tgt = random.randrange(len(new_sol.boxes))
                    if tgt==box_idx and len(solution.boxes)>1:
                        # wähle neu
                        continue
                    # Einfügen shelf-basiert
                    rect_inserted = self._place_shelf_in_box(problem, new_sol.boxes[tgt], rect)
                    if not rect_inserted:
                        # neue Box
                        new_box = []
                        new_sol.boxes.append(new_box)
                        self._place_shelf_in_box(problem, new_box, rect)
                    neighbors.append(new_sol)

                elif move_type=="bonus" and almost_empty:
                    # neue Box
                    new_sol = deepcopy(solution)
                    del new_sol.boxes[box_idx][rect_idx]
                    new_box = []
                    new_sol.boxes.append(new_box)
                    self._place_shelf_in_box(problem, new_box, rect)
                    neighbors.append(new_sol)
        return neighbors

    # Shelf-Einfügen in *eine* Box:
    def _place_shelf_in_box(self, problem, box_content, rect):
        if not box_content:
            # leer
            if rect.width<=problem.L and rect.height<=problem.L:
                box_content.append((rect,(0,0),False))
                return True
            elif rect.height<=problem.L and rect.width<=problem.L:
                box_content.append((rect,(0,0),True))
                return True
            return False

        placed = sorted(box_content, key=lambda x: x[1][1])
        shelves = self._build_shelves(problem, placed)
        last_y, last_h, last_w = shelves[-1]
        w,h = rect.width, rect.height
        can_norm = (last_w + w <= problem.L) and (last_y + max(last_h,h)<=problem.L)
        can_rot = (last_w + h <= problem.L) and (last_y + max(last_h,w)<=problem.L)
        if can_norm:
            box_content.append((rect,(last_w, last_y),False))
            return True
        elif can_rot:
            box_content.append((rect,(last_w, last_y),True))
            return True
        else:
            new_y = last_y+last_h
            if new_y>=problem.L:
                return False
            if w<=problem.L and new_y+h<=problem.L:
                box_content.append((rect,(0,new_y),False))
                return True
            if h<=problem.L and new_y+w<=problem.L:
                box_content.append((rect,(0,new_y),True))
                return True
            return False

    def _build_shelves(self, problem, placed_rects):
        shelves = []
        cy = None
        ch = 0
        cw = 0
        for (r,(rx,ry),rot) in placed_rects:
            w = r.width if not rot else r.height
            h = r.height if not rot else r.width
            if cy is None:
                cy = ry
                ch = h
                cw = w
            else:
                if abs(ry-cy)<1e-9:
                    cw += w
                    ch = max(ch,h)
                else:
                    shelves.append((cy,ch,cw))
                    cy = ry
                    ch = h
                    cw = w
        if cy is not None:
            shelves.append((cy,ch,cw))
        return shelves
