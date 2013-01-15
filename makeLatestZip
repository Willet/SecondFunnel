#!/bin/bash

git archive -o latest.zip HEAD
if [ -f secondfunnel/settings/dev_env.py ]
then
    zip latest.zip secondfunnel/settings/dev_env.py 1>/dev/null
fi
