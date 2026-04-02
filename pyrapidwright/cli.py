import sys
import os
import subprocess
from pathlib import Path

def get_project_root():
    return Path(__file__).parent.parent.absolute()

def run_java_tool(args):
    """Launches the official RapidWright Java CLI."""
    from pyrapidwright import get_rw_path
    
    rw_path = get_rw_path()
    rw_bin = Path(rw_path) / "bin" / "rapidwright"
    
    if not rw_bin.exists():
        print(f"Error: RapidWright binary not found at {rw_bin}")
        print("Please run 'python -m pyrapidwright.install' or equivalent.")
        sys.exit(1)
        
    # Execute the official RapidWright script
    env = os.environ.copy()
    env["RAPIDWRIGHT_PATH"] = str(rw_path)
    
    try:
        subprocess.run([str(rw_bin)] + args, env=env, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(0)

def main():
    if len(sys.argv) < 2:
        print("pyrapidwright - Unified CLI")
        print("Usage:")
        print("  pyrapidwright <JavaTool> [args...]       (e.g. DeviceBrowser, DesignExplorer)")
        print("  pyrapidwright report <dcp>               (Design resource report)")
        print("  pyrapidwright find <dcp> -p <pattern>    (Search and inspect nets)")
        print("  pyrapidwright add-ila <dcp> [args...]    (Interactive ILA insertion)")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    # Official Java tools are usually CamelCase or specific names
    java_tools = ["DeviceBrowser", "DesignExplorer", "RapidWright", "HandPlacer", "LibraryPathCreator"]
    
    if cmd in java_tools or (cmd[0].isupper() and "." not in cmd):
        run_java_tool(sys.argv[1:])
        return

    # Python Subcommands
    if cmd == "report":
        from pyrapidwright.examples import design_report
        sys.argv = [sys.argv[0]] + args
        design_report.main()
    elif cmd == "find":
        from pyrapidwright.examples import find_nets
        sys.argv = [sys.argv[0]] + args
        find_nets.main()
    elif cmd == "add-ila":
        from pyrapidwright.examples import add_ila_cli
        sys.argv = [sys.argv[0]] + args
        add_ila_cli.main()
    else:
        # Fallback to Java tool for anything else
        run_java_tool(sys.argv[1:])

if __name__ == "__main__":
    main()
