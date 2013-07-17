#!/bin/bash
# Script to install the necessary tools for the testing environment to work properly.
DOWNLOADER=""
if [ `uname` = "Darwin" ]; then
    DOWNLOADER="curl -O"
else
    DOWNLOADER="wget"
fi

JASMINE="https://github.com/downloads/pivotal/jasmine/jasmine-standalone-1.3.1.zip"
JASMINEADAPTER="https://raw.github.com/ibolmo/jasmine-jstd-adapter/master/src/JasmineAdapter.js"
JSTESTDRIVER="https://js-test-driver.googlecode.com/files/JsTestDriver-1.3.5.jar"
PHANTOMJSTD="https://raw.github.com/larrymyers/js-test-driver-phantomjs/master/phantomjs-jstd.js"

REQUIRED=(
    # Form of (file/dir, command)
    '("jasmine" "$DOWNLOADER $JASMINE && mkdir -p jasmine && unzip jasmine-standalone-1.3.1.zip -d jasmine/ && rm jasmine-standalone-1.3.1.zip" )'
    '("jstestdriver/JasmineAdapter.js" "$DOWNLOADER $JASMINEADAPTER && mv JasmineAdapter.js jstestdriver/JasmineAdapter.js")'
    '("jstestdriver/JsTestDriver-1.3.5.jar" "$DOWNLOADER $JSTESTDRIVER && mv JsTestDriver-1.3.5.jar jstestdriver/JsTestDriver-1.3.5.jar")'
    '("phantomjs/phantomjs-jstd.js" "$DOWNLOADER $PHANTOMJSTD && mv phantomjs-jstd.js phantomjs/phantomjs-jstd.js")'
)

mkdir -p phantomjs jstestdriver
for tuple in "${REQUIRED[@]}"; do
    pair=`eval ${tuple}`
    if [ ! -e ${pair[0]} ]; then
        echo "Downloading dependency...."
        eval ${pair[1]};
    fi
done


