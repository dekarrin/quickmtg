#!/bin/bash

# need to execute everything from this directory
cd "$(dirname "$0")"

echo "Placing all output from tests in test_output/ directory..."
mkdir test_output 2>/dev/null

echo "Attempting to generate binder view..."
./qmtg view create testfiles/small_inventory.txt test_output/small_binder || exit $ERR_TEST
