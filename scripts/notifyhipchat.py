#!/usr/bin/env python

import hipchat

where = ''
try:
    import os
    where = os.environ['HOSTNAME']
    if where:
        where = ' on %s' % where
except KeyError:
    pass

hip = hipchat.HipChat(token="675a844c309ec3227fa9437d022d05")
hip.method("rooms/message", method="POST",
           parameters={"room_id": 115122, "from": "Mr. T%s" % where,
                       "message": "I pity the fool who doesn't deploy!"
                                  " New version is up!"})