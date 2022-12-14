from roaprotocol import (
    ROAPMessageType,
    ROAPMessageErrorType,
    ROAPSession,
    ROAPSessionsManager
)

from flask import Flask, json, request
from flask_mqtt import Mqtt
from flask_socketio import (
    SocketIO,
    send,
    join_room,
    leave_room
)

all_active_roap_sesions = ROAPSessionsManager()

app = Flask(__name__)
app.config.from_file("Configure.json", load=json.load)

socketio = SocketIO(app, logger=True, engineio_logger=True,
                    cors_allowed_origins="*")
mqtt = Mqtt(app)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# ---------Socket IO----------


@socketio.on('ready', namespace='/webrtc')
def handle_json():
    packet = {'cmd': 'AWAIT-OFFER'}
    join_room('waiting_room')
    mqtt.publish(
        'webrtc/notify/camera',
        json.dumps(packet, indent=4).encode("utf-8")
    )


@socketio.on('setup', namespace='/webrtc')
def handle_message(packet):
    match packet:
        case {
            'messageType': ROAPMessageType.ANSWER |
            ROAPMessageType.OK |
            ROAPMessageType.ERROR |
            ROAPMessageType.SHUTDOWN,
            'offererSessionId': offererSessionId,
            'answererSessionId': answererSessionId,
            'seq': seq
        }:
            if all_active_roap_sesions.is_have_offer(offererSessionId):
                s = all_active_roap_sesions.get_session_of_answer(
                    answererSessionId)
                if (packet["messageType"] == ROAPMessageType.OK and
                        s.is_wait_for_close()):
                    all_active_roap_sesions.delete_offer_and_answer(
                        offererSessionId,
                        answererSessionId
                    )
                    leave_room('living_room')
                elif (seq == 1 and
                        packet["messageType"] == ROAPMessageType.ANSWER):
                    currentSession = ROAPSession(
                        offererSessionId,
                        answererSessionId,
                        request.sid
                    )
                    all_active_roap_sesions.add_answer(
                        answererSessionId,
                        currentSession)
                    leave_room('waiting_room')
                    join_room('living_room')
                mqtt.publish(
                    "webrtc/roap/camera",
                    json.dumps(packet, indent=4).encode('utf-8'))
            else:
                error_msg = {
                    'messageType': ROAPMessageType.ERROR,
                    'errorType': ROAPMessageErrorType.NOMATCH,
                    'offererSessionId': offererSessionId,
                    'answererSessionId': answererSessionId,
                    'seq': seq
                }
                send(json.dumps(error_msg, indent=4))
        case _:
            error_msg = {
                'messageType': ROAPMessageType.ERROR,
                'errorType': ROAPMessageErrorType.FAILED
            }
            send(json.dumps(error_msg, indent=4))


@socketio.on('connect', namespace='/webrtc')
def handle_connect(auth):
    pass
    # print("Client connect:" + str(auth) + str(request.sid) + str(session))


@socketio.on('disconnect', namespace='/webrtc')
def handle_disconnect():
    all_active_roap_sesions.delete_session(request.sid)
    print('Client disconnected')


# ---------MQTT----------
@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print('MQTT {0}: {1}'.format(level, buf))


@mqtt.on_connect()
def handle_mqtt_connect(client, userdata, flags, rc):
    mqtt.subscribe('webrtc/roap/app')


@mqtt.on_disconnect()
def handle_mqtt_disconnect(client, userdata, flags, rc):
    print('try to reconnect')
    mqtt.client.reconnect()


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
            with app.app_context():
                socketio.emit(
                    'to_answer', packet,
                    to='waiting_room', namespace='/webrtc')
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
                s = all_active_roap_sesions.get_session_of_answer(
                    answererSessionId)
                if s.isWaitClose():
                    all_active_roap_sesions.delete_offer_and_answer(
                        offererSessionId, answererSessionId)
                elif packet['messageType'] == ROAPMessageType.SHUTDOWN:
                    s.setStateWaitClose()
                socketio.emit('setup', packet, to=s.socketioSid)
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
            error_msg = {
                'messageType': ROAPMessageType.ERROR.value,
                'errorType': ROAPMessageErrorType.FAILED.value,
            }
            mqtt.publish(
                'webrtc/roap/camera',
                json.dumps(error_msg, indent=4).encode('utf-8'))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', use_reloader=False, debug=True)
