import logging

from celery import shared_task, group, chord
from redis import Redis
from django.conf import settings

from sports.models import Event
from .models import Selection
from .dto import SelectionData

from common.constants.sportsbook_definitions import SPORTSBOOK_CLIENTS, CLIENT_LEAGUES
from common.utils.client import get_client
from common.utils.sportsbook_helpers import get_sport_from_league

redis = Redis(
	host=settings.REDIS_HOST,
	port=settings.REDIS_PORT,
	db=settings.REDIS_DB,
	decode_responses=True
)
logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def sync_selections(status: str):
	logger.info('Syncing selections...')
	chord(
		group(
			scrape_selections_for_event.s(sportsbook=sportsbook, league=league, event_key=event_key)
			for league in CLIENT_LEAGUES
			for sportsbook in SPORTSBOOK_CLIENTS
			for event_key in redis.smembers(f'events:{league}:{status}')
		),
		batch_upsert_selections.s()
	).apply_async()


@shared_task(queue='scraping')
def sync_sportsbook_schedule():
	logger.info('Syncing sportsbook schedules...')
	group(
		scrape_events_for_league.s(sportsbook=sportsbook, league=league)
		for sportsbook in SPORTSBOOK_CLIENTS
		for league in CLIENT_LEAGUES
	).apply_async()


@shared_task(queue='scraping')
def scrape_selections_for_event(sportsbook, league, event_key):
	logger.info(f'Scraping {sportsbook} selections for {event_key}...')
	client = get_client(sportsbook, sport=get_sport_from_league(league), league=league)
	selections = client.parse_markets(event_key)
	return [s.to_dict() for s in selections]


@shared_task(queue='scraping')
def scrape_events_for_league(sportsbook, league):
	logger.info(f'Scraping {sportsbook} events for {league}...')
	client = get_client(sportsbook, sport=get_sport_from_league(league), league=league)
	client.parse_events()


@shared_task(queue='database')
def batch_upsert_selections(selection_data_lists: list):
	selection_data = [
		SelectionData.from_dict(s)
		for sublist in selection_data_lists 
		for s in sublist
	]
	
	logger.info(f'Upserting {len(selection_data)} selections...')

	deduped_selection_data = {}
	for selection in selection_data:
		key = (selection.sportsbook, selection.league, selection.event_key, selection.market_key, selection.outcome)
		deduped_selection_data[key] = selection
	
	selection_data = list(deduped_selection_data.values())

	to_create, to_update = [], []

	lookup_keys = set(
		(s.sportsbook, s.league, s.event_key, s.market_key, s.outcome)
		for s in selection_data
	)

	existing_selections = {
		(s.sportsbook, s.league, s.event_key, s.market_key, s.outcome): s
		for s in Selection.objects.filter(
			sportsbook__in={k[0] for k in lookup_keys},
			league__in={k[1] for k in lookup_keys},
			event_key__in={k[2] for k in lookup_keys},
			market_key__in={k[3] for k in lookup_keys},
			outcome__in={k[4] for k in lookup_keys},
		)
	}

	event_map = {
		e.event_key: e
		for e in Event.objects.filter(event_key__in=[s.event_key for s in selection_data])
	}

	for selection in selection_data:
		key = (selection.sportsbook, selection.league, selection.event_key, selection.market_key, selection.outcome)
		event = event_map.get(selection.event_key)
		if not event:
			event_key = selection.event_key
			logger.warning(f'Event foriegn key {event_key} does not exist')
			continue
		
		existing = existing_selections.get(key)
		if existing:
			has_changes = any(
				getattr(existing, field) != getattr(selection, field)
				for field in ['line', 'value', 'status']
			)
			if has_changes:
				for field in ['line', 'value', 'status', 'collected_at']:
					setattr(existing, field, getattr(selection, field))
				to_update.append(existing)
		else:
			to_create.append(Selection(event=event, **selection.to_dict()))

	if to_create:
		Selection.objects.bulk_create(to_create)
		logger.info(f'Creating {len(to_create)} selection rows...')
	if to_update:
		Selection.objects.bulk_update(to_update, ['line', 'value', 'status', 'collected_at'])
		logger.info(f'Updating {len(to_update)} selection rows...')