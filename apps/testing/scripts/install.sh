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

mkdir -p resources tests/results

if [ ! -e "resources/jasmine" ]; then
    $DOWNLOADER $JASMINE -o jasmine-standalone.zip
    unzip jasmine-standalone.zip -d resources/jasmine/
    rm jasmine-standalone.zip
fi

if [ ! -e "resources/JasmineAdapter.js" ]; then
    $DOWNLOADER $JASMINEADAPTER -o JasmineAdapter.js
    mv JasmineAdapter.js resources/JasmineAdapter.js
fi

if [ ! -e "resources/JsTestDriver.jar" ]; then
    $DOWNLOADER $JSTESTDRIVER -o JsTestDriver.jar
    mv JsTestDriver.jar resources/JsTestDriver.jar
fi

if [ ! -e "resources/phantomjs-jstd.js" ]; then
    $DOWNLOADER $PHANTOMJSTD -o phantomjs-jstd.js
    mv phantomjs-jstd.js resources/phantomjs-jstd.js
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


