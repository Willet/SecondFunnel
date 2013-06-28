#!/bin/bash
#
# The purpose of this script is to provide an easier starting point for running
# rabbitmq-server, django-celery and the django server without the need
# to open multiple terminals oneselve and execute individually.
#
USAGE="Usage: runserver [ restart, start, stop ]"
usage () {
    echo $USAGE
    exit 1
}
# Ensure we're running in a virtual environment
if [ "$VIRTUAL_ENV" == "" ]; then
    workon SecondFunnel
fi
# The indiviual commands we need to run in seperate terminals for logging/server
# Ensure that if this is the second time the script is being called, we terminate the current
# instances.
RUNNING=$(ps aux | grep 'manage.py runserver' | grep -v "grep" | wc -l)
if [[ ${#} -gt 1 || ${#} -lt 1 ]]; then
    usage
elif [ $RUNNING != "0" ]; then
    if [ ${1} = "restart" ]; then
        ./runserver stop && ./runserver start
    elif [ ${1} = "stop" ]; then
        echo "Shutting down RabbitMQ...this make take a few moments."
        sudo rabbitmqctl stop > /dev/null
        killall memcached
        pkill -f "runserver"
        echo "RabbitMQ, Memcached, and Django server successfully stopped."
    else
        usage
    fi
elif [ ${1} = "start" ]; then
    rm errorlog.txt serverlog.txt > /dev/null 2>&1
    echo "Starting RabbitMQ...this make take a few moments."
    sudo rabbitmq-server -detached 2> /dev/null
    memcached -p 8000 start 2> errorlog.txt 2>&1 &
    python manage.py runserver > serverlog.txt 2>&1 &
    echo "RabbitMQ, Memcached, and Django server successfully started."
else
    usage
fi