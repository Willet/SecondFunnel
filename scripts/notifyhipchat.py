#!/usr/bin/env python

import hipchat


def hipchat_broadcast(by='HipChat', message='Hello, World!', room_id=115122):
    """Says random stuff on our Hipchat boards."""
    hip = hipchat.HipChat(token="675a844c309ec3227fa9437d022d05")
    hip.method("rooms/message", method="POST",
               parameters={"room_id": room_id, "from": by,
                           "message": message, "message_format": "text"})


import os
where = os.getenv('PARAM1')
if where == 'test':
    hipchat_broadcast(by="Hubert", message="(notsureif) New version on %s?" % (where))
else:
    hipchat_broadcast(by="Hubert", message="(goodnews) New version on %s!" % (where if where else "PRODUCTION"))