#!/usr/bin/env python

import os
import sys

import hipchat

HIPCHAT_API_TOKEN = "675a844c309ec3227fa9437d022d05"
HIPCHAT_CODE_ROOM_ID = 115122
HIPCHAT_DEV_ROOM_ID = 115128


def hipchat_broadcast(by='HipChat', message='Hello, World!', room_id=HIPCHAT_CODE_ROOM_ID):
    """Says random stuff on our Hipchat boards."""
    hip = hipchat.HipChat(token=HIPCHAT_API_TOKEN)
    hip.method(
        "rooms/message",
        method="POST",
        parameters={
            "room_id": room_id,
            "from": by,
            "message": message,
            "message_format": "text"}
    )

where = os.getenv('PARAM1')
if len(sys.argv) > 3:
    hipchat_broadcast(by=sys.argv[1], message=sys.argv[2], room_id=sys.argv[3])
elif where == 'TEST':
    hipchat_broadcast(
        by="Philip",
        message="(notsureif) New version on %s?" % (where),
        room_id=HIPCHAT_DEV_ROOM_ID
    )
else:
    hipchat_broadcast(
        by="Hubert",
        message="(goodnews) New version on %s!" % (where if where else "PRODUCTION")
    )
