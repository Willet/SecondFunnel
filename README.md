SecondFunnel
============
SecondFunnel is a collection of related applications for converting browser
into shoppers. Additional information on the project can be found [in the
wiki](https://github.com/Willet/SecondFunnel/wiki).

Installation
------------
Detailed instructions can be found in [the SecondFunnel wiki](https://github.com/Willet/SecondFunnel/wiki/Environment-Setup), but a quick installation can
 be done by doing the following:

1. Set up a virtual environment using `virtualenv` or `virtualenvwrapper`
2. Install MySQL
3. Install python dependencies: `pip install -r requirements.txt`

Then, getting started is as easy as creating a `local_settings.py` file in the
`secondfunnel` folder with the following contents...

    DATABASES = {
        'default': {
            'ENGINE'  : 'django.db.backends.sqlite3',
            'NAME'    : 'test.sqlite',
            'USER'    : '',
            'PASSWORD': '',
            'HOST'    : '',
            'PORT'    : '',
        }
    }

    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

...and run the following command...

    python manage.py runserver

And voila! Again, full details are available [in the wiki](https://github.com/Willet/SecondFunnel/wiki/Environment-Setup)

Structure
---------
The SecondFunnel project is broken into different folders for the application.

- `scripts`: Python and Bash scripts for deployment and/or utility
- `secondfunnel`: Where settings and site-wide URLs are recorded
- `apps`: Applications and common code
    - `analytics`: Our analytics framework for tracking users
    - `assets`: Common models and functions used across applications
    - `pinpoint`: A dynamic landing page

Documentation
-------------
The SecondFunnel project uses Epydocs for documenting code.  For procedural and development guidelines consult the wiki [here](https://github.com/Willet/SecondFunnel/wiki).  Documentation for the code can be generated locally using epydocs; steps for running epydocs can be found [here](https://github.com/Willet/SecondFunnel/wiki/Epydoc).


The SecondFunnel project has a few primary components:
* [**IntentRank**](.#intentRank):  The backbone of the SecondFunnel project; provides an API for requesting and serving content. 
* [**Pages**](.#pages): The front-end javascript; manages how content is arranged on the pinpoint pages, services API queries to IntentRank and handles interactions between the user and the pinpoint pages.
* [**Analytics**](.#analytics): An analytics framework for tracking how users interact with the pinpoint pages.


#### <a id="IntentRank"></a>IntentRank
[Read more here.](https://github.com/Willet/IntentRank)


#### <a id="Pages"></a> Pages
Pages is the front-end javascript of the SecondFunnel project that manages how content is displayed on the Pinpoint pages.  In addition, it manages how users are able to interact with those pages; by clicking, scrolling, social media, etc.  It services API calls to IntentRank to fetch content based on a myriad of factors dependent on how the user is currently interacting with the page.  It makes use of the popular [Masonry Library](https://github.com/desandro/masonry) to render content in a cascading infinite scroll grid.  As users interact with the page, it also records analytic data.


#### <a id="Analytics"></a> Analytics
Analytics is our framework for tracking how users interact with the pinpoint pages.  This provides information for both the store owner and us about how users are using our pages so that we can better tailor our pages to increase traffic and promote purchases.  Similarily, it provides the store owner with insight into how effective the pinpoint pages are for their business.


License
-------
Copyright 2012-2013, Willet Inc.
