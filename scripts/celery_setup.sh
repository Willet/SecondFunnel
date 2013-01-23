#!/bin/sh -e
# ============================================
#  celery_setup - Runs on the leader EC2 instance, creates celery user/group,
#   creates required dirs and symlinks up things for celeryd and celerybeat daemons to work.
# ============================================

# Make an unprivileged, non-password-enabled user and group to run celery
# AWS Beanstalk script runners are using 'set -e'
# which we don't want in this particular instance. Disabled it

# make a spot for the logs and the pid files
mkdir -p /var/log/celery
mkdir -p /var/run/celery/bin
mkdir -p /var/run/celery/config
echo "Ensured /var/log/celery, /var/run/celery/bin and /var/run/celery/config exist"

# set ownership of log/run dirs
chown celery:celery /var/log/celery
chown -R celery:celery /var/run/celery
echo "Set ownership for log and pid dirs"

# Symlink config files
# CELERY COMMON
if [ -h "/var/run/celery/config/celerycommon" ]
then
    rm /var/run/celery/config/celerycommon
    echo "Deleted existing symlink for celerycommon config."
fi

ln -s `pwd`/secondfunnel/settings/celerycommon /var/run/celery/config/celerycommon
echo "Created symlink for celerycommon config"

# CELERYD
if [ -h "/var/run/celery/config/celeryd" ]
then
    rm /var/run/celery/config/celeryd
    echo "Deleted existing symlink for celeryd config."
fi

ln -s `pwd`/secondfunnel/settings/celeryd /var/run/celery/config/celeryd
echo "Created symlink for celeryd config"

# CELERYBEAT
if [ -h "/var/run/celery/config/celerybeat" ]
then
    rm /var/run/celery/config/celerybeat
    echo "Deleted existing symlink for celerybeat config."
fi

ln -s `pwd`/secondfunnel/settings/celerybeat /var/run/celery/config/celerybeat
echo "Created symlink for celerybeat config"


# Daemon celeryd
if [ -h "/var/run/celery/bin/celeryd" ]
then
    rm /var/run/celery/bin/celeryd
    echo "Deleted existing symlink for celeryd daemon script."
fi

ln -s `pwd`/scripts/celeryd /var/run/celery/bin/celeryd
chmod +x /var/run/celery/bin/celeryd
echo "Created symlink for celeryd daemon script"

# Daemon celerybeat
if [ -h "/var/run/celery/bin/celerybeat" ]
then
    rm /var/run/celery/bin/celerybeat
    echo "Deleted existing symlink for celerybeat daemon script."
fi

ln -s `pwd`/scripts/celerybeat /var/run/celery/bin/celerybeat
chmod +x /var/run/celery/bin/celerybeat
echo "Created symlink for celerybeat daemon script"

echo "Done preliminary celery setup."
exit 0
