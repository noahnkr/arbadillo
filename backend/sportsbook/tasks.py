import logging
import random
import time

from celery import shared_task, group, chord
from redis import Redis
from django.conf import settings
from django.db import transaction

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
	tasks = []
	for league in CLIENT_LEAGUES:
		event_keys = list(redis.smembers(f'events:{league}:{status}'))
		for i, event_key in enumerate(event_keys):
			for j, sportsbook in enumerate(sorted(SPORTSBOOK_CLIENTS)):
				countdown = (j * 8) + (i * 1.5) + random.uniform(0, 3)
				tasks.append(
					scrape_selections_for_event.s(
						sportsbook=sportsbook, league=league, event_key=event_key,
					).set(countdown=countdown)
				)
	if not tasks:
		logger.warning(f'sync_selections({status!r}): no event keys in Redis — skipping')
		return
	chord(group(tasks), batch_upsert_selections.s()).apply_async()


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
			keys = list(redis.scan_iter(f'{sportsbook}:timing:scrape_selections_for_event:{league}:*'))
			if not keys:
				continue

			pipe = redis.pipeline()
			for k in keys:
				pipe.get(k)
			raw_values = pipe.execute()
			durations = [float(v) for v in raw_values if v is not None]

			total_time = sum(durations)
			avg_time = total_time / len(durations) if durations else 0

			logger.info(f'Total {sportsbook} execution time for {league}: {total_time:.2f} seconds.')
			logger.info(f'Avg. {sportsbook} execution time for {league}: {avg_time:.2f} seconds.')
			redis.delete(*keys)

	# Flatten nested lists and load selection data, guarding against failed subtasks
	selection_data = [
		SelectionData.from_dict(s)
		for sublist in selection_data_lists
		if sublist
		for s in sublist
	]

	# Last-write-wins dedup within the batch
	deduped: dict[tuple, SelectionData] = {}
	for sel in selection_data:
		key = (sel.sportsbook, sel.league, sel.event_key, sel.market_key, sel.outcome)
		deduped[key] = sel

	deduped_list = list(deduped.values())
	logger.info(f'Upserting {len(deduped_list)} selections...')

	with transaction.atomic():
		Selection.objects.bulk_create(
			[Selection(**s.to_dict()) for s in deduped_list],
			update_conflicts=True,
			unique_fields=['sportsbook', 'league', 'event_key', 'market_key', 'outcome'],
			update_fields=['line', 'value', 'status', 'collected_at'],
		)