from flask_migrate import Migrate
from flask import Flask
from database.models import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from .events import bp as events_bp
    app.register_blueprint(events_bp)
    
    return app