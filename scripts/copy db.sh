#!/bin/sh

# Script is used for copying between two databases on RDS
# for some reason you cannot use pg_restore

# PRODUCTION
#SRC_HOST=aae9bptwm2fn7s.c9ahaxgbbpcf.us-west-2.rds.amazonaws.com
#DEST_HOST=secondfunnel-production-db.c9ahaxgbbpcf.us-west-2.rds.amazonaws.com
#DEST_PASS=4rjSR4EpgBcbvSP6

# STAGE
SRC_HOST=aae9bptwm2fn7s.c9ahaxgbbpcf.us-west-2.rds.amazonaws.com
DEST_HOST=secondfunnel-stage-db.c9ahaxgbbpcf.us-west-2.rds.amazonaws.com
DEST_PASS=8tJg66zMcZIRfkTu

PGPASSWORD=postgres pg_dump -h $SRC_HOST -s -U sf -d ebdb > db_dump.sql
perl -p -i -e 's/^(.*)EXTENSION/--$1EXTENSION/g' db_dump.sql # remove stuff from db_production.sql (extensions, that are not modifiable by us on RDS)
perl -p -i -e 's/TO sf/TO willet/g' db_dump.sql  # replace "TO sf" to "TO new_user" in db_production.sql
perl -p -i -e 's/FROM sf/FROM willet/g' db_dump.sql  # replace "TO sf" to "TO new_user" in db_production.sql
PGPASSWORD=$DEST_PASS psql --host=$DEST_HOST --username=willet --dbname=sfdb -1 -f db_dump.sql

## now for the data
PGPASSWORD=postgres pg_dump -h $SRC_HOST --data-only -U sf -d ebdb -W > db_dump.sql
perl -p -i -e 's/TO sf/TO willet/g' db_dump.sql  # replace "TO sf" to "TO new_user" in db_production.sql
perl -p -i -e 's/FROM sf/FROM willet/g' db_dump.sql  # replace "TO sf" to "TO new_user" in db_production.sql
PGPASSWORD=$DEST_PASS psql --host=$DEST_HOST --username=willet --dbname=sfdb -1 -f db_dump.sql
