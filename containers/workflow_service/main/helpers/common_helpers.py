import json
from uuid import UUID
from datetime import timedelta

def parse_message(message):
    try:
        if not isinstance(message, str):
            raise TypeError('Message should be of type string')
        msg_uuid, msg_dict = message.split('<>')
        msg_dict = json.loads(msg_dict)
        msg_uuid = UUID(msg_uuid)
    except (TypeError, ValueError, json.decoder.JSONDecodeError) as e:
        status_message = "Coudn't parse message: {}".format(message)
        return None, None, status_message
    else:
        status_message = 'Successfully parsed message ID:{}, uuid version:{}'.format(
            msg_uuid, msg_uuid.version)
        return msg_dict, msg_uuid, status_message
