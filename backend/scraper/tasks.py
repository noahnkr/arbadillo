import logging
from celery import shared_task, group, chord
from django.utils.timezone import now
from common.constants.sportsbook import LEAGUES, CLIENT_SCRAPERS
from common.utils import get_client
from .models import Event, Odds

logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def launch_client(client_name, mode, league, status=None):
	"""
	Launches a client scraper to parse the upcoming or active schedule, odds, or props data for a given league.
	"""
	logger.info(f'launching {mode} client `{client_name}` ({league})...')
	client = get_client(client_name, league)
	if mode == 'schedule':
		client.parse_schedule()
	elif mode == 'primary':
		client.parse_primary_odds(status)
	elif mode == 'props':
		client.parse_props(status)
	else:
		logger.warning(f'unknown mode `{mode}`')


@shared_task(queue='scraping')
def run_initial_scrape():
	"""
    Initiates an inital scrape workflow on startup:
    - Collects ESPN events.
    - Collects sportsbook events.
    - Collects sportsbook odds.
    """
	logger.info(f'running initial scrape...')
	logger.info(f'collecting ESPN events...')
	chord(
		group(
			launch_client.s('espn', mode='schedule', league=lg)
			for lg in LEAGUES
		),
		collect_initial_sportsbook_schedule.si()
	).apply_async()


@shared_task(queue='scraping')
def collect_initial_sportsbook_schedule():
	"""
    Collects events from all sportsbooks except ESPN.
    This task is triggered after ESPN events are collected.
    """
	logger.info(f'collecting initial sportsbook events...')
	chord(
		group(
			launch_client.s(sbook, mode='schedule', league=lg)
			for sbook in CLIENT_SCRAPERS if sbook != 'espn'
			for lg in LEAGUES
		),
		collect_initial_sportsbook_odds.si()
	).apply_async()


@shared_task(queue='scraping')
def collect_initial_sportsbook_odds():
	"""
	Collecets pre-match and live odds and props from all sportsbooks.
	This task is triggered after each sportsbooks schedule is collected.
	"""
	logger.info(f'collecting initial sportsbook odds...')
	group(
		collect_odds.s(mode=mode, status=status)
		for mode in ['primary', 'props']
		for status in ['upcoming', 'active']
	).apply_async()


@shared_task(queue='scraping')
def collect_espn_schedule():
	logger.info('collecting ESPN events...')
	group(
		launch_client.s('espn', mode='schedule', league=lg)
		for lg in LEAGUES
	).apply_async()


@shared_task(queue='scraping')
def collect_sportsbook_schedule():
	logger.info('collecting sportsbook events...')
	group(
		launch_client.s(sbook, mode='schedule', league=lg)
		for sbook in CLIENT_SCRAPERS if sbook != 'espn'
		for lg in LEAGUES
	).apply_async()


@shared_task(queue='scraping')
def collect_odds(mode, status):
	"""
	Collects odds or props from all sportsbooks for all leagues for the given event status.
	Args:
		- mode: either `primary` or `props`, props for a specific event have their own respective API url, which 
		  means their scraping pipeline should be seperated from the popular markets which are usually batched
		  by league. This improves efficiency of scraping while still utilizing concurrency.
		- status: either `upcoming` o `active`, since pre-match odds change less frequently than live
		  odds, we should collect them on different intervals.
	"""
	logger.info(f'collecting sportsbook {mode} ({status})...')
	group(
		launch_client.s(sbook, mode=mode, league=lg, status=status)
		for sbook in CLIENT_SCRAPERS
		for lg in LEAGUES
	).apply_async()


@shared_task(queue='database')
def batch_upsert_events(event_data: list):
	"""Inserts or updates event data in the database in bulk"""
	to_create, to_update = [], []

	existing_events = {
		e.event_key: e
		for e in Event.objects.filter(event_key__in=[e['event_key'] for e in event_data])
	}

	for event in event_data:
		existing = existing_events.get(event['event_key'])
		if existing:
			has_changes = any(
				getattr(existing, field) != event[field]
				for field in ['league', 'start_time', 'away', 'home', 'status']
			)
			if has_changes:
				for field in ['league', 'start_time', 'away', 'home', 'status']:
					setattr(existing, field, event[field])
				existing.collected_at = now()
				to_update.append(existing)
		else:
			to_create.append(Event(**event))

	if to_create:
		Event.objects.bulk_create(to_create)
		logger.info(f'created {len(to_create)} event rows.')
	if to_update:
		Event.objects.bulk_update(to_update, ['league', 'start_time', 'away', 'home', 'status', 'collected_at'])
		logger.info(f'updated {len(to_update)} event rows.')



@shared_task(queue='database')
def batch_upsert_odds(odds_data: list):
	"""Inserts or updates odds data in the database in bulk."""
	to_create, to_update = [], []

	existing_odds = {
		(o.event_key, o.market_key, o.sportsbook, o.outcome): o
		for o in Odds.objects.filter(
			event_key__in=[o['event_key'] for o in odds_data],
			sportsbook__in=[o['sportsbook'] for o in odds_data],
			outcome__in=[o['outcome'] for o in odds_data]
		)
	}

	event_map = {
		e.event_key: e
		for e in Event.objects.filter(event_key__in=[o['event_key'] for o in odds_data])
	}

	for odds in odds_data:
		key = (odds['event_key'], odds['market_key'], odds['sportsbook'], odds['outcome'])
		event = event_map.get(odds['event_key'])
		if not event:
			event_key = odds['event_key']
			logger.warning(f'event foriegn key {event_key} does not exist')
			continue
		
		existing = existing_odds.get(key)
		if existing:
			has_changes = any(
				getattr(existing, field) != odds[field]
				for field in ['market', 'outcome', 'line', 'value', 'team', 'player']
			)
			if has_changes:
				for field in ['market', 'outcome', 'line', 'value', 'team', 'player']:
					setattr(existing, field, odds[field])
				existing.collected_at = now()
				to_update.append(existing)
		else:
			to_create.append(Odds(
				event=event,
				event_key=odds['event_key'],
                market_key=odds['market_key'],
                sportsbook=odds['sportsbook'],
                market=odds['market'],
                outcome=odds['outcome'],
                line=odds['line'],
                value=odds['value'],
				team=odds['team'],
                player=odds['player'],
			))

	if to_create:
		Odds.objects.bulk_create(to_create)
		logger.info(f'created {len(to_create)} odds rows.')
	if to_update:
		Odds.objects.bulk_update(to_update, ['market', 'outcome', 'line', 'value', 'team', 'player', 'collected_at'])
		logger.info(f'updated {len(to_update)} odds rows.')

				
				