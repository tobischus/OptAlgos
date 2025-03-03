from .interfaces import OptimizationProblem

class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

class RectangleSolution:
    def __init__(self):
        self.boxes = []  # list of list of (Rectangle,(x,y),rotated)

class RectanglePackingProblem(OptimizationProblem):
    def __init__(self, L, rectangles):
        self.L = L
        self.rectangles = rectangles

    def evaluate_solution(self, solution):
        """
        Minimierungsziel: #Boxen * 1000 + Strafe pro Overlap + out-of-bounds
        """
        box_count = len(solution.boxes)
        penalty = 0
        for box_content in solution.boxes:
            for i in range(len(box_content)):
                r_i, (x_i,y_i), rot_i = box_content[i]
                w_i = r_i.width if not rot_i else r_i.height
                h_i = r_i.height if not rot_i else r_i.width
                # boundary
                if x_i<0 or y_i<0 or (x_i+w_i)>self.L or (y_i+h_i)>self.L:
                    penalty += 100000
                for j in range(i+1, len(box_content)):
                    r_j, (x_j,y_j), rot_j = box_content[j]
                    w_j = r_j.width if not rot_j else r_j.height
                    h_j = r_j.height if not rot_j else r_j.width
                    # overlap check
                    if not( (x_j+w_j)<=x_i or x_j>=(x_i+w_i) or (y_j+h_j)<=y_i or y_j>=(y_i+h_i) ):
                        penalty += 100000
        return box_count*1000 + penalty

    def create_empty_solution(self):
        return RectangleSolution()

    def place_rectangle_shelf(self, rect, solution):
        """
        Einfaches Shelf-Verfahren:
        - Probiere existierende Boxen
        - Falls nicht reinpasst, neue Box
        """
        for box_content in solution.boxes:
            if self._try_shelf_insert(rect, box_content):
                return solution
        # neue Box
        new_box = []
        solution.boxes.append(new_box)
        self._try_shelf_insert(rect, new_box)  # passt (lt. Aufgabe)
        return solution

    def _try_shelf_insert(self, rect, box_content):
        if not box_content:
            # leer
            if rect.width<=self.L and rect.height<=self.L:
                box_content.append((rect,(0,0),False))
                return True
            if rect.height<=self.L and rect.width<=self.L:
                box_content.append((rect,(0,0),True))
                return True
            return False

        # baue shelves
        placed = sorted(box_content, key=lambda x: x[1][1])
        shelves = []
        cy=None
        ch=0
        cw=0
        for (r,(rx,ry),rot) in placed:
            w = r.width if not rot else r.height
            h = r.height if not rot else r.width
            if cy is None:
                cy=ry
                ch=h
                cw=w
            else:
                if abs(ry-cy)<1e-9:
                    # selbe Zeile
                    cw+=w
                    ch = max(ch,h)
                else:
                    shelves.append((cy,ch,cw))
                    cy=ry
                    ch=h
                    cw=w
        if cy is not None:
            shelves.append((cy,ch,cw))

        # versuche in letzter Zeile
        last_y,last_h,last_w = shelves[-1]
        w=rect.width
        h=rect.height
        # normal
        can_norm = (last_w + w <= self.L) and (last_y+max(last_h,h)<=self.L)
        can_rot = (last_w + h <= self.L) and (last_y+max(last_h,w)<=self.L)
        if can_norm:
            box_content.append((rect,(last_w,last_y),False))
            return True
        if can_rot:
            box_content.append((rect,(last_w,last_y),True))
            return True
        # neue Zeile
        new_y = last_y+last_h
        if new_y>=self.L:
            return False
        if w<=self.L and (new_y+h)<=self.L:
            box_content.append((rect,(0,new_y),False))
            return True
        if h<=self.L and (new_y+w)<=self.L:
            box_content.append((rect,(0,new_y),True))
            return True
        return False
