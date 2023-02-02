from enum import Enum


class ROAPMessageType(Enum):
    OFFER = 'OFFER'
    ANSWER = 'ANSWER'
    OK = 'OK'
    ERROR = 'ERROR'
    SHUTDOWN = 'SHUTDOWN'


class ROAPMessageErrorType(Enum):
    NOMATCH = 'NOMATCH'
    TIMEOUT = 'TIMEOUT'
    REFUSED = 'REFUSED'
    CONFLICT = 'CONFLICT'
    DOUBLECONFLICT = "DOUBLECONFLICT"
    FAILED = 'FAILED'


def match_message_type(packet: dict) -> bool:
    type = ROAPMessageType(packet['messageType'])
    if type in (ROAPMessageType.OFFER,
                ROAPMessageType.ANSWER):
        return 'sdp' in packet
    elif type in (ROAPMessageType.OK,
                  ROAPMessageType.SHUTDOWN):
        return True
    elif type == ROAPMessageType.ERROR:
        return 'errorType' in packet
    else:
        return False


def check_packet_format(packet: dict) -> bool:
    if ('seq' and 'messageType') in packet:
        if packet['seq'] == 1:
            if 'offererSessionId' in packet:
                return match_message_type(packet)
            else:
                return False
        else:
            if (('offererSessionId' and
                 'answererSessionId') in packet):
                return match_message_type(packet)
            else:
                return False
    else:
        return False
