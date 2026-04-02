import os
import sys
import re
import fnmatch
import tkinter as tk
from tkinter import ttk, messagebox

def select_nets_cli(design):
    """Interactive CLI loop to select nets from the design."""
    nets = design.get_all_nets()
    print("\n" + "="*40)
    print("   PYRAPIDWRIGHT ILA NET SELECTION (CLI)")
    print("="*40)
    print(f"Total nets in design: {len(nets)}")
    print("\nInstructions:")
    print(" - Enter a number to select a net by index.")
    print(" - Enter a comma-separated list of numbers (e.g., 1,2,5).")
    print(" - Enter a string to search for nets (e.g., 'data_out').")
    print(" - Press Enter without typing anything to finish selection.")
    
    selected_indices = set()
    
    # Show some initial nets
    print("\nSample nets:")
    for i in range(min(20, len(nets))):
        print(f" [{i:3d}] {nets[i].getName()}")
    
    while True:
        print(f"\nSelected so far: {len(selected_indices)} nets")
        val = input("Select/Search> ").strip()
        
        if not val:
            if not selected_indices:
                confirm = input("No nets selected. Exit? (y/n): ")
                if confirm.lower() == 'y':
                    return []
                continue
            break
        
        if val.isdigit():
            idx = int(val)
            if 0 <= idx < len(nets):
                selected_indices.add(idx)
                print(f" [+] Added: {nets[idx].getName()}")
            else:
                print(f" [!] Index {idx} out of range.")
        elif "," in val:
            parts = val.split(",")
            added_count = 0
            for p in parts:
                p = p.strip()
                if p.isdigit():
                    idx = int(p)
                    if 0 <= idx < len(nets):
                        selected_indices.add(idx)
                        added_count += 1
            print(f" [+] Added {added_count} nets.")
        else:
            # Search
            results = [i for i, n in enumerate(nets) if val in str(n.getName())]
            if not results:
                print(f" [!] No nets matching '{val}' found.")
            else:
                print(f"\nFound {len(results)} matches:")
                for r in results[:30]:
                    status = "*" if r in selected_indices else " "
                    print(f" {status}[{r:5d}] {nets[r].getName()}")
                if len(results) > 30:
                    print(f" ... and {len(results)-30} more.")
                
                quick_add = input("\nAdd all these matches? (y/n) or 'idx1,idx2...': ").strip().lower()
                if quick_add == 'y':
                    for r in results:
                        selected_indices.add(r)
                elif quick_add and any(c.isdigit() for c in quick_add):
                    for p in quick_add.split(","):
                        p = p.strip()
                        if p.isdigit():
                            idx = int(p)
                            if 0 <= idx < len(nets):
                                selected_indices.add(idx)

    return [nets[i].getName() for i in selected_indices]

class NetSelectorGUI:
    def __init__(self, nets, root=None):
        if root is None:
            self.root = tk.Tk()
            self.own_root = True
        else:
            self.root = root
            self.own_root = False
            
        self.root.title("pyrapidwright ILA Net Selection")
        self.root.geometry("800x600")
        
        self.all_nets = nets
        self.selected_map = {} # net_name -> bool
        self.final_selection = []
        
        self._setup_style()
        self._setup_ui()
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        if self.own_root:
            self.root.mainloop()

    def _setup_style(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(main_frame, text="Select Nets to Probe", font=("Helvetica", 14, "bold"))
        header.pack(pady=(0, 10))

        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter Search:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._on_filter_change)
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.filter_entry.focus_set()

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "selected")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Hierarchical Net Name")
        self.tree.heading("selected", text="Status", anchor=tk.CENTER)
        
        self.tree.column("name", width=600, anchor=tk.W)
        self.tree.column("selected", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_double_click)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Selected: 0 nets")
        ttk.Label(bottom_frame, textvariable=self.status_var).pack(side=tk.LEFT)

        ttk.Button(bottom_frame, text="Confirm Selection", command=self._on_confirm).pack(side=tk.RIGHT)
        ttk.Button(bottom_frame, text="Cancel", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Toggle Selected", command=self._on_toggle_selected).pack(side=tk.RIGHT, padx=5)

        self._update_tree()

    def _update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = self.filter_var.get()
        count = 0
        for net in self.all_nets:
            name = str(net.getName())
            if query in name:
                status = "[X]" if self.selected_map.get(name, False) else "[ ]"
                self.tree.insert("", tk.END, values=(name, status))
                count += 1
                if count > 2000:
                    self.tree.insert("", tk.END, values=("... filter for more results ...", ""))
                    break

    def _on_filter_change(self, *args):
        self._update_tree()

    def _on_toggle_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        name = self.tree.item(item, "values")[0]
        
        if name == "... filter for more results ...":
            return

        current = self.selected_map.get(name, False)
        self.selected_map[name] = not current
        new_status = "[X]" if not current else "[ ]"
        self.tree.set(item, "selected", new_status)
        self._update_status()

    def _on_double_click(self, event):
        self._on_toggle_selected()

    def _update_status(self):
        count = sum(1 for v in self.selected_map.values() if v)
        self.status_var.set(f"Selected: {count} nets")

    def _on_confirm(self):
        self.final_selection = [name for name, sel in self.selected_map.items() if sel]
        self.root.destroy()

def select_nets_gui(design, root=None):
    """Launches the GUI for net selection."""
    nets = design.get_all_nets()
    gui = NetSelectorGUI(nets, root=root)
    return gui.final_selection

def select_nets(design, nets_hint=None, gui=False):
    """
    Unified entry point for net selection.
    If nets_hint is provided, returns it.
    If gui is True, launches the GUI.
    Otherwise, launches the CLI interactive loop.
    """
    if nets_hint:
        return nets_hint
    if gui:
        return select_nets_gui(design)
    return select_nets_cli(design)

def select_clock(design, clk_net_hint=None):
    """Interactive loop to select a clock net."""
    if clk_net_hint:
        return clk_net_hint
        
    print("\n" + "-"*20)
    print("Clock Selection")
    print("-"*20)
    print("RapidWright needs a clock for the ILA.")
    print("Common clocks often contain 'clk' or 'BUFG'.")
    
    nets = design.get_all_nets()
    clk_candidates = [str(n.getName()) for n in nets if 'clk' in str(n.getName()).lower() or 'bufg' in str(n.getName()).lower()]
    
    if clk_candidates:
        print("\nSuggested clocks:")
        for i, c in enumerate(clk_candidates[:10]):
            print(f" [{i}] {c}")
        
        clk_input = input("\nEnter clock name or index from suggestions: ").strip()
        if clk_input.isdigit():
            idx = int(clk_input)
            if 0 <= idx < len(clk_candidates):
                return clk_candidates[idx]
        return clk_input
    
    return input("Enter clock hierarchical name: ").strip()

def search_nets(design, pattern, regex=False):
    """
    Search for nets in the design using wildcards (*, ?) or regular expressions.
    Returns a list of matching net names.
    """
    nets = design.get_all_nets()
    results = []
    
    if regex:
        compiled_re = re.compile(pattern)
        for n in nets:
            name = str(n.getName())
            if compiled_re.search(name):
                results.append(name)
    else:
        # Wildcard search (case-insensitive)
        for n in nets:
            name = str(n.getName())
            if fnmatch.fnmatch(name.lower(), pattern.lower()):
                results.append(name)
    
    return results

def get_clock_nets(design):
    """
    Identifies potential clock nets in the design.
    Returns a list of net names likely to be clocks.
    """
    nets = design.get_all_nets()
    clocks = []
    for n in nets:
        name = str(n.getName())
        # Heuristic: search for 'clk', 'bufg', 'clock' or check for global clock buffer drivers
        if any(x in name.lower() for x in ['clk', 'bufg', 'clock']):
            clocks.append(name)
    return clocks

def report_resource_usage(design):
    """
    Summarizes the resource usage (cells) in the design.
    Returns a dictionary of counts.
    """
    counts = {
        "LUTs": 0,
        "Registers": 0,
        "BRAMs": 0,
        "DSPs": 0,
        "Carry": 0,
        "Others": 0
    }
    
    # We iterate over EDIF cell instances (logical view)
    netlist = design.design.getNetlist()
    for inst in netlist.getAllLeafCellInstances():
        type_name = str(inst.getCellType().getName()).upper()
        
        if "LUT" in type_name:
            counts["LUTs"] += 1
        elif type_name.startswith("FD") or "REG" in type_name:
            counts["Registers"] += 1
        elif "BRAM" in type_name or "FIFO" in type_name or "RAMB" in type_name:
            counts["BRAMs"] += 1
        elif "DSP" in type_name:
            counts["DSPs"] += 1
        elif "CARRY" in type_name:
            counts["Carry"] += 1
        else:
            counts["Others"] += 1
            
    return counts
