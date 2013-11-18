SecondFunnel
============  
SecondFunnel is the backend application that powers the [CampaignManager](Willet/CampaignManager). It mostly serves as a facade for dealing with composite actions that the front-end can't handle, and to make the API appear to come from one location (which also allows us to handle authentication / authorization from one location).

Setup
-----  
1. `git clone` the repository
2. `pip install -r requirements/dev.txt`
3. `python src/manage.py syncdb`
4. `python src/manage.py runserver`

Structure
---------  
Top-level directories indicate project-level files: files that are important to the setup of the project.

- `.ebextensions/`: For use with deployment; mostly sets up python environment details. [Further details here.](http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/customize-containers.html)
- `.elasticbeanstalk/`: For use with deployment; mostly for use with command line deployment. [Further details here.](http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create_deploy_Python_django.html)
- `requirements/`: Lists of python requirements from `pip freeze` for different environments
- `requirements.txt`: The file used by Elastic Beanstalk to determine which python packages to install. Mostly just references `requirements/production.txt`.
- `ssh_keys`: List of public ssh-keys that are able to access EC2 instances

The remaining directories (i.e. those in `src`) follow a fairly standard Django setup.

- `apps/api/`: Code to handle API facade, authentication, and authorization
- `apps/contentgraph/`: Code to handle any contentgraph proxying
- `apps/intentrank/`: Code to handle any intentrank proxying (mostly for page generation)
- `apps/page_generator/`: Code to handle page generation and saving files to S3
- `apps/utils/`: Any code used by multiple apps
- `secondfunnel/`: Standard django project folder. Contains settings and wsgi files.
