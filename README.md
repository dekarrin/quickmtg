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

```bash
git clone git@github.com:dekarrin/quickmtg.git
```

Enter the root of your repository clone:

```bash
cd quickmtg
```

Set up a virtual environment to run quickmtg in:

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
. .venv/bin/activate`

# OR on windows, do this instead:
. .venv/Scripts/activate`
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

And you are good to go! You will need to be in this directory to execute qmtg.py
directly, so if you exit this dir, you will need to return to it before running
them and ensure the virtual environment is activated.

Alternatively, you can just execute the `qmtg` shell script, which can be
executed from any location and takes the same parameters as python qmtg. The
rest of these instructions just use that method.

### Run
To run, execute `qmtg` in the repo root. Help can be seen by doing
`qmtg --help`.

### Test
Tests are run by executing `test.sh` in the repo root.
