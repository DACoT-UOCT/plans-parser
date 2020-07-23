from flask import Flask
from flask_cors import CORS
from .junction import junction
from .petitions import petitions
from .intersection import intersection
from  .main2 import main2

def create_app(config_object='src.settings'):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_object)
    app.register_blueprint(intersection)
    app.register_blueprint(junction)
    app.register_blueprint(petitions)
    app.register_blueprint(main2)
    return app
