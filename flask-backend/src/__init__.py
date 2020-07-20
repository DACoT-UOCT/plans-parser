from flask import Flask

from .extensions import mongo

from .junction import junction

from .petitions import petitions

from  .main2 import main2

def create_app(config_object='src.settings'):
    app = Flask(__name__)

    app.config.from_object(config_object)

    mongo.init_app(app)

    app.register_blueprint(junction)

    app.register_blueprint(petitions)

    app.register_blueprint(main2)

    return app