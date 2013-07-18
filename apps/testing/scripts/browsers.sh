#!/bin/bash                                                                                                                                            
CAPTURE_URL=$1

getApp () {
    # Naive Mapping
    KEY=$BROWSER
    for i in `seq 0 ${#KEYS[@]}`; do
        if [[ ${KEYS[$i]} = $KEY ]]; then
            APP=${VALUES[$i]}
            break
        fi
    done
}

# Process IDs for this script's parent and itself respectively
echo $PPID >> /tmp/jstestdriver.pid
echo $$ >> /tmp/jstestdriver.pid

# This script's name so it can be deleted.
echo $0 >> /tmp/jstestdriver.scripts

# Iterate over the browsers specified
for BROWSER in ${@:2}; do
    # Seperate conditions for MAC OSX and Linux
    if [[ `uname` = "Darwin" ]]; then
	    KEYS=("chrome" "firefox" "safari")
	    VALUES=("Google Chrome" "Firefox" "Safari")
	    getApp
        
	    # Delete saved application states
        if [[ $APP = "Safari" ]]; then
            trap "{ killall Safari; rm -rf ~/Library/Saved\ Application\ State/com.apple.Safari.savedState/; exit 0; }" EXIT
	    elif [[ $APP = "Google Chrome" ]]; then
            trap "{ killall Google\ Chrome; rm -rf ~/Library/Saved\ Application\ State/com.google.Chrome.savedState/; exit 0; }" EXIT
	    fi
        
        # Run the programs.
        # Firefox is strange in which it won't terminate when it's parent terminates, so we have to continue execution
        # for it.
        if [[ $APP = "Firefox" ]]; then
            open -a "$APP" "$CAPTURE_URL"
        else
            open -a "$APP" -W "$CAPTURE_URL"
        fi
        pid=`ps -ax | grep "/Applications/$APP.app/Contents/MacOS/*" | grep -v grep | awk '{print $1}'`
        echo $pid >> /tmp/jstestdriver.pid
    else
        KEYS=("chrome" "firefox")
        VALUES=("google-chrome" "firefox")
        getApp
        # Start application and capture process ID
        "$APP" "$CAPTURE_URL"
        echo $! >> /tmp/jstestdriver.pid
    fi
done
