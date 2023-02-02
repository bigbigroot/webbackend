import os

from flask import Flask
from flask_mqtt import Mqtt
from flask_socketio import SocketIO

mqtt = Mqtt()
socketio = SocketIO()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='DEV'
    )
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    socketio.init_app(app, logger=True, engineio_logger=True,
                      cors_allowed_origins="*")
    mqtt.init_app(app)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import auth
    app.register_blueprint(auth.bp)

    return app
