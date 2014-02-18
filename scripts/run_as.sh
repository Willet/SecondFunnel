#!/bin/bash
# Runs any command (the args) in the virtualenv environment where this script resides.
#
# use: /path/to/env_run.sh <command>
# e.g.: /path/to/env_run.sh python main.py --arg-one --arg-two

E_BADARGS=85

export RDS_PORT="3306"
export RDS_DB_NAME="sfdb"
export RDS_USERNAME="sf"

if [ "$1" = "test" ]; then
    echo "TEST"
    export DJANGO_SETTINGS_MODULE="secondfunnel.settings.test"
    export RDS_PASSWORD="postgres"
    export RDS_HOSTNAME="aa1fq6h81nzaxoc.c9ahaxgbbpcf.us-west-2.rds.amazonaws.com"

elif [ "$1" = "production" ]; then
    echo "PROD"
    export DJANGO_SETTINGS_MODULE="secondfunnel.settings.production"
    export RDS_PASSWORD="postgres"
    export RDS_HOSTNAME="aa1fq6h81nzaxoc.c9ahaxgbbpcf.us-west-2.rds.amazonaws.com"
else
    echo "Must pass in environment name. 'test' or 'production'"
    exit $E_BADARGS
fi

ACTIVATE_PATH=../bin/activate

source ${ACTIVATE_PATH}

execlist=()
counter=0
for arg in "$@"; do

    # skip the first argument, which is environment type
    if [ $counter -gt 0 ]; then
        execlist+=("$arg")
    fi
    counter=$[counter + 1]

done
exec ${execlist[@]}

exit 0
