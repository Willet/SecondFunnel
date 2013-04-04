#!/bin/bash
# Runs any command (the args) in the virtualenv environment where this script resides.
#
# use: /path/to/env_run.sh <command>
# e.g.: /path/to/env_run.sh python main.py --arg-one --arg-two

WORKING_DIR=../
ACTIVATE_PATH=../bin/activate
ACTIVATE_PROD=scripts/enable_prod
MY_PATH="`dirname \"$0\"`"              # relative
MY_PATH="`( cd \"$MY_PATH\" && pwd )`"  # absolutized and normalized

cd ${MY_PATH}
cd ${WORKING_DIR}
source ${ACTIVATE_PROD}
source ${ACTIVATE_PATH}
exec $@