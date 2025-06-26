import logging

from oddsdata.tasks import logger
from sportsdata.models import Team, Event

from celery import shared_task
from django.utils.timezone import now

logger = logging.getLogger(__name__)

@shared_task
def batch_upsert_events(event_data):
	to_create, to_update = [], []

	event_keys = [e['event_key'] for e in event_data]
	existing_events = {
		e.event_key: e
		for e in Event.objects.filter(event_key__in=event_keys)
	}

	team_keys = set()
	for e in event_data:
		team_keys.add(e['away_team_key'])
		team_keys.add(e['home_team_key'])

	teams = {
		t.team_key: t
		for t in Team.objects.filter(team_key__in=team_keys)
	}

	for event in event_data:
		away_team = teams.get(event['away_team_key'])
		home_team = teams.get(event['home_team_key'])

		if not away_team or not home_team:
			logger.warning(f'Missing team(s) for event_key={event["event_key"]}')
		
		existing = existing_events.get(event['event_key'])
		if existing:
			has_changes = (
				existing.league != event['league'] or
				existing.away_team != away_team or
				existing.home_team != home_team or
				existing.start_time != event['start_time'] or
				existing.status != event['statuts']
			)
			if has_changes:
				existing.league = event['league']
				existing.away_team = away_team
				existing.home_team = home_team
				existing.start_time = event['start_time']
				existing.status = event['status']
				existing.updated_at = now()
				to_update.append(existing)
		else:
			to_create.append(Event(
				event_key=event['event_key'],
				league=event['league'],
				away_team=away_team,
				home_team=home_team,
				start_time=event['start_time'],
				status=event['status'],
				collected_at=now(),
				updated_at=now()
			))
	
	if to_create:
		Event.objects.bulk_create(to_create)
		logger.info(f'Created {len(to_create)} new event(s).')

	if to_update:
		Event.objects.bulk_update(to_update, ['league', 'away_team', 'home_team', 'start_time', 'status', 'updated_at'])
		logger.info(f'Updated {len(to_update)} existing event(s).')