import sys
import argparse
from pathlib import Path

from pyrapidwright.design_util import RWDesign
from pyrapidwright import setup_rw
from pyrapidwright.analysis import report_resource_usage, get_clock_nets

def main():
    parser = argparse.ArgumentParser(description="Generate a report for a Xilinx DCP design.")
    parser.add_argument("dcp", help="Input DCP file")
    args = parser.parse_args()
    
    setup_rw()
    
    print(f"[*] Loading design: {args.dcp}...\n")
    design = RWDesign(args.dcp)
    
    print("="*40)
    print("      DESIGN SUMMARY REPORT")
    print("="*40)
    print(f"Device: {design.device.getName()}")
    
    # Resource Usage
    print("\n[ Resource Usage ]")
    resources = report_resource_usage(design)
    for res, count in resources.items():
        print(f" - {res:12s}: {count:6d}")
        
    # Clock Information
    print("\n[ Clock Nets ]")
    clocks = get_clock_nets(design)
    if not clocks:
        print(" - No clocks identified by heuristic.")
    else:
        for clk in clocks[:15]:
            print(f" - {clk}")
        if len(clocks) > 15:
            print(f" ... and {len(clocks)-15} more.")
            
    print("\n" + "="*40)

if __name__ == "__main__":
    main()
