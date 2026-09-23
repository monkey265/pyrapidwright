# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python wrapper (via JPype) around [RapidWright](https://www.rapidwright.io/), the Java FPGA toolkit, for scripting against Xilinx DCP checkpoints: resource reports, net search/inspection, and ILA debug-core insertion. It exposes one `pyrapidwright` CLI.

## Setup & commands

```bash
bash install_rapidwright.sh          # clones + builds RapidWright into ./rapidwright (gitignored), via ./gradlew updateJars compileJava
export RAPIDWRIGHT_PATH="$PWD/rapidwright"
uv sync                              # or `pip install -e .`; registers the `pyrapidwright` entry point (pyrapidwright.cli:main)
                                     # with uv, prefix the commands below with `uv run`

pyrapidwright report <dcp>
pyrapidwright find <dcp> -p "*axi*"          # wildcard, case-insensitive; -r for regex; -i <net> to show drivers/loads
pyrapidwright add-ila <dcp> [-n NET ...] [-c CLK] [-o out.dcp] [--gui]   # prompts for anything not given; --gui = Tkinter net picker
pyrapidwright DeviceBrowser                  # Capitalized names / dotted class names go to RapidWright's bin/rapidwright

uv run python tests/test_design.py           # the only test: builds a tiny netlist in RapidWright, needs no DCP or Vivado
```

There is no linter or CI. `.dcp`, `.edf`, and `.tcl` files are gitignored.

## Architecture

- **JVM lifecycle (`pyrapidwright/__init__.py`)**: `setup_rw()` starts the JVM; `RWDesign.__init__` calls it, and repeat calls do nothing. Importing the package does not start it. JPype can start only one JVM per process, so the classpath (`bin`, `bin/*`, `jars/*`) is fixed at first start. `get_rw_path()` uses `$RAPIDWRIGHT_PATH`, else `./rapidwright`.
- **Java imports must come after JVM start.** `com.xilinx.rapidwright.*` imports sit inside functions or methods (see `design_util.py` and `get_clock_nets`), never at module top level. Keep it that way.
- **`design_util.RWDesign`** is the high-level wrapper around a loaded `Design`. It holds `.design`, `.device`, and `.netlist`, and it is where new design-level operations go (net and cell info, `insert_ila`, `save`). Net names are looked up in the logical netlist (`getHierNetFromName`). Java strings come back as Java objects, so the code wraps them in `str(...)` before comparing or formatting them.
- **`analysis.py`** has functions that take an `RWDesign`: interactive net and clock selection (CLI loop plus the `NetSelectorGUI` Tkinter class), `search_nets`, `get_clock_nets` (nets driven by BUFG\*, else a name heuristic), and `report_resource_usage` (buckets cells by cell-type prefix).
- **`cli.py`** is a hand-rolled dispatcher, not argparse. Commands in `SUBCOMMANDS` rewrite `sys.argv` and call `main()` in the matching `examples/*.py` module, which does its own argparse. Capitalized or dotted commands go to `run_java_tool`; anything else prints usage. To add a subcommand, add an `examples/` module with `main()` and an entry in `SUBCOMMANDS`.

## RapidWright gotchas

- `ILAInserter.applyILAToDesign` only wires the clock. `RWDesign.insert_ila` wires the probes itself: the ILA sits in the top cell with one bus port `probes[N-1:0]`, so `_net_to_top` adds output ports up the hierarchy (the same approach upstream uses for the clock). Ports go on the cell *type*, so a multiply-instantiated module gets the port on every instance.
- `ILAInserter.createILADesign` generates the ILA core with **Vivado**, so ILA insertion needs Vivado installed and on PATH.
- You cannot insert an ILA into a DCP that already has a debug hub, because RapidWright fails to load it. `RWDesign.__init__` turns that load failure into a clear `RuntimeError`. Add all probes in one pass on a clean DCP.
