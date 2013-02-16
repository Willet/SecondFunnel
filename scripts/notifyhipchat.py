#!/usr/bin/env python

hip = hipchat.HipChat(token="675a844c309ec3227fa9437d022d05")
hip.method("rooms/message", method="POST", parameters={"room_id": 115122, "from": "Mr. T", "message": "I pity the fool who doesn't deploy! New version is up! (mrt)"})