#!/bin/bash
if [ -e /tmp/jstestdriver.pid ]; then
    for pid in `cat /tmp/jstestdriver.pid`; do
        kill -TERM $pid > /dev/null 2>&1
    done
    rm /tmp/jstestdriver.pid
fi

if [ -e /tmp/jstestdriver.scripts ]; then
    for script in `cat /tmp/jstestdriver.scripts`; do
        killall $script > /dev/null 2>&1
        rm $script > /dev/null 2>&1
    done
    rm /tmp/jstestdriver.scripts
fi

pid=`ps -ax | grep "/usr/bin/java -jar .*/jstestdriver/JsTestDriver.jar" | grep -v grep | awk '{print $1}'`
kill -TERM $pid > /dev/null 2>&1