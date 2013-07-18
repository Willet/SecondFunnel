#!/bin/bash
# Script to install the necessary tools for the testing environment to work properly.
DOWNLOADER=""
DIR=`pwd`

cd "$( dirname "${BASH_SOURCE[0]}" )"
cd ..

if [[ `uname` = "Darwin" ]]; then
    DOWNLOADER="curl -L"
else
    DOWNLOADER="wget"
fi

JASMINE="https://github.com/downloads/pivotal/jasmine/jasmine-standalone-1.3.1.zip"
JASMINEADAPTER="https://raw.github.com/ibolmo/jasmine-jstd-adapter/master/src/JasmineAdapter.js"
JSTESTDRIVER="https://js-test-driver.googlecode.com/files/JsTestDriver-1.3.5.jar"
PHANTOMJSTD="https://raw.github.com/larrymyers/js-test-driver-phantomjs/master/phantomjs-jstd.js"

mkdir -p phantomjs jstestdriver

if [ ! -e "jasmine" ]; then
    $DOWNLOADER $JASMINE -o jasmine-standalone.zip
    unzip jasmine-standalone.zip -d jasmine/
    rm jasmine-standalone.zip
fi

if [ ! -e "jstestdriver/JasmineAdapter.js" ]; then
    $DOWNLOADER $JASMINEADAPTER -o JasmineAdapter.js
    mv JasmineAdapter.js jstestdriver/JasmineAdapter.js
fi

if [ ! -e "jstestdriver/JsTestDriver.jar" ]; then
    $DOWNLOADER $JSTESTDRIVER -o JsTestDriver.jar
    mv JsTestDriver.jar jstestdriver/JsTestDriver.jar
fi

if [ ! -e "phantomjs/phantomjs-jstd.js" ]; then
    mdkir -p phantomjs
    $DOWNLOADER $PHANTOMJSTD -o phantomjs-jstd.js
    mv phantomjs-jstd.js phantomjs/phantomjs-jstd.js
fi

if [ ! -e "jstestdriver/settings.py" ]; then
    echo -e "GENERIC_BROWSER_LIST = [ \"chrome\", \"firefox\", \"safari\", \"ie\" ]\n\n" >> jstestdriver/settings.py
    echo -e "ADDITIONAL_BROWSER_LIST = [ \n]\n\n" >> jstestdriver/settings.py
    echo -e "CONFIG = {\n\t\"desktop\": \"tests/dev.desktop.yaml\",\n\t\"mobile\": \"tests/dev.mobile.yaml\"" >> jstestdriver/settings.py
    echo -e "\n\t\"sample\": \"sample/sample.yaml\"\n}\n" >> jstestdriver.settings.py
fi


path=`command -v phantomjs > /dev/null 2>&1`
if [[ ${?} -ne 0 ]]; then
    if [[ `uname` = "Darwin" ]]; then
        brew install phantomjs
    else
        sudo apt-get install phantomjs
    fi
fi


# Return to the directory from which this script was called
cd $DIR


