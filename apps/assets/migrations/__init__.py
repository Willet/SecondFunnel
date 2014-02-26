"""
# Rebuilding migrations: http://stackoverflow.com/a/14508663/1558430
rm apps/assets/migrations/*
python manage.py schemamigration assets --initial
python manage.py migrate assets 0001 --fake  --delete-ghost-migrations
"""
