#!/bin/sh
export RDS_HOSTNAME="{{database.hostname}}"
export RDS_PORT="{{database.port}}"
export RDS_DB_NAME="{{database.db_name}}"
export RDS_USERNAME="{{database.username}}"
export RDS_PASSWORD="{{database.password}}"

export DJANGO_SETTINGS_MODULE="{{django_settings_module}}"

export AWS_ACCESS_KEY_ID="{{aws_access_key_id}}"
export AWS_SECRET_KEY="{{aws_secret_key}}"

export PATH=$PATH:$EC2_HOME
