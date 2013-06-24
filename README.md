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
Documentation for the SecondFunnel project can be found ..... **COMING SOON**

License
-------
Copyright 2012, Willet Inc.