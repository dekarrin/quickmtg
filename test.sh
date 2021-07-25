#!/bin/bash

# need to execute everything from this directory
cd "$(dirname "$0")"

# parse args
PARAMS=""
while (( "$#" )); do
  case "$1" in
    -t|--test)
      test_name="$2"
      shift 2
      ;;
	-h|--help)
	  echo "usage: $0 [<flags>]"
	  echo "Runs tests. Only tests currently is whether it runs without error,"
	  echo "not actually validate the output. Options are available to select"
      echo "specific tests."
      echo ''
	  echo "Flags:"
	  echo '  -h, --help                      Show this help and exit'
	  echo '  -t, --test "test_name"          Give the test to execute. If not'
      echo '                                  given, all tests are glu88in'
      echo '                                  selected, which could 8e'
      echo '                                  undesiria8u88le! 8ut usually is'
      echo '                                  8est to make sure they are run at'
      echo '                                  least once, glubglub. oh ya! here'
      echo '                                  are the tests u can pick, nyaaa:'
      echo '                                   * onebinder'
      echo '                                   * smallbinder'
      echo '                                   * medbinder'
      echo ''
	  echo '      --                          Flag end marker; no flags after'
      echo '                                  this will be parsed. you could use'
      echo '                                  it in case you have args that look'
      echo '                                  like options, glu8!'
	  exit 0
	  ;;
    --) # end argument parsing
      shift
      break
      ;;
    -*|--*=) # unsupported flags
      echo "Error: Unsupported flag $1" >&2
	  echo "Invoke with -h or --help for help" >&2
      exit 1
      ;;
    *) # preserve positional arguments
      PARAMS="$PARAMS $1"
      shift
      ;;
  esac
done
# set positional arguments in their proper place
eval set -- "$PARAMS"

echo "Placing all output from tests in test_output/ directory..."
mkdir test_output 2>/dev/null

echo "Attempting to generate binder views..."
if [ -z "$test_name" -o "$test_name" = "onebinder" ]; then
  set -x
  ./qmtg view create testfiles/one_inventory.txt test_output/one_binder || exit $ERR_TEST
  set +x
fi
if [ -z "$test_name" -o "$test_name" = "smallbinder" ]; then
  set -x
  ./qmtg view create testfiles/small_inventory.txt test_output/small_binder || exit $ERR_TEST
  set +x
fi
if [ -z "$test_name" -o "$test_name" = "medbinder" ]; then
  set -x
  ./qmtg view create testfiles/medium_inventory.txt test_output/medium_binder || exit $ERR_TEST
  set +x
fi
