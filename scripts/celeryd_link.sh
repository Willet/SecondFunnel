#!/bin/sh -e
# ============================================
#  celeryd_link - Runs on the leader EC2 instance and links up things for celeryd daemon to work.
# ============================================

# Configuration file
if [ ! -h "/etc/default/celeryd" ]
then
    ln -s `pwd`/secondfunnel/settings/celeryd /etc/default/celeryd
    echo "Created symlink for celery config"
else
    echo "Skipping creating symlink for celery config"
fi

# Init script
if [ ! -h "/etc/init.d/celeryd" ]
then
    ln -s `pwd`/scripts/celeryd /etc/init.d/celeryd
    chmod +x /etc/init.d/celeryd
    echo "Created symlink for celery init script"
else
    echo "Skipping creating symlink for celery init script"
fi

# Make an unprivileged, non-password-enabled user and group to run celery
useradd -M celery
useradd_status=$?
if [ useradd_status != 0 ]
then
    echo "useradd exited with an error code: '$useradd_status'"
else
    echo "Created unprivileged user 'celery'"
fi

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