#!/bin/bash
if [ -e /tmp/jstestdriver.pid ]; then
    for pid in `cat /tmp/jstestdriver.pid`; do
        kill -TERM $pid > /dev/null 2>&1
    done
    rm /tmp/jstestdriver.pid
fi

if [ -e /tmp/jstestdriver.cleanup ]; then
    chmod u+x /tmp/jstestdriver.cleanup
    /tmp/jstestdriver.cleanup > /dev/null 2>&1
    rm /tmp/jstestdriver.cleanup
fi

pid=`ps -ax | grep "/usr/bin/java -jar .*/resources/JsTestDriver.jar" | grep -v grep | awk '{print $1}'`
kill -TERM $pid > /dev/null 2>&1
