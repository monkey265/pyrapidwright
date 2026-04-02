import sys
import argparse
from pathlib import Path
import tkinter as tk

from pyrapidwright.design_util import RWDesign
from pyrapidwright import setup_rw
from pyrapidwright.analysis import select_nets_gui, select_clock

def main():
    parser = argparse.ArgumentParser(description="Add an ILA core to a Xilinx DCP design (GUI).")
    parser.add_argument("dcp", help="Input DCP file")
    parser.add_argument("-o", "--output", help="Output DCP file (default: output.dcp)")
    
    args = parser.parse_args()
    output_path = args.output or "output.dcp"
    
    setup_rw()
    
    print(f"[*] Loading design: {args.dcp}...\n")
    design = RWDesign(args.dcp)
    
    # 1. Net Selection (GUI)
    print("[*] Opening Net Selection GUI...")
    root = tk.Tk()
    probe_nets = select_nets_gui(design, root=root)
    root.destroy()
    
    if not probe_nets:
        print("[!] No nets selected. Exiting.")
        return
        
    # 2. Clock Selection (CLI fallback for now, or could be GUI)
    clk_net = select_clock(design)
    if not clk_net:
        print("[!] No clock selected. Exiting.")
        return
        
    # 3. ILA Insertion
    print(f"\n[*] Inserting ILA on {len(probe_nets)} nets...")
    design.insert_ila(probe_nets, clk_net)
    
    # 4. Save
    print(f"[*] Saving design to {output_path}...")
    design.save(output_path)
    print("\n[+] Done! You can now load the output DCP in Vivado.")

if __name__ == "__main__":
    main()
