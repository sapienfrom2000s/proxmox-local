from flask import Flask, jsonify
from config import Config
from app.redis import init_redis


def create_app(config=None):
    app = Flask(__name__)
    if config:
        app.config.update(config)
    else:
        app.config.from_object(Config)

    init_redis(app)

    from app.routes import api
    app.register_blueprint(api)

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": e.description}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "internal server error"}), 500

    return app
