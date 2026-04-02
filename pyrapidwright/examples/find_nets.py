import sys
import argparse
from pathlib import Path

from pyrapidwright.design_util import RWDesign
from pyrapidwright import setup_rw
from pyrapidwright.analysis import search_nets

def main():
    parser = argparse.ArgumentParser(description="Search and inspect nets in a Xilinx DCP.")
    parser.add_argument("dcp", help="Input DCP file")
    parser.add_argument("-p", "--pattern", help="Search pattern (e.g., '*clk*')")
    parser.add_argument("-r", "--regex", action="store_true", help="Use regex for pattern")
    parser.add_argument("-i", "--inspect", help="Show connectivity for a specific net name")
    
    args = parser.parse_args()
    
    if not args.pattern and not args.inspect:
        parser.error("Either --pattern or --inspect must be provided.")
    
    setup_rw()
    
    print(f"[*] Loading design: {args.dcp}...")
    design = RWDesign(args.dcp)
    
    if args.inspect:
        print(f"\n[ Inspecting Net: {args.inspect} ]")
        info = design.get_net_info(args.inspect)
        if not info:
            print(f" [!] Net '{args.inspect}' not found.")
        else:
            print(f" - Drivers: {len(info['drivers'])}")
            for d in info['drivers']:
                print(f"    <- {d}")
            print(f" - Loads: {len(info['loads'])}")
            for l in info['loads']:
                print(f"    -> {l}")
        return

    print(f"\n[*] Searching for pattern: '{args.pattern}' (regex={args.regex})")
    results = search_nets(design, args.pattern, args.regex)
    
    if not results:
        print(" [!] No nets found matching the pattern.")
    else:
        print(f"\nFound {len(results)} matches:")
        for r in results[:50]:
            print(f" - {r}")
        if len(results) > 50:
            print(f" ... and {len(results)-50} more.")
            
    print(f"\nTotal matches: {len(results)}")

if __name__ == "__main__":
    main()
