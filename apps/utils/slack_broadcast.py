#   We use a client library (python-simple-hipchat) to interface
#   with the standard Hipchat API.  It is listed as a library on 
#   Hipchat's old api v1, but not on its api v2.  Nonetheless it
#   works fine.
#   library docs: https://github.com/kurttheviking/python-simple-hipchat
#   Hipchat API docs: https://www.hipchat.com/docs/api, look under "rooms/message"

import slackpy
INCOMING_WEB_HOOK = "https://hooks.slack.com/services/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"

def slack(channel, sender, message, level="info"):
    if level not in ['info','warn','error']:
        level = 'info'
    s = slackpy.SlackLogger(INCOMING_WEB_HOOK, channel, sender)
    getattr(s, level)(message=message)