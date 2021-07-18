#!/bin/bash

echo "Activating virtual environment..."
. .venv/Scripts/activate || exit 1

echo "Placing all output from tests in test_output/ directory..."
mkdir test_output 2>/dev/null

echo "Attempting to generate binder view..."
python qmtg.py view create testfiles/small-inventory.txt test_output/small-binder || exit 1
