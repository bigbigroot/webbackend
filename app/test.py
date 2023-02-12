from flask import request
from flask_socketio import disconnect
from flask_mqtt import MQTT_ERR_SUCCESS

from . import create_app, socketio, mqtt
from .signaling_channel import (
    back_to_offer,
    call_offer,
    close_client,
    to_answer
)
from .auth import authenticate_token


app = create_app()

# socketio = SocketIO(app, logger=True, engineio_logger=True,
#                     cors_allowed_origins="*")
# mqtt = Mqtt(app)


# ---------Socket IO----------


@socketio.on('connect', namespace='/webrtc')
def handle_connect(auth):
    if not authenticate_token(auth['token']):
        disconnect(namespace='/webrtc')
    # print("Client connect:" + str(auth) + str(request.sid) + str(session))


@socketio.on('disconnect', namespace='/webrtc')
def handle_disconnect():
    close_client(request.sid)

    app.logger.info('Client ({}) disconnected'.format(request.sid))


# ---------MQTT----------
@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    app.logger.debug('MQTT {0}: {1}'.format(level, buf))


@mqtt.on_connect()
def handle_mqtt_connect(client, userdata, flags, rc):
    app.logger.info('MQTT is connected to the broker.')
    (res, mid) = mqtt.subscribe('webrtc/roap/app')
    if res == MQTT_ERR_SUCCESS:
        app.logger.info("subscribe Topic sucess.")
    else:
        app.logger.error("subscribe Topic not sucess!")


@mqtt.on_disconnect()
def handle_mqtt_disconnect():
    app.logger.error('MQTT lost connect.')
    # mqtt.client.reconnect()


# ---------singnalingchannel----------
@socketio.on('call_offer', namespace='/webrtc')
def on_call_offer():
    call_offer(request.sid)


@socketio.on('to_offer', namespace='/webrtc')
def handle_message(message):
    back_to_offer(request.sid, message)


@mqtt.on_topic('webrtc/roap/app')
def on_to_answer(client, userdata, message):
    to_answer(message.payload.decode())


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', use_reloader=False, debug=True)
