import json
from roaprotocol import ROAPMessageType, ROAPMessageErrorType, ROAPSession, ROAPSessionsManager

from flask import Flask, session, request 
from flask_sock import Sock
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from flask_mqtt import Mqtt, MQTT_LOG_ERR


app = Flask(__name__)
app.config.from_file("Configure.json", load=json.load)
session["ROAPSessions"] = ROAPSessionsManager()

sock = Sock(app)
socketio = SocketIO(app, cors_allowed_origins ="*")
mqtt = Mqtt(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# ---------WebSocket Router---------
# @sock.route("/ws")
# def ROAPConnect(ws):
#     while True:
#         message = ws.receive()
#         packet = json.loads(message)
#         match packet:
#             case {
#                 'messageType': ROAPMessageType.Offer,
#                 'offererSessionId': offererSessionId,
#                 'seq': seq
#                 } if seq == 1:
#                 endpoints.addWsClients(offererSessionId, ws)
#                 mqtt.publish("webrtc/roap/app/camera", message)
#             case {
#                 'messageType': ROAPMessageType.Offer|ROAPMessageType.Ok|ROAPMessageType.Error,
#                 'offererSessionId': offererSessionId,
#                 'answererSessionId': answererSessionId,
#                 'seq': seq
#                 }:
#                 if answererSessionId in endpoints.allAnswers:
#                     mqtt.publish("webrtc/roap/app/camera", message)
#                 else:
#                     errorMsg={
#                         'messageType': ROAPMessageType.Error,
#                         'errorType': ROAPMessageErrorType.NoMatch,
#                         'offererSessionId': offererSessionId,
#                         'answererSessionId': answererSessionId,
#                         'seq': seq
#                     }
#                     ws.send(json.dumps(errorMsg, indent=4))
#             case _:
#                 errorMsg={
#                     'messageType': ROAPMessageType.Error,
#                     'errorType': ROAPMessageErrorType.Failed
#                 }
#                 ws.send(json.dumps(errorMsg, indent=4))
# ---------Socket IO----------
@socketio.on('ExceptOffer', namespace='/webrtc')
def handle_json(packet):
    match packet:
        case {
            'message': 'except a offer'
            }:
            join_room('waiting_room')
            
            mqtt.publish("webrtc/reguestmedia/camera", json.dumps(packet, indent=4)) 

@socketio.on('ROAP', namespace='/webrtc')
def handle_json(packet):
    match packet:
        case {
            'messageType': ROAPMessageType.Answer|ROAPMessageType.Ok|ROAPMessageType.Error|ROAPMessageType.Shutdown,
            'offererSessionId': offererSessionId,
            'answererSessionId': answererSessionId,
            'seq': seq
            }:
            if session["ROAPSessions"].isHaveOffer(offererSessionId):
                if seq == 1 and packet["messageType"] == ROAPMessageType.Answer:
                    currentSession = ROAPSession(offererSessionId, answererSessionId, request.sid)
                    session["ROAPSessions"].addAnswer(answererSessionId, currentSession)
                    leave_room('waiting_room ')
                    join_room('living_room')
                mqtt.publish("webrtc/roap/camera", json.dumps(packet, indent=4)) 
            else:
                errorMsg={
                    'messageType': ROAPMessageType.Error,
                    'errorType': ROAPMessageErrorType.NoMatch,
                    'offererSessionId': offererSessionId,
                    'answererSessionId': answererSessionId,
                    'seq': seq
                }
                send(json.dumps(errorMsg, indent=4))
        case _:
            errorMsg={
                'messageType': ROAPMessageType.Error,
                'errorType': ROAPMessageErrorType.Failed
            }
            send(json.dumps(errorMsg, indent=4))

@socketio.on('connect', namespace='/webrtc')
def handle_connect(auth):
    # pass
    print("Client connect:" + str(auth) + str(request.sid) + str(session))

@socketio.on('disconnect', namespace='/webrtc')
def handle_disconnect():
    print('Client disconnected')
# ---------MQTT----------
@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    if level == MQTT_LOG_ERR:
        print('Error: {}'.format(buf))

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('webrtc/roap/app')

@mqtt.on_topic('webrtc/roap/app')
def handle_message(client, userdata, message):
    msgStr = message.payload.decode()
    packet = json.loads(msgStr)
    match packet:
        case {
            'messageType': ROAPMessageType.Offer,
            'offererSessionId': offererSessionId,
            'seq': seq
            } if seq == 1:
            session["ROAPSessions"].addOffer(offererSessionId)
            emit('ROAP', packet, to='waiting_room')
        case {
            'messageType': ROAPMessageType.Offer|ROAPMessageType.Ok|ROAPMessageType.Error|ROAPMessageType.Shutdown,
            'offererSessionId': offererSessionId,
            'answererSessionId': answererSessionId,
            'seq': seq
            }:
            if session["ROAPSessions"].isHaveAnswer(answererSessionId):
                s = session["ROAPSessions"].getAnswerSession(answererSessionId)
                if s.isWaitClose():
                    session["ROAPSessions"].deleteOfferAndAnswer()
                if packet['messageType'] == ROAPMessageType.Shutdown:
                    s.setStateWaitClose()
                emit('ROAP', packet, to=sid)
            else:
                errorMsg={
                    'messageType': ROAPMessageType.Error,
                    'errorType': ROAPMessageErrorType.NoMatch,
                    'offererSessionId': offererSessionId,
                    'answererSessionId': answererSessionId,
                    'seq': seq
                }
                mqtt.publish('webrtc/roap/camera', json.dumps(errorMsg, indent=4))
        case _:
            errorMsg={
                'messageType': ROAPMessageType.Error,
                'errorType': ROAPMessageErrorType.Failed
            }
            mqtt.publish('webrtc/roap/camera', json.dumps(errorMsg, indent=4))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)