import random
from .rectangle_packing_problem import Rectangle

def generate_instances(count, num_rectangles, min_side1, max_side1, min_side2, max_side2, L):
    instances = []
    for _ in range(count):
        rects = []
        for __ in range(num_rectangles):
            w = random.randint(min_side1, max_side1)
            h = random.randint(min_side2, max_side2)
            w = min(w, L)
            h = min(h, L)
            rects.append(Rectangle(w,h))
        instances.append(rects)
    return instances
