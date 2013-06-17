#!/usr/bin/env python

import hipchat


def hipchat_broadcast(by='HipChat', message='Hello, World!', room_id=115122):
    """Says random stuff on our Hipchat boards."""
    hip = hipchat.HipChat(token="675a844c309ec3227fa9437d022d05")
    hip.method("rooms/message", method="POST",
               parameters={"room_id": room_id, "from": by, "message": message})


where = ''
try:
    import os
    where = os.getenv('PARAM1')
    if where:
        where = ' on %s' % where
except KeyError:
    pass

hipchat_broadcast(by="Mr. T%s" % where,
                  message="I pity the fool who doesn't deploy!"
                          " New version is up!")