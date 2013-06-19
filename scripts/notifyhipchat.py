#!/usr/bin/env python

import hipchat


def hipchat_broadcast(by='HipChat', message='Hello, World!', room_id=115122):
    """Says random stuff on our Hipchat boards."""
    hip = hipchat.HipChat(token="675a844c309ec3227fa9437d022d05")
    hip.method("rooms/message", method="POST",
               parameters={"room_id": room_id, "from": by,
                           "message": message, "message_format": "text"})


where = ''
try:
    import os
    where = os.getenv('PARAM1')
    if where:
        where = ' on %s' % where
except KeyError:
    pass

hipchat_broadcast(by="Hubert" % where, message="(goodnews) New version%s!")