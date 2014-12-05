#   We use a client library (python-simple-hipchat) to interface
#   with the standard Hipchat API.  It is listed as a library on 
#   Hipchat's old api v1, but not on its api v2.  Nonetheless it
#   works fine.
#   library docs: https://github.com/kurttheviking/python-simple-hipchat
#   Hipchat API docs: https://www.hipchat.com/docs/api, look under "rooms/message"

import hipchat
HIPCHAT_API_TOKEN = "675a844c309ec3227fa9437d022d05"

# hipchat room ids
rooms = {
    "scrapy": 1003016,
    "101010": 115128,
    "code": 115112
}

h = hipchat.HipChat(token=HIPCHAT_API_TOKEN)

def msg(sender, room, message, type="text", **kwargs):
    kwargs.update({
        "from": sender,
        "room_id": rooms[room.lower()],
        "message": message,
        "message_format": type
    })
    h.method(
        "rooms/message",
        method="POST",
        parameters=kwargs
    )
