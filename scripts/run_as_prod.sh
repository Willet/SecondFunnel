#!/bin/bash
# Runs any command (the args) in the virtualenv environment where this script resides.
#
# use: /path/to/env_run.sh <command>
# e.g.: /path/to/env_run.sh python main.py --arg-one --arg-two

export DJANGO_SETTINGS_MODULE="secondfunnel.settings.production"
export RDS_PORT="3306"
export RDS_USERNAME="ebroot"
export RDS_PASSWORD="braTh9hU"
export RDS_DB_NAME="ebdb"
export RDS_HOSTNAME="db.secondfunnel.com"

ACTIVATE_PATH=../bin/activate

source ${ACTIVATE_PATH}
exec $@