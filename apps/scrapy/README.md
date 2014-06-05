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
