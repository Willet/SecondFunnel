# import all tasks setup in folder
from fabfile import *

# set default user to be ec2-user for remote executions
env.user = 'ec2-user'
