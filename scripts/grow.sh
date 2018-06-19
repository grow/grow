#!/bin/bash

function realdirname() {
  # a cross platform version of $(dirname $(realpath $1))
  # OS X does not have /usr/bin/realpath
  python -c 'import sys, os.path; print(os.path.dirname(os.path.realpath(sys.argv[1])))' "$1"
}

HERE="$(realdirname "$0")"

# Find the virtual env for grow.
PIP_ENV=$(
  cd "${HERE}/../" && pipenv --venv;
)

# Activate the virtual environment and run the command.
(
  source "${PIP_ENV}/bin/activate";
  "${HERE}/../bin/grow" ${@};
  deactivate;
)
