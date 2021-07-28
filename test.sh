#!/bin/bash

# need to execute everything from this directory
caller_dir="$(pwd)"
cd "$(dirname "$0")"

output_dir="test_output"
qmtg_home_set=

# parse args
PARAMS=""
while (( "$#" )); do
  case "$1" in
    -m|--qmtg-home)
      if [[ "$2" = /* ]]
      then
        qmtg_home="$2"
      else
        qmtg_home="$caller_dir/$2"
      fi
      qmtg_home_set=1
      shift 2
      ;;
    -o|--output_dir)
      if [[ "$2" = /* ]]
      then
        output_dir="$2"
      else
        output_dir="$caller_dir/$2"
      fi
      shift 2
      ;;
    -t|--test)
      test_name="$2"
      shift 2
      ;;
    -h|--help)
      echo "usage: $0 [<flags>]"
      echo "Runs tests. Only tests currently is whether it runs without error,"
      echo "not actually validate the output. Options are available to select"
      echo "specific tests and control outputs."
      echo ''
      echo "Flags:"
      echo '  -h, --help                      Show this help and exit'
      echo ''
      echo '  -t, --test TEST_NAME            Give the test to execute. If not'
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
      echo '  -o, --output-dir DIR            Give a different output directory'
      echo '                                  from the default value of'
      echo '                                  "test_output".'
      echo ''
      echo '  -m, --qmtg-home DIR             Set a directory to use as the QMTG'
      echo '                                  homedir. The QMTG store in this'
      echo '                                  location will be deleted as part'
      echo '                                  of testing, and the scryfall cache'
      echo '                                  may also 8e manipul8ed. Default'
      echo '                                  value is the directory ".qmtg"'
      echo '                                  located in the output dir.'
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

[ -z "$qmtg_home_set" ] && qmtg_home="$output_dir/.qmtg"

echo "Placing all output from tests in directory '$output_dir'..."
mkdir "$output_dir" 2>/dev/null

echo "Setting/creating QMTG homedir at '$qmtg_home...'"
mkdir "$qmtg_home" 2>/dev/null

echo "Reseting QMTG store before running tests..."
rm -rf "$qmtg_home/qmtg.p"

echo "Attempting to generate binder views..."
if [ -z "$test_name" -o "$test_name" = "onebinder" ]; then
  set -x
  ./qmtg -m "$qmtg_home" binder create \
    testfiles/one_inventory.txt \
    "$output_dir/one_binder" \
    -n "One Binder" \
    || exit $ERR_TEST
  set +x
fi
if [ -z "$test_name" -o "$test_name" = "smallbinder" ]; then
  set -x
  ./qmtg -m "$qmtg_home" binder create \
    testfiles/small_inventory.txt \
    "$output_dir/small_binder" \
    -n "Small Binder"  \
    || exit $ERR_TEST
  set +x
fi
if [ -z "$test_name" -o "$test_name" = "medbinder" ]; then
  set -x
  ./qmtg -m "$qmtg_home" binder create \
    testfiles/medium_inventory.txt \
    "$output_dir/medium_binder" \
    -n "Med Binder" \
    || exit $ERR_TEST
  set +x
fi
