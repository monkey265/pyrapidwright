# pyrapidwright
[![RapidWright](https://img.shields.io/badge/RapidWright-2023.2+-orange.svg)](https://www.rapidwright.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-11%2B-red.svg)](https://www.oracle.com/java/)

This repository provides a Python-based library and unified CLI for [RapidWright](https://www.rapidwright.io/). It provides highlevel methods for scripting.

## Installation & Setup

### 1. Install RapidWright
Use the provided script to clone and build RapidWright automatically:
```bash
bash install_rapidwright.sh
```

### 2. Install Python Package
Install in editable mode to register the unified `pyrapidwright` command:
```bash
pip install -e .
```

### 3. Unified CLI Usage
Once installed, the `pyrapidwright` command handles both official Java tools and Python-based analysis:

```bash
# Launch Official Java Tools
pyrapidwright DeviceBrowser
pyrapidwright DesignExplorer

# Run Python Analysis Subcommands
pyrapidwright report <dcp_file>
pyrapidwright find <dcp_file> -p "*axi*"
pyrapidwright add-ila <dcp_file>
```

## Features
*   **Unified CLI**: Single entry point for all RapidWright-related tasks.
*   **Interactive ILA Insertion**: Add debug probes to implemented DCPs.
*   **Advanced Analysis**:
    *   Resource usage reporting (LUTs, FFs, BRAMs, DSPs).
    *   Automatic clock net identification.
    *   Hierarchical net/cell inspection (drivers, loads, placement).
*   **GUI & CLI Support**: Tkinter-based tree-view for easy net navigation.

## Project Structure
*   `pyrapidwright/`: Core library and JVM bridge.
    *   `cli.py`: Unified command dispatcher.
    *   `analysis.py`: Selection and analysis logic.
    *   `design_util.py`: High-level `RWDesign` API.
    *   `examples/`: Integrated example scripts.
*   `pyproject.toml`: Package metadata and entry points.
