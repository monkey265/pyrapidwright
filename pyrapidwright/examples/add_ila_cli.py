import argparse

from pyrapidwright.design_util import RWDesign
from pyrapidwright.analysis import select_nets, select_clock

def main():
    parser = argparse.ArgumentParser(description="Add an ILA core to a Xilinx DCP design.")
    parser.add_argument("dcp", help="Input DCP file")
    parser.add_argument("-o", "--output", help="Output DCP file (default: output.dcp)")
    parser.add_argument("-n", "--nets", nargs="+", help="Nets to probe")
    parser.add_argument("-c", "--clock", help="Clock net name")
    parser.add_argument("--gui", action="store_true", help="Pick nets in a window instead of the terminal")
    
    args = parser.parse_args()
    output_path = args.output or "output.dcp"
    
    print(f"[*] Loading design: {args.dcp}...\n")
    design = RWDesign(args.dcp)
    
    # 1. Net Selection
    probe_nets = select_nets(design, args.nets, gui=args.gui)
    if not probe_nets:
        print("[!] No nets selected. Exiting.")
        return
        
    # 2. Clock Selection
    clk_net = select_clock(design, args.clock)
    if not clk_net:
        print("[!] No clock selected. Exiting.")
        return
        
    # 3. ILA Insertion
    print(f"\n[*] Inserting ILA on {len(probe_nets)} nets...")
    try:
        design.insert_ila(probe_nets, clk_net)
    except ValueError as e:
        raise SystemExit(f"[!] {e}")
    
    # 4. Save
    print(f"[*] Saving design to {output_path}...")
    design.save(output_path)
    print("\n[+] Done! You can now load the output DCP in Vivado.")

if __name__ == "__main__":
    main()
