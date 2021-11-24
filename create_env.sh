#!/usr/bin/env bash

SCRIPT_DIR=$(cd $(dirname $0); pwd)
cd $SCRIPT_DIR

if [ "$1" = "" ]; then
    PYTHON="$(which python3)"
else
    PYTHON="$1"
fi

if [ "${VIRTUAL_ENV}" != "" ]; then
    echo "! You are in a virtualenv: ${VIRTUAL_ENV}"
    echo "! Use deactivate first, and retry"
    exit 1
fi

VENV='.env'
rm -rf "${VENV}"

echo "Creating virtualenv with ${PYTHON}"
virtualenv --clear "${VENV}" --python="${PYTHON}"
source "${VENV}/bin/activate"

"${VENV}"/bin/python -m pip install --upgrade pip
"${VENV}"/bin/python -m pip install -r requirements.txt

echo -e "\n* Finished, now you should do:"
echo -e "source ${VENV}/bin/activate"
