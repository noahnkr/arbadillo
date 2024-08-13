from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    away_team = db.Column(db.String, nullable=False)
    home_team = db.Column(db.String, nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

    picks = db.relationship('Pick', backref='event', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'away_team': self.away_team,
            'home_team': self.home_team,
            'event_time': self.event_time.isoformat(),
            'active': self.active
        }

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_name = db.Column(db.String, nullable=False)
    last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    picks = db.relationship('Pick', backref='book', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'book_name': self.book_name,
            'last_update': self.last_update.isoformat()
        }

class Market(db.Model):
    __tablename__ = 'markets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    market_key = db.Column(db.String, nullable=False)

    picks = db.relationship('Pick', backref='market', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'market_key': self.market_key
        }

class Pick(db.Model):
    __tablename__ = 'picks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('markets.id'), nullable=False)
    team = db.Column(db.String, nullable=True)
    line = db.Column(db.Float, nullable=True)
    odds = db.Column(db.Integer, nullable=False)
    player = db.Column(db.String, nullable=True)
    outcome = db.Column(db.String, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'book_id': self.book_id,
            'market_id': self.market_id,
            'team': self.team,
            'line': self.line,
            'odds': self.odds,
            'player': self.player,
            'outcome': self.outcome
        }