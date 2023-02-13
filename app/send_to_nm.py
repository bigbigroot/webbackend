from . import mqtt
from gevent.event import AsyncResult


def requset_to_networkmanager(message: str):
    mqtt.publish('networking/manager', message.encode())
    response = AsyncResult()

    @mqtt.on_topic('networking/app')
    def receive(client, userdata, message):
        response.set(message.payload.decode())

    return response
