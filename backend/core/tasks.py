import logging
from .models import Event, Odds
from .celery import app
from common.utils import format_odds

logger = logging.getLogger('celery')

@app.task
def upsert_event(event_data):
    logger.info(f"Upserting event {event_data['event_key']}...")
    Event.objects.update_or_create(
        event_key=event_data['event_key'],
        defaults={
            'league': event_data['league'],
            'start_time': event_data['start_time'],
            'away': event_data['away'],
            'home': event_data['home'],
            'status': event_data['status'],
        }
    )


@app.task
def upsert_odds(odds_data):
    try:
        logger.info(f"Upserting {odds_data['sportsbook']} {format_odds(odds_data)} for event: {odds_data['event_key']}...")
        event = Event.objects.get(event_key=odds_data['event_key'])
        Odds.objects.update_or_create(
            event=event,
            sportsbook=odds_data['sportsbook'],
            market=odds_data['market'],
            outcome=odds_data['outcome'],
            line=odds_data['line'],
            defaults={
                'value': odds_data['value'],
                'player': odds_data['player'],
                'prop': odds_data['prop'],
            }
        )
        logger.info(f"Odds successfully updated for event: {odds_data['event_key']}")
    except Event.DoesNotExist:
        logger.error(f"Event with key {odds_data['event_key']} does not exist.")
    except Exception as e:
        logger.error(f'Failed to update or create odds: {e}')
