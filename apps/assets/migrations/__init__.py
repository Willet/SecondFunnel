"""
# Rebuilding migrations: http://stackoverflow.com/a/14508663/1558430
rm apps/assets/migrations/*
python manage.py schemamigration assets --initial
python manage.py migrate assets 0001 --fake  --delete-ghost-migrations
# if problems persist, run the following two:
python manage.py migrate assets zero
python manage.py migrate
"""
