import time
from medianclients import (
    ROAPMessageType,
    ROAPMessageErrorType,
    ROAPSessionsManager
)

import multiprocessing
from flask import Flask, json, request
from flask_mqtt import Mqtt
from flask_socketio import (
    SocketIO,
    emit,
    join_room,
    leave_room
)

globalDataManager = multiprocessing.Manager()
all_active_roap_sesions = ROAPSessionsManager()
waitClientsSid = globalDataManager.dict()

app = Flask(__name__)
app.config.from_file("Configure.json", load=json.load)

socketio = SocketIO(app, logger=True, engineio_logger=True,
                    cors_allowed_origins="*")
mqtt = Mqtt(app)


@app.route("/api/authenticate")
def authenticator():
    return "ok"


# ---------Socket IO----------
@socketio.on('call_offer', namespace='/webrtc')
def handle_json():
    packet = {'cmd': 'AWAIT-OFFER'}
    waitClientsSid[request.sid] = time.time()
    mqtt.publish(
        'webrtc/notify/camera',
        json.dumps(packet, indent=4).encode("utf-8")
    )


@socketio.on('to_offer', namespace='/webrtc')
def handle_message(message):
    packet = json.loads(message)
    match packet:
        case {
            'messageType': ROAPMessageType.ANSWER.value |
            ROAPMessageType.OK.value |
            ROAPMessageType.ERROR.value |
            ROAPMessageType.SHUTDOWN.value,
            'offererSessionId': offererSessionId,
            'answererSessionId': answererSessionId,
            'seq': seq
        }:
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
                        request.sid)
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
                    to=request.sid, namespace='/webrtc')
        case _:
            app.logger.warning("unaccept formate of ROAP Message from answer")


@socketio.on('connect', namespace='/webrtc')
def handle_connect(auth):
    pass
    # print("Client connect:" + str(auth) + str(request.sid) + str(session))


@socketio.on('disconnect', namespace='/webrtc')
def handle_disconnect():
    sid = request.sid
    all_active_roap_sesions.delete_session(sid)
    if sid in waitClientsSid:
        del waitClientsSid[request.sid]

    app.logger.info('Client ({}) disconnected'.format(sid))


# ---------MQTT----------
@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print('MQTT {0}: {1}'.format(level, buf))


@mqtt.on_connect()
def handle_mqtt_connect(client, userdata, flags, rc):
    mqtt.subscribe('webrtc/roap/app')


@mqtt.on_disconnect()
def handle_mqtt_disconnect():
    app.logger.error('MQTT lost connect')
    # mqtt.client.reconnect()


@mqtt.on_topic('webrtc/roap/app')
def handle_mqtt_message(client, userdata, message):
    msgStr = message.payload.decode()
    packet = json.loads(msgStr)
    match packet:
        case {
            'messageType': ROAPMessageType.OFFER.value,
            'offererSessionId': offererSessionId,
            'seq': seq
        } if seq == 1:
            all_active_roap_sesions.add_offer(offererSessionId)
            while len(waitClientsSid) > 0:
                [sid, createTime] = waitClientsSid.popitem()
                if (time.time() - createTime) < 30:
                    socketio.emit(
                        'to_answer', msgStr,
                        to=sid, namespace='/webrtc')
                    break

            # else:
            #     print("offer have been sent more than once.")
            #     error_msg = {
            #         'messageType': ROAPMessageType.ERROR.value,
            #         'errorType': ROAPMessageErrorType.FAILED.value,
            #         'offererSessionId': offererSessionId,
            #         'seq': seq
            #     }
            #     mqtt.publish(
            #         'webrtc/roap/camera',
            #         json.dumps(error_msg, indent=4).encode('utf-8'))

        case {
            'messageType': ROAPMessageType.OFFER.value |
            ROAPMessageType.OK.value |
            ROAPMessageType.ERROR.value |
            ROAPMessageType.SHUTDOWN.value,
            'offererSessionId': offererSessionId,
            'answererSessionId': answererSessionId,
            'seq': seq
        }:
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
        case _:
            app.logger.warning("unaccept formate of ROAP Message from offer")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', use_reloader=False, debug=True)
