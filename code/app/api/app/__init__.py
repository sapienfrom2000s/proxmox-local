from flask import Flask
from config import Config


def create_app(config=None):
    app = Flask(__name__)  # TODO: understand what __name__ does
    if config:
        app.config.update(config)
    else:
        app.config.from_object(Config)

    from app.routes import api
    app.register_blueprint(api)

    return app
