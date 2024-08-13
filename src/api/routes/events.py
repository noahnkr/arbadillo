from flask import Blueprint, jsonify, request, abort
from database.models import db, Event

bp = Blueprint('events', __name__, url_prefix='/events')

@bp.route('/', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([event.to_dict() for event in events])

@bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())

@bp.route('/', methods=['POST'])
def create_event():
    data = request.get_json()
    new_event = Event(
        away_team=data['away_team'],
        home_team=data['home_team'],
        event_time=data['event_time'],
        active=data.get('active', True)
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify(new_event.to_dict()), 201