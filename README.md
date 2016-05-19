SecondFunnel is a collection of related applications for converting browser
into shoppers. Additional information on the project can be found
[in the wiki](https://github.com/Willet/SecondFunnel/wiki).

Installation
------------

See the super useful [Setup Environment wiki](https://github.com/Willet/SecondFunnel/wiki/Environment-Setup).

Structure
---------
The SecondFunnel project is broken into different folders for the application.

- `ansible`: Deployment and Provisioning of server code
- `secondfunnel`: Where settings and site-wide URLs are recorded
- `apps`: Applications and common code
    - `api2`: The base API used by various of our front-end services
    - `assets`: Common models and functions used across applications
    - `dashboard`: A dashboard to manage & review analytics for pages
    - `imageservice`: All management of images across servers and services
    - `intentrank`: An algorithm for ordering content in pages
    - `light`: The front-end pages
    - `scrapy`: A scraper to update product & content from websites & datafeeds
    - `tracking`: A web tracking pixel loader
    - `utils`: A whole whack of utilities
- `scripts + fabfile`: Python and Bash scripts for deployment and/or utility

Documentation
-------------

The SecondFunnel project has a few primary components:
* [**API2**](.#-api): The backbone of the SecondFunnel project; provides an API for requesting and serving content.
* [**Light (Pages)**](.#-pages): The front-end javascript; manages how content is arranged on the discovery page or ad, services API queries to IntentRank and handles interactions between the user and the pages.
* [**IntentRank**](.#intentrank):  Provides Pages with products and content (in the form of "Tiles").
* [**Scrapy**](.#-scrapy): The system for keeping products and content continually updated.

#### <a id="API2"></a>API2
The SecondFunnel API2 is a RESTful list of resources, for internal use only.  Currently it is primarily used by the `dashboard`


#### <a id="IntentRank"></a>IntentRank
IntentRank is the main recommendation system, and controls the output of the feed (ordering, and what tiles (content/products) are shown).
It is the foundation for analyzing users and determining what the user is most interested in based on various parameters.


#### <a id="Pages"></a>Light (Pages)
Pages is the front-end javascript of the SecondFunnel project that manages how content is displayed on the Light pages.
In addition, it manages how users are able to interact with those pages; by clicking, scrolling, social media, etc.
It API calls out to IntentRank to fetch tiles based on a myriad of factors dependent on how the user is currently interacting with the page.
It makes use of the popular [Masonry Library](https://github.com/desandro/masonry) to render content in a cascading infinite scroll grid.
As users interact with the page, it also records analytic data.


#### <a id="Scrapy"></a> Scrapy
Scrapy is our system for keep pages updated.  There are two types of updates: datafeed updates and page scraping updates.  Datafeed updates are fast, but usually some of the data (pricing & availability) is 24 hours out of date and the pictures are limited and low-res.  Page scraping updates are *really* slow, but provide great data and images.


License
-------
Copyright 2012-2016, Willet Inc.
