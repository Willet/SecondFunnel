__author__ = 'Willet Inc'
# http://stackoverflow.com/questions/8578223/how-to-disable-south-debug-logging-in-django
# shut up south
import logging
south_logger=logging.getLogger('south')
south_logger.setLevel(logging.INFO)

