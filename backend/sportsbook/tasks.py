import logging
import time

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
	start = time.perf_counter()
	logger.info(f'Scraping {sportsbook} selections for {event_key}...')
	sport = get_sport_from_league(league)
	redis_key = f'{sportsbook}:timing:scrape_selections_for_event:{league}:{event_key}'
	try:
		with get_client(sportsbook, sport, league) as client:
			selections = client.parse_markets(event_key)
		return [s.to_dict() for s in selections]
	except Exception:
		logger.exception(f'scrape_selections_for_event failed: {sportsbook} / {league} / {event_key}')
		return []
	finally:
		elapsed = time.perf_counter() - start
		redis.set(redis_key, elapsed)
		logger.debug(f'Scraped {sportsbook} selections for {event_key} in {elapsed:.2f} seconds.')


@shared_task(queue='scraping')
def scrape_events_for_league(sportsbook, league):
	logger.info(f'Scraping {sportsbook} events for {league}...')
	sport = get_sport_from_league(league)
	with get_client(sportsbook, sport, league) as client:
		client.parse_events()


@shared_task(queue='database')
def batch_upsert_selections(selection_data_lists: list):
	# Aggregate scraping times from previous tasks
	for sportsbook in SPORTSBOOK_CLIENTS:
		for league in CLIENT_LEAGUES:
			keys = redis.keys(f'{sportsbook}:timing:scrape_selections_for_event:{league}:*')
			durations = [float(redis.get(k)) for k in keys]

			total_time = sum(durations)
			avg_time = total_time / len(durations) if durations else 0

			logger.info(f'Total {sportsbook} execution time for {league}: {total_time:.2f} seconds.')
			logger.info(f'Avg. {sportsbook} execution time for for {league}: {avg_time:.2f} seconds.')

			if keys:
				redis.delete(*keys)

	# Flatten nested lists and load selection data
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

	for selection in selection_data:
		key = (selection.sportsbook, selection.league, selection.event_key, selection.market_key, selection.outcome)
		
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
			to_create.append(Selection(**selection.to_dict()))

	if to_create:
		Selection.objects.bulk_create(to_create)
		logger.info(f'Creating {len(to_create)} selection rows...')
	if to_update:
		Selection.objects.bulk_update(to_update, ['line', 'value', 'status', 'collected_at'])
		logger.info(f'Updating {len(to_update)} selection rows...')