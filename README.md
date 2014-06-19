![image](http://www.secondfunnel.com/wp-content/uploads/2013/03/sf_logo_1x.png)

SecondFunnel is a collection of related applications for converting browser
into shoppers. Additional information on the project can be found
[in the wiki](https://github.com/Willet/SecondFunnel/wiki).

Installation
------------

1. Download and Install [Vagrant](http://www.vagrantup.com/)
2. Download and Install [VirtualBox](https://www.virtualbox.org/)
2. Download and Install [pip](http://pip.readthedocs.org)
```
    wget https://bootstrap.pypa.io/get-pip.py
    python get-pip.py
```
3. Download and Install [Ansible](http://docs.ansible.com/intro_installation.html)
```
    pip install ansible
```
4. Download and Install [Node](http://nodejs.org)
5. Install various dev utils and libraries
```
    npm install -g gulp cult coffee-script bower
```
6. Add `export PATH=node_modules/.bin:$PATH` to your `.bashrc/.zshrc`
7. Build a local vagrant instance (this may take a while to provision, feel free to walk away, have a coffee)

    `vagrant up`
    `honcho start gulp`

And voila! The server should be available [here](http://localhost:8000) ; note you should be redirect to www.secondfunnel.com

An NGINX server (exactly like production) is running inside the vagrant box, and auto-reloading of code should work seamlessly.

gulp runs on your local box and monitors light's assets and recompiles + reloads your browser if necessary.

Structure
---------
The SecondFunnel project is broken into different folders for the application.

- `ansible`: Deployment and Provisioning of server code
- `scripts + fabfile`: Python and Bash scripts for deployment and/or utility
- `secondfunnel`: Where settings and site-wide URLs are recorded
- `apps`: Applications and common code
    - `analytics`: Our analytics framework for tracking users
    - `assets`: Common models and functions used across applications
    - `pinpoint`: (deprecated) Th old landing pages, and feeds
    - `dashboard`: A dashboard to show all analytics gathered to the end user
    - `api`: The base API used by various of our front-end services
    - `intentrank`: A system used for ordering content in feeds for our components
    - `scrapy`: A scraper framework that we use to grab product & content from websites
    - `light`: A replacement for pinpoint, and future components

Documentation
-------------
The SecondFunnel project uses Epydocs for documenting code.  For procedural and development guidelines consult the wiki [here](https://github.com/Willet/SecondFunnel/wiki).  Documentation for the code can be generated locally using epydocs; steps for running epydocs can be found [here](https://github.com/Willet/SecondFunnel/wiki/Epydoc).


The SecondFunnel project has a few primary components:
* [**API**](.#-api): The backbone of the SecondFunnel project; provides an API for requesting and serving content.
* [**Pinpoint (Pages)**](.#-pages): The front-end javascript; manages how content is arranged on the pinpoint pages, services API queries to IntentRank and handles interactions between the user and the pinpoint pages.
* [**IntentRank**](.#intentrank):  Provides Pages with products and content (in the form of "Tiles").
* [**Analytics**](.#-analytics): An analytics framework for tracking how users interact with the pinpoint pages.

#### <a id="API"></a>API
The SecondFunnel API is a tastypie list of resources for internal use only.


#### <a id="IntentRank"></a>IntentRank
IntentRank is the main recommendation system, and controls the output of the feed (ordering, and what tiles (content/products) are shown).
It will become the foundation of analyzing users and determining what the user is most interested in based on various parameters.


#### <a id="Pages"></a> Pages
Pages is the front-end javascript of the SecondFunnel project that manages how content is displayed on the Light pages.
In addition, it manages how users are able to interact with those pages; by clicking, scrolling, social media, etc.
It API calls out to IntentRank to fetch tiles based on a myriad of factors dependent on how the user is currently interacting with the page.
It makes use of the popular [Masonry Library](https://github.com/desandro/masonry) to render content in a cascading infinite scroll grid.
As users interact with the page, it also records analytic data.


#### <a id="Analytics"></a> Analytics
Analytics is our framework for tracking how users interact with the pinpoint pages.  This provides information for both the store owner and us about how users are using our pages so that we can better tailor our pages to increase traffic and promote purchases.  Similarily, it provides the store owner with insight into how effective the pinpoint pages are for their business.


License
-------
Copyright 2012-2014, Willet Inc.

[ ![Codeship Status for Willet/SecondFunnel](https://codeship.io/projects/a2949e90-0588-0132-6e2b-32730fef382b/status)](https://codeship.io/projects/30913)
