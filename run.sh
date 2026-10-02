#!/bin/bash
# Convenient runner for BBAT104 TQM Library Management System
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check if python3-tk is present in system
if ! python3 -c "import tkinter" &>/dev/null; then
    echo "=========================================================================="
    echo " [!] NOTICE: 'python3-tk' is not yet installed on your system."
    echo " To open the desktop GUI window, please run:"
    echo "    sudo apt update && sudo apt install -y python3-tk"
    echo "=========================================================================="
    echo ""
fi

# Run using virtual environment if it exists, otherwise system python3
if [ -d "$DIR/.venv" ]; then
    "$DIR/.venv/bin/python" "$DIR/app.py" "$@"
else
    python3 "$DIR/app.py" "$@"
fi
