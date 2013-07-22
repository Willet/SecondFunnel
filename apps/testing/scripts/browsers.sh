#!/bin/bash                                                                                                                                            
CAPTURE_URL=$1

getApp () {
    # Naive Mapping
    KEY=$BROWSER
    for i in `seq 0 ${#KEYS[@]}`; do
        if [[ ${KEYS[$i]} = $KEY ]]; then
            APP=${VALUES[$i]}
            return 0
        fi
    done
    APP=$BROWSER
    return 1
}

createTempFirefoxProfile () {
    RAND="$RANDOM.JSTESTDRIVER"
    cp "$PROFILEDIR/profiles.ini" /tmp/profiles.ini
    $FIREFOX -CreateProfile $RAND
    ARGS="--args -p $RAND"
    echo "rm -rf \"$PROFILEDIR\"/Profiles/*.$RAND" >> /tmp/jstestdriver.cleanup
    echo "mv /tmp/profiles.ini \"$PROFILEDIR/profiles.ini\"" >> /tmp/jstestdriver.cleanup
}

# Process IDs for this script's parent and itself respectively
echo $PPID >> /tmp/jstestdriver.pid
echo $$ >> /tmp/jstestdriver.pid

# This script's name so it can be deleted.
echo "killall $0" >> /tmp/jstestdriver.cleanup
echo "rm $0" >> /tmp/jstestdriver.cleanup

# Iterate over the browsers specified
for BROWSER in ${@:2}; do
    # Seperate conditions for MAC OSX and Linux
    if [[ `uname` = "Darwin" ]]; then
	    KEYS=("chrome" "firefox" "safari")
	    VALUES=("Google Chrome" "Firefox" "Safari")
	    ARGS=""
        getApp
        
        # Start the selected browser
        if [[ $APP = "Firefox" ]]; then
            PROFILEDIR=~/Library/Application\ Support/$APP
            FIREFOX="/Applications/$APP.app/Contents/MacOS/firefox"
            createTempFirefoxProfile
        elif [[ $APP = "Google Chrome" ]]; then
            RAND="/tmp/$RANDOM.GOOGLE.CHROME.PROFILE.JSTESTDRIVER"
            ARGS="--args --user-data-dir=\"$RAND\" --no-first-run --no-default-browser-check"
            # TODO: FIGURE OUT WHY I CAN'T REMOVE THE CHROME PROFILE DIRECTORY
            echo "rm -rf $RAND" >> /tmp/jstestdriver.cleanup
        fi
        eval "open -na \"$APP\" \"$CAPTURE_URL\" -g $ARGS"
        # Only want to affect the last running process
        pid=`ps -ax | grep "/Applications/$APP.app/Contents/MacOS/*" | grep -v grep | awk '{print $1}' | tail -n 1`
        echo $pid >> /tmp/jstestdriver.pid
    else
        KEYS=("chrome" "firefox")
        VALUES=("google-chrome" "firefox")
        getApp
        if [[ $APP = "Firefox" ]]; then
            PROFILEDIR=~/.mozilla/firefox
            FIREFOX="firefox"
            createTempFirefoxProfile
        elif [[ $APP = "Google Chrome" ]]; then
            RAND="/tmp/$RANDOM.GOOGLE.CHROME.PROFILE.JSTESTDRIVER"
            ARGS="--args --user-data-dir=\"$RAND\" --no-first-run --no-default-browser-check"
            echo "rm -rf $RAND" >> /tmp/jstestdriver.cleanup
        fi
        # Start application and capture process ID
        "$APP" "$CAPTURE_URL" $ARGS
        echo $! >> /tmp/jstestdriver.pid
    fi
done
