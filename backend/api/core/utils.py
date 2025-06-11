from .models import Event, Odds

def insert_or_update_event(event_data):
    """
    Insert a new event or update an existing one in the database.
    """
    event, created = Event.objects.update_or_create(
        event_key=event_data['event_key'],
        defaults=event_data
    )
    return event


def insert_or_update_odds(odds_data):
    """
    Insert a new odds entry or update an existing one in the database.
    """
    event = Event.objects.get(event_key=odds_data['event_key'])
    odds, created = Odds.objects.update_or_create(
        event=event,
        sportsbook=odds_data['sportsbook'],
        market=odds_data['market'],
        outcome=odds_data['outcome'],
        defaults={
            'line': odds_data.get('line'),
            'value': odds_data['value'],
            'player': odds_data.get('player'),
            'prop': odds_data.get('prop')
        }
    )
    return odds