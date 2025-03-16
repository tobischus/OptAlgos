# gui/gui.py

import tkinter as tk
import tkinter.ttk as ttk
import threading
import time
import random

from problem.instance_generator import generate_instances
from problem.rectangle_packing_problem import RectanglePackingProblem, RectangleSolution
from algorithms.greedy import greedy
from algorithms.local_search import local_search
from strategies.greedy_strategy import (
    StrategyLargestAreaFirst,
    StrategyMaxSideFirst,
    StrategyBestFitShelf
)
from strategies.guillotine_strategy import StrategyGuillotine
from neighbors.geometry_based_neighbor import GeometryBasedNeighbor
from neighbors.rule_based_neighbor import RuleBasedNeighbor
from neighbors.overlapping_neighbor import OverlappingNeighbor

class PackingGUI:
    def __init__(self, width=1200, height=800):
        self.root = tk.Tk()
        self.root.title("Rectangle Packing Visualization")
        self.root.geometry(f"{width}x{height}")

        self.mainframe = ttk.Frame(self.root)
        self.mainframe.pack(fill=tk.BOTH, expand=True)

        # Instanzparameter
        self.var_num_rect = tk.IntVar(value=15)
        self.var_min_side1 = tk.IntVar(value=1)
        self.var_max_side1 = tk.IntVar(value=9)
        self.var_min_side2 = tk.IntVar(value=1)
        self.var_max_side2 = tk.IntVar(value=9)
        self.var_L = tk.IntVar(value=20)

        self.var_algorithm = tk.StringVar(value="Greedy")
        # NEU: 3 mögliche Strategien
        self.var_greedy_strategy = tk.StringVar(value="LargestArea")
        self.var_neighbor_type = tk.StringVar(value="Geometry")

        # Problem-Instanz
        self.current_problem = None
        self.current_rectangles = []

        # Snapshots
        self.snapshots = []
        self.snapshot_idx = 0

        # Progress
        self.progress_toplevel = None
        self.progress_var = None

        self._build_ui()

    def _build_ui(self):
        # Parameter-Frame
        param_frame = ttk.LabelFrame(self.mainframe, text="Parameter für Instanz")
        param_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(param_frame, text="Anzahl Rechtecke:").grid(row=0, column=0, sticky=tk.E)
        ttk.Entry(param_frame, textvariable=self.var_num_rect, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(param_frame, text="min Seite1:").grid(row=0, column=2, sticky=tk.E)
        ttk.Entry(param_frame, textvariable=self.var_min_side1, width=5).grid(row=0, column=3, padx=5)

        ttk.Label(param_frame, text="max Seite1:").grid(row=0, column=4, sticky=tk.E)
        ttk.Entry(param_frame, textvariable=self.var_max_side1, width=5).grid(row=0, column=5, padx=5)

        ttk.Label(param_frame, text="min Seite2:").grid(row=0, column=6, sticky=tk.E)
        ttk.Entry(param_frame, textvariable=self.var_min_side2, width=5).grid(row=0, column=7, padx=5)

        ttk.Label(param_frame, text="max Seite2:").grid(row=0, column=8, sticky=tk.E)
        ttk.Entry(param_frame, textvariable=self.var_max_side2, width=5).grid(row=0, column=9, padx=5)

        ttk.Label(param_frame, text="Boxlänge L:").grid(row=0, column=10, sticky=tk.E)
        ttk.Entry(param_frame, textvariable=self.var_L, width=5).grid(row=0, column=11, padx=5)

        btn_gen = ttk.Button(param_frame, text="Instanz generieren", command=self.on_generate_instance)
        btn_gen.grid(row=0, column=12, padx=10)

        # Algorithmus-Frame
        algo_frame = ttk.LabelFrame(self.mainframe, text="Algorithmus auswählen")
        algo_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        rb_greedy = ttk.Radiobutton(algo_frame, text="Greedy",
                                    variable=self.var_algorithm, value="Greedy",
                                    command=self.on_algo_change)
        rb_ls = ttk.Radiobutton(algo_frame, text="Lokale Suche",
                                variable=self.var_algorithm, value="LocalSearch",
                                command=self.on_algo_change)
        rb_greedy.grid(row=0, column=0, padx=5)
        rb_ls.grid(row=0, column=1, padx=5)

        # Combox für Greedy-Strategie: JETZT mit 3 Optionen
        self.combo_greedy = ttk.Combobox(
    algo_frame,
    textvariable=self.var_greedy_strategy,
    state="readonly",
    values=["LargestArea", "MaxSide", "BestFitShelf", "Guillotine"]
        )
        self.combo_greedy.grid(row=0, column=2, padx=5)

        # Combox für LS-Nachbarschaften
        self.combo_neighbor = ttk.Combobox(
            algo_frame,
            textvariable=self.var_neighbor_type,
            state="readonly",
            values=["Geometry", "Rule", "Overlap"]
        )
        self.combo_neighbor.grid(row=0, column=3, padx=5)

        # default: Nachbarschaftsbox verstecken, wenn "Greedy" ausgewählt ist
        if self.var_algorithm.get() == "Greedy":
            self.combo_neighbor.grid_remove()
        else:
            self.combo_greedy.grid_remove()

        btn_start = ttk.Button(algo_frame, text="Algorithmus starten", command=self.on_start_algorithm)
        btn_start.grid(row=0, column=4, padx=5)

        # Visualisierung (mit Scrollbars)
        vis_frame = ttk.LabelFrame(self.mainframe, text="Visualisierung")
        vis_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas_frame = ttk.Frame(vis_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(yscrollcommand=self.scrollbar_y.set,
                              xscrollcommand=self.scrollbar_x.set)

        nav_frame = ttk.Frame(self.mainframe)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.label_stepinfo = ttk.Label(nav_frame, text="Schritt 0/0")
        self.label_stepinfo.pack(side=tk.LEFT, padx=5)

        btn_prev = ttk.Button(nav_frame, text="<< Zurück", command=self.show_previous)
        btn_prev.pack(side=tk.LEFT, padx=5)
        btn_next = ttk.Button(nav_frame, text="Weiter >>", command=self.show_next)
        btn_next.pack(side=tk.LEFT, padx=5)

    def on_generate_instance(self):
        nr = self.var_num_rect.get()
        mn1 = self.var_min_side1.get()
        mx1 = self.var_max_side1.get()
        mn2 = self.var_min_side2.get()
        mx2 = self.var_max_side2.get()
        L = self.var_L.get()

        inst = generate_instances(1, nr, mn1, mx1, mn2, mx2, L)[0]
        self.current_rectangles = inst
        self.current_problem = RectanglePackingProblem(L, inst)

        self.snapshots = []
        self.snapshot_idx = 0
        self.canvas.delete("all")
        self.label_stepinfo.config(text="Schritt 0/0")
        self.canvas.create_text(20,20, text=f"{nr} Rechtecke generiert.\nNoch keine Lösung.", anchor="nw")

        # Scrollregion zurücksetzen
        self.canvas.config(scrollregion=(0, 0, 0, 0))

    def on_algo_change(self):
        if self.var_algorithm.get() == "Greedy":
            self.combo_greedy.grid()
            self.combo_neighbor.grid_remove()
        else:
            self.combo_greedy.grid_remove()
            self.combo_neighbor.grid()

    def on_start_algorithm(self):
        if not self.current_problem:
            return

        self.snapshots.clear()
        self.snapshot_idx = 0
        self.canvas.delete("all")

        if self.var_algorithm.get() == "Greedy":
            self.run_greedy()
        else:
            self.run_local_search_threaded()

    def run_greedy(self):
        strategy_name = self.var_greedy_strategy.get()
        if strategy_name == "LargestArea":
            strategy = StrategyLargestAreaFirst()
        elif strategy_name == "MaxSide":
            strategy = StrategyMaxSideFirst()
        elif strategy_name == "BestFitShelf":
            strategy = StrategyBestFitShelf()
        elif strategy_name == "Guillotine":
            strategy = StrategyGuillotine(sort_by="area-desc")
        else:
            strategy = StrategyLargestAreaFirst()

        rects_ordered = strategy.get_ordered_rectangles(self.current_problem.rectangles)
        solution = self.current_problem.create_empty_solution()

        # Nur alle x Rechtecke als Snapshot
        snapshot_frequency = max(1, len(rects_ordered)//10)

        for i, rect in enumerate(rects_ordered):
            solution = strategy.place_rectangle_in_solution(rect, solution, self.current_problem)
            if (i+1) % snapshot_frequency == 0 or i == len(rects_ordered)-1:
                self.add_snapshot(solution, f"Greedy Schritt {i+1}: {len(solution.boxes)} Box(en)")

        self.snapshot_idx = 0
        self.show_snapshot()

    def run_local_search_threaded(self):
        self.progress_toplevel = tk.Toplevel(self.root)
        self.progress_toplevel.title("Lokale Suche - bitte warten...")

        ttk.Label(self.progress_toplevel, text="Suche nach besseren Lösungen...").pack(padx=10, pady=10)
        self.progress_var = tk.DoubleVar(value=0)
        pbar = ttk.Progressbar(self.progress_toplevel, variable=self.progress_var, maximum=100)
        pbar.pack(fill="x", padx=10, pady=10)

        start_sol = RectangleSolution()
        for r in self.current_rectangles:
            start_sol.boxes.append([(r,(0,0),False)])

        nb = self.var_neighbor_type.get()
        if nb == "Geometry":
            neighbor = GeometryBasedNeighbor(max_shift=5, neighbor_count=5)
        elif nb == "Rule":
            neighbor = RuleBasedNeighbor(swaps_per_call=5)
        else:
            neighbor = OverlappingNeighbor(initial_overlap_ratio=100, decrement=10, neighbor_count=5)

        def snapshot_cb(sol, iteration, val, elapsed):
            self.add_snapshot(sol, f"Iter {iteration}: val={val}")
            progress_pct = min(100, (elapsed/10.0)*100)
            self.progress_var.set(progress_pct)
            self.root.update_idletasks()

        def worker():
            best_sol = local_search(
                problem=self.current_problem,
                current_solution=start_sol,
                neighbor_generator=neighbor,
                max_iter=1000,
                max_time=10.0,
                partial_sample_size=5,
                snapshot_callback=snapshot_cb
            )
            self.root.after(0, self.local_search_done, best_sol)

        import threading
        t = threading.Thread(target=worker)
        t.start()

    def local_search_done(self, best_sol):
        if self.progress_toplevel:
            self.progress_toplevel.destroy()
            self.progress_toplevel = None

        if not self.snapshots:
            self.add_snapshot(best_sol, f"Ende: {len(best_sol.boxes)} Box(en)")

        self.snapshot_idx = 0
        self.show_snapshot()

    def add_snapshot(self, solution, label):
        import copy
        self.snapshots.append((copy.deepcopy(solution), label))

    def show_snapshot(self):
        if not self.snapshots:
            return
        sol, txt = self.snapshots[self.snapshot_idx]
        self.label_stepinfo.config(text=f"Schritt {self.snapshot_idx+1}/{len(self.snapshots)}")
        self.draw_solution(sol, txt)

    def show_previous(self):
        if self.snapshot_idx > 0:
            self.snapshot_idx -= 1
            self.show_snapshot()

    def show_next(self):
        if self.snapshot_idx < len(self.snapshots) - 1:
            self.snapshot_idx += 1
            self.show_snapshot()

    def draw_solution(self, solution, info_text):
        self.canvas.delete("all")
        self.canvas.create_text(10,10, text=info_text, anchor="nw", font=("Arial",12,"bold"))
        if not self.current_problem:
            return
        L = self.current_problem.L
        box_size = 200
        margin = 20
        xstart = margin
        ystart = 40

        max_x = xstart
        max_y = ystart

        for box_index, box_content in enumerate(solution.boxes):
            self.canvas.create_rectangle(xstart, ystart, xstart+box_size, ystart+box_size,
                                         outline="gray", width=2)
            for r_index, (rect,(rx,ry),rot) in enumerate(box_content):
                w = rect.width if not rot else rect.height
                h = rect.height if not rot else rect.width
                scale = box_size/float(L)
                sx = rx*scale
                sy = ry*scale
                sw = w*scale
                sh = h*scale
                # Farbfehlsichere 2-Farben
                fill_color = "#1E90FF" if (r_index % 2) == 0 else "#FFD700"
                self.canvas.create_rectangle(
                    xstart+sx, ystart+sy,
                    xstart+sx+sw, ystart+sy+sh,
                    outline="black", width=1, fill=fill_color
                )
            xstart += box_size + margin
            if xstart+box_size > self.canvas.winfo_width()-margin:
                xstart = margin
                ystart += box_size + margin

            max_x = max(max_x, xstart+box_size)
            max_y = max(max_y, ystart+box_size)

        self.canvas.config(scrollregion=(0, 0, max_x + margin, max_y + margin))

    def run(self):
        self.root.mainloop()
