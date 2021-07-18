quickmtg
========

A set of python scripts to organize, sort, and view Magic: The Gathering
libraries to patch some of the difficulties of using tappedout.net. Makes binder
views from lists, in HTML format.

A single entry point for the scripts, `qmtg.py`, is provided.

### Requirements
Python 3 must be installed to execute this script. This project was tested with
Python 3.7, but other versions of Python 3.x may also be compatible.

### Download/Install
To download and install these scripts, first clone this repository:

`git clone git@github.com:dekarrin/quickmtg.git`

Enter the root of your repository clone:

`cd quickmtg`

Set up a virtual environment to run quickmtg in:

`python -m venv .venv`

Activate the virtual environment:

`. .venv/bin/activate` (or `. .venv/Scripts/activate` on windows)

. Then go to the root of your
repository clone and set up a virtual environment by doing `python -m venv
.venv`.

### Run
To run, do `python qmtg.py` in the repo root. Help can be seen by doing `python
qmtg.py --help`.

### Test
Tests are run by doing `./test.sh`. You need a virtual environment named `.venv`
located in the current working directory for this to work.