# Scrapy

Scrapy is neat. It makes it possible to decouple different aspects of scraping
(e.g. downloading image from parsing page, processing from downloading etc.)
and is fairly flexible (even if it could use some improvement) as compared to
our existing setup. Plus, its faster!

## Usage

Most of what is possible can be revealed by calling the `scrapy` command with no
 arguments, however, the most common commands have been outlined below.

*Note: All commands should be run from the root of the project,
as you would do with `manage.py`*

### Starting a scrape

    scrapy crawl <scraper_name> [-a <spider-argument>=<spider-value>] [-t <output format> -o <filename>]`

- Spider arguments are passed to their `__init__` method as `kwargs`
- Details on default exporting formats can be found [here](http://doc.scrapy.org/en/latest/topics/feed-exports.html#feed-exporters-base).

### Run a contract

    scrapy check [<scraper_name>] -s SENTRY_SIGNALS=[]

- Small problem when `scraper_name` is not provided: occasionally Ghostdriver
 throws an exception...
- The `-s` flag lets you override project settings,
and we override `SENTRY_SIGNALS` as it causes problems with contracts
- More information on contracts can be found in the [Scrapy docs](http://doc.scrapy.org/en/latest/topics/contracts.html).

## Documentation

Most of the scraping is build off of ordinary Scrapy or the Scrapy source
code itself.

- **Scrapy Documentation**: http://doc.scrapy.org/en/latest/

In order to scrape JavaScript, we leverage scrapy-webdriver which itself uses
PhantomJS. Assuming that PhantomJS is installed, everything should just work.

- **`scrapy-webdriver` Project**: https://github.com/brandicted/scrapy-webdriver/

## Performance
At the moment, the slowest part of scraping is likely persistence and image
processing, namely because it does these two things serially, and one-by-one.

If it is of interest to do scraping more quickly, it would be best to have
the scraper focus on scraping, return a `jsonlines` feed,
then have another script iterate over all lines and handle the batch
insertion, image processing, and association.

Further, some performance is likely to be gained by using the native
`CrawlSpider` instead of `WebDriverCrawlSpider` to avoid the overhead of
using `PhantomJS`. This, however, would mean that we wouldn't have any means
to scrape JavaScript in the scraper, which may require more cleverness when
writing spiders.

## (F?)AQ
### Why do I get `ScrapyDeprecationWarning: HttpDownloadHandler is deprecated`?
It is a problem with `scrapy-webdriver`. It sets up a `FALLBACK_HANDLER` in
`scrapy_webdriver.download` which imports the deprecated
`HttpDownloadHandler`. Since it doesn't look in settings for an alternate
value, this warning is hard to get rid of. **Don't worry about it**.

### Why do I get `DeprecationWarning: the sets module is deprecated`?
**Don't worry about it**. It is from deep in the Twisted framework code,
and is not something we can fix.
