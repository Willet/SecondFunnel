#!/bin/bash -ex
cd $WORKSPACE
virtualenv -q ve
source ./ve/bin/activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py jenkins