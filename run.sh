#!/bin/bash
# Convenient runner for BBAT104 TQM Library Management System
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PYTHON="$DIR/.venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

MODE="${1:---web}"

if [ "$MODE" = "--desktop" ]; then
    echo "=========================================================================="
    echo " Starting BBAT104 Library Management System (Desktop GUI)..."
    echo "=========================================================================="
    if ! "$PYTHON" -c "import tkinter" &>/dev/null; then
        echo " [!] NOTICE: 'python3-tk' is not installed."
        echo " Falling back to browser web application on http://localhost:5000"
        exec "$PYTHON" "$DIR/web_app.py"
    else
        exec "$PYTHON" "$DIR/app.py" "${@:2}"
    fi
else
    echo "=========================================================================="
    echo " Starting BBAT104 Library Management System (Web Application)..."
    echo " Accessible in web browser at: http://localhost:5000"
    echo "=========================================================================="
    exec "$PYTHON" "$DIR/web_app.py"
fi
