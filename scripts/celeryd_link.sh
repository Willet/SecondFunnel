#!/bin/sh -e
# ============================================
#  celeryd_link - Runs on the leader EC2 instance and links up things for celeryd daemon to work.
# ============================================

# Configuration file
ln -s `pwd`/secondfunnel/settings/celeryd /etc/default/celeryd
if [ "$?" -eq "1" ]
then
    echo "celeryd config symlink already exists."
fi

# Init script
ln -s `pwd`/scripts/celeryd /etc/init.d/celeryd
if [ "$?" -eq "1" ]
then
    echo "celeryd init script symlink already exists."
fi

# The init script needs to be executable:
chmod +x /etc/init.d/celeryd

# Make an unprivileged, non-password-enabled user and group to run celery
useradd celery
if [ "$?" -ne "0" ]
then
    if [ "$?" -ne "9" ]
    then
        echo "useradd exited with an error other than duplicate user. useradd exit code: '$?'"
        exit 1
    fi
fi

# make a spot for the logs and the pid files
mkdir -p /var/log/celery
mkdir -p /var/run/celery

# set ownership of log/pid
chown celery:celery /var/log/celery
chown celery:celery /var/run/celery

exit 0