import logging

from celery import shared_task, group, chord
from redis import Redis
from django.utils.timezone import now
from django.conf import settings

from common.constants.sportsbook_definitions import SPORTSBOOK_CLIENTS, CLIENT_LEAGUES
from common.utils.client import get_client
from common.utils.sportsbook_helpers import get_sport_from_league

from sportsdata.models import Event
from .models import Odds

redis = Redis(
	host=settings.REDIS_HOST,
	port=settings.REDIS_PORT,
	db=settings.REDIS_DB,
	decode_responses=True
)
logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def sync_odds(status: str):
	logger.info('Syncing odds...')
	chord(
		group(
			scrape_odds_for_event.s(sportsbook=sportsbook, league=league, event_key=event_key)
			for league in CLIENT_LEAGUES
			for sportsbook in SPORTSBOOK_CLIENTS
			for event_key in redis.smembers(f'events:{league}:{status}')
		),
		batch_upsert_odds.s()
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
def scrape_odds_for_event(sportsbook, league, event_key):
	logger.info(f'Scraping {sportsbook} odds for {event_key}...')
	client = get_client(sportsbook, sport=get_sport_from_league(league), league=league)
	return client.parse_markets(event_key)


@shared_task(queue='scraping')
def scrape_events_for_league(sportsbook, league):
	logger.info(f'Scraping {sportsbook} events for {league}...')
	client = get_client(sportsbook, sport=get_sport_from_league(league), league=league)
	client.parse_events()


@shared_task(queue='database')
def batch_upsert_odds(odds_data_lists: list):
	odds_data = [odds for sublist in odds_data_lists for odds in sublist]
	logger.info(f'Upserting {len(odds_data)} odds...')

	deduped_odds_data = {}
	for odds in odds_data:
		key = (odds["event_key"], odds["market_key"], odds["sportsbook"], odds["outcome"])
		deduped_odds_data[key] = odds
	
	odds_data = list(deduped_odds_data.values())

	to_create, to_update = [], []

	lookup_keys = set(
        (o['event_key'], o['market_key'], o['sportsbook'], o['outcome'])
        for o in odds_data
    )

	existing_odds = {
		(o.event_key, o.market_key, o.sportsbook, o.outcome): o
		for o in Odds.objects.filter(
			event_key__in={k[0] for k in lookup_keys},
			market_key__in={k[1] for k in lookup_keys},
			sportsbook__in={k[2] for k in lookup_keys},
			outcome__in={k[3] for k in lookup_keys},
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
				for field in ['line', 'value', 'status']
			)
			if has_changes:
				for field in ['line', 'value', 'status']:
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
				status=odds['status']
			))

	if to_create:
		Odds.objects.bulk_create(to_create)
		logger.info(f'Creating {len(to_create)} odds rows...')
	if to_update:
		Odds.objects.bulk_update(to_update, ['value', 'status', 'collected_at'])
		logger.info(f'Updating {len(to_update)} odds rows...')

				
				