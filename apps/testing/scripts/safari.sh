# Workaround for Safari on MAC
# Reference: https://code.google.com/p/js-test-driver/issues/detail?id=97#c8

#!/bin/bash
trap "{ killall Safari; rm -rf ~/Library/Saved\ Application\ State/com.apple.Safari.savedState/; exit 0; }" EXIT
open -a Safari -W $1