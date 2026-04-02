#!/bin/bash
# install_rapidwright.sh
# Automates the cloning and building of RapidWright for this boilerplate.

REPO_URL="https://github.com/Xilinx/RapidWright.git"
INSTALL_DIR="$(pwd)/rapidwright"

echo "=============================================="
echo "    RapidWright Installation Script"
echo "=============================================="

# 1. Clone
if [ -d "$INSTALL_DIR" ]; then
    echo "[*] RapidWright directory already exists at $INSTALL_DIR"
    read -p "Overwrite and re-clone? (y/n): " confirm
    if [[ $confirm == [yY] ]]; then
        rm -rf "$INSTALL_DIR"
    else
        echo "[*] Skipping clone. Proceeding to build..."
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    echo "[*] Cloning RapidWright from $REPO_URL..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 2. Build
echo "[*] Building RapidWright (this may take a few minutes)..."
cd "$INSTALL_DIR"

# Ensure jars are present and compile classes to bin/
./gradlew updateJars compileJava

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================="
    echo "    SUCCESS: RapidWright Built Successfully"
    echo "=============================================="
    echo ""
    echo "To use this boilerplate, set the following environment variable:"
    echo "  export RAPIDWRIGHT_PATH=\"$INSTALL_DIR\""
    echo ""
    echo "You can add this to your .bashrc or run 'source' on this script if updated."
    echo "=============================================="
else
    echo "[!] Error: RapidWright build failed. Please check the logs above."
    exit 1
fi
