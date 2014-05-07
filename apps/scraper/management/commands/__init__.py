__doc__ = """Scrapers

# The scraper command

You should not run the scraper command locally. Instead, run the scraper on
test or production:

./manage.py scraper
    Run all scrapers for all stores.

./manage.py scraper --store-id 123
    Run all scrapers for the store with id 123.

./manage.py scraper --store-id 123 --url http://gap.com
    Pick a scraper for that url, and add whatever products/content
    to the store with id 123.
"""
