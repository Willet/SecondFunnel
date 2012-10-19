SecondFunnel
------------
SecondFunnel is a collection of related applications for converting browser
into shoppers. Additional information on the project can be found [in the
wiki](https://github.com/Willet/SecondFunnel/wiki).

Installation
============
Detailed instructions can be found in [the SecondFunnel wiki](https://github
.com/Willet/SecondFunnel/wiki),
but a quick installation can be done by doing the following:

# Set up a virtual environment using `virtualenv` or `virtualenvwrapper`
# Install MySQL
# Install python dependencies: `pip install -r requirements.txt`

Then, getting started is as easy as creating a `local_settings.py` file and
running the following command:

    python manage.py runserver

Structure
=========
The SecondFunnel project is broken into different folders for the application.

- `scripts`: ???
- `secondfunnel`: Where settings and site-wide URLs are recorded
- `apps`: Applications and common code
    - `analytics`: Our analytics framework for tracking users
    - `assets`: Common models and functions used across applications
    - `pinpoint`: A dynamic landing page

Documentation
=============
Coming Soon

License
=======
Copyright 2012, Willet Inc.