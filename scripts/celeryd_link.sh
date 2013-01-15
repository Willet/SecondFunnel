#!/bin/sh -e
# ============================================
#  celeryd_link - Runs on the leader EC2 instance and links up things for celeryd daemon to work.
# ============================================

# Configuration file
if [ -h "/etc/default/celeryd" ]
then
    rm /etc/default/celeryd
    echo "Deleted existing symlink for celery config."
fi

ln -s `pwd`/secondfunnel/settings/celeryd /etc/default/celeryd
echo "Created symlink for celery config"


# Init script
if [ -h "/etc/init.d/celeryd" ]
then
    rm /etc/init.d/celeryd
    echo "Deleted existing symlink for celery init script."
fi

ln -s `pwd`/scripts/celeryd /etc/init.d/celeryd
chmod +x /etc/init.d/celeryd
echo "Created symlink for celery init script"


# Beat script
if [ -h "/etc/init.d/celerybeat" ]
then
    rm /etc/init.d/celerybeat
    echo "Deleted existing symlink for celerybeat script."
fi

ln -s `pwd`/scripts/celerybeat /etc/init.d/celerybeat
chmod +x /etc/init.d/celerybeat
echo "Created symlink for celerybeat script"


# Make an unprivileged, non-password-enabled user and group to run celery
# AWS Beanstalk script runners are using 'set -e'
# which we don't want in this particular instance. Disabled it
set +e
useradd -M celery
useradd_status=$?
if [ useradd_status != 0 ]
then
    echo "useradd exited with an error code: '$useradd_status'"
else
    echo "Created unprivileged user 'celery'"
fi
# Reenable it
set -e

# make a spot for the logs and the pid files
mkdir -p /var/log/celery
mkdir -p /var/run/celery
echo "Ensured /var/log/celery and /var/run/celery exist"

# set ownership of log/pid
chown celery:celery /var/log/celery
chown celery:celery /var/run/celery
echo "Set ownership for log and pid dirs"

echo "Done preliminary celery setup."
exit 0