import time

from .roappacket import (
    ROAPMessageType,
    ROAPMessageErrorType,
    check_packet_format
)
from .rtc_clients import ROAPSessionsManager
from . import mqtt, socketio


# import multiprocessing
from flask import json, current_app
from flask_socketio import (
    emit,
    join_room,
    leave_room
)


# globalDataManager = multiprocessing.Manager()
all_active_roap_sesions = ROAPSessionsManager()
waitClientsSid = dict()


def close_client(sid: str):
    all_active_roap_sesions.delete_session(sid)
    if sid in waitClientsSid:
        del waitClientsSid[sid]


def call_offer(sid: str):
    packet = {'cmd': 'AWAIT-OFFER'}
    waitClientsSid[sid] = time.time()
    mqtt.publish(
        'webrtc/notify/camera',
        json.dumps(packet, indent=4).encode("utf-8")
    )


def back_to_offer(sid: str, message: str):
    packet = json.loads(message)
    if (check_packet_format(packet)):
        offererSessionId = packet['offererSessionId']
        answererSessionId = packet['answererSessionId']
        seq = packet['seq']
        if all_active_roap_sesions.is_have_offer(offererSessionId):
            s = all_active_roap_sesions.get_session_of_offer(
                offererSessionId)
            if (packet["messageType"] == ROAPMessageType.OK and
                    s.is_wait_for_close()):
                all_active_roap_sesions.delete_offer_and_answer(
                    offererSessionId,
                    answererSessionId
                )
                leave_room('living_room')
            elif (seq == 1 and
                    packet["messageType"] == ROAPMessageType.ANSWER):
                all_active_roap_sesions.add_answer(
                    offererSessionId,
                    answererSessionId,
                    sid)
                join_room('living_room')
            mqtt.publish(
                "webrtc/roap/camera",
                json.dumps(packet, indent=4).encode('utf-8'))
        else:
            error_msg = {
                'messageType': ROAPMessageType.ERROR.value,
                'errorType': ROAPMessageErrorType.NOMATCH.value,
                'offererSessionId': offererSessionId,
                'answererSessionId': answererSessionId,
                'seq': seq
            }
            emit(
                'to_answer', json.dumps(error_msg, indent=4),
                to=sid, namespace='/webrtc')
    else:
        current_app.logger.warning(
            "unaccept formate of ROAP Message from answer")


def to_answer(msgStr: str):
    packet = json.loads(msgStr)
    if check_packet_format(packet):
        offererSessionId = packet['offererSessionId']
        seq = packet['seq']
        if seq == 1:
            all_active_roap_sesions.add_offer(offererSessionId)
            while len(waitClientsSid) > 0:
                [sid, createTime] = waitClientsSid.popitem()
                if (time.time() - createTime) < 30:
                    socketio.emit(
                        'to_answer', msgStr,
                        to=sid, namespace='/webrtc')
                    break

            else:
                current_app.logger.warning("have not a active client.")
            #     error_msg = {
            #         'messageType': ROAPMessageType.ERROR.value,
            #         'errorType': ROAPMessageErrorType.FAILED.value,
            #         'offererSessionId': offererSessionId,
            #         'seq': seq
            #     }
            #     mqtt.publish(
            #         'webrtc/roap/camera',
            #         json.dumps(error_msg, indent=4).encode('utf-8'))

        else:
            answererSessionId = packet['answererSessionId']
            if all_active_roap_sesions.is_have_answer(answererSessionId):
                s = all_active_roap_sesions.get_session_of_offer(
                    offererSessionId)
                if s.is_wait_for_close():
                    all_active_roap_sesions.delete_offer_and_answer(
                        offererSessionId, answererSessionId)
                elif packet['messageType'] == ROAPMessageType.SHUTDOWN:
                    s.set_state_as_wait_close()
                socketio.emit('to_answer', msgStr, to=s.socketioSid)
            else:
                error_msg = {
                    'messageType': ROAPMessageType.ERROR.value,
                    'errorType': ROAPMessageErrorType.NOMATCH.value,
                    'offererSessionId': offererSessionId,
                    'answererSessionId': answererSessionId,
                    'seq': seq
                }
                mqtt.publish(
                    'webrtc/roap/camera',
                    json.dumps(error_msg, indent=4).encode('utf-8'))
    else:
        current_app.logger.warning(
            "unaccept formate of ROAP Message from offer")
