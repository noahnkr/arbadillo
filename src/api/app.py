from flask_migrate import Migrate
from flask import Flask
from database.models import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        db.create_all()

        from .routes import events
        app.register_blueprint(events.bp)
    
    return app