#!/usr/bin/env python

import os, sys

import hipchat


def hipchat_broadcast(by='HipChat', message='Hello, World!', room_id=115122):
    """Says random stuff on our Hipchat boards."""
    hip = hipchat.HipChat(token="675a844c309ec3227fa9437d022d05")
    hip.method("rooms/message", method="POST",
               parameters={"room_id": room_id, "from": by,
                           "message": message, "message_format": "text"})


where = os.getenv('PARAM1')
if len(sys.argv) > 3:
    hipchat_broadcast(by=sys.argv[1], message=sys.argv[2], room_id=sys.argv[3])
elif where == 'TEST':
    hipchat_broadcast(by="Philip", message="(notsureif) New version on %s?" % (where),
                      room_id=115128)  # code
else:
    hipchat_broadcast(by="Hubert", message="(goodnews) New version on %s!" % (
        where if where else "PRODUCTION"))
