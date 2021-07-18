#!/bin/bash

ERR_VENV=1
ERR_TEST=2

[ -d .venv ] || { echo "No virtual environment .venv found. Create it and install dependencies before running tests" >&2 ; exit $ERR_VENV ; }
echo "Activating virtual environment..."

if [ -d .venv/bin ]
then
    . .venv/bin/activate || exit $ERR_VENV
else
    . .venv/Scripts/activate || exit $ERR_VENV
fi

echo "Placing all output from tests in test_output/ directory..."
mkdir test_output 2>/dev/null

echo "Attempting to generate binder view..."
python qmtg.py view create testfiles/small-inventory.txt test_output/small-binder || exit $ERR_TEST
