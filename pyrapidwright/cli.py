import sys
import os
import importlib
import subprocess
from pathlib import Path

USAGE = """pyrapidwright - Unified CLI
Usage:
  pyrapidwright <JavaTool> [args...]       (e.g. DeviceBrowser, DesignExplorer)
  pyrapidwright report <dcp>               (Design resource report)
  pyrapidwright find <dcp> -p <pattern>    (Search and inspect nets)
  pyrapidwright add-ila <dcp> [args...]    (ILA insertion; --gui for the net selector window)"""

# subcommand -> module in pyrapidwright.examples
SUBCOMMANDS = {"report": "design_report", "find": "find_nets", "add-ila": "add_ila_cli"}

def run_java_tool(args):
    """Launches the official RapidWright Java CLI."""
    from pyrapidwright import get_rw_path

    rw_path = get_rw_path()
    rw_bin = Path(rw_path) / "bin" / "rapidwright"

    if not rw_bin.exists():
        print(f"Error: RapidWright binary not found at {rw_bin}")
        print("Run install_rapidwright.sh or set RAPIDWRIGHT_PATH.")
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
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd in SUBCOMMANDS:
        module = importlib.import_module(f"pyrapidwright.examples.{SUBCOMMANDS[cmd]}")
        sys.argv = [f"pyrapidwright {cmd}"] + args
        module.main()
    elif cmd[0].isupper() or "." in cmd:
        # Official Java tools are CamelCase (DeviceBrowser) or fully qualified class names
        run_java_tool(sys.argv[1:])
    else:
        print(f"Unknown command: {cmd}\n\n{USAGE}")
        sys.exit(1)

if __name__ == "__main__":
    main()
