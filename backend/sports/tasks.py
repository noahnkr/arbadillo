import logging

from django.utils.timezone import is_naive, make_aware
from django.db import transaction
from celery import shared_task
from datetime import datetime, timezone

from sports.models import Team, Player, Event
from sports.clients.espn import ESPNClient

logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def sync_teams(sport: str, league: str):
	logger.info('Syncing teams...')
	client = ESPNClient(sport, league)
	teams, upsert_teams = client.get_teams()
	if upsert_teams:
		upsert_teams_db.delay([t.to_dict() for t in upsert_teams])
	return [t.to_dict() for t in teams]


@shared_task(queue='database')
def upsert_teams_db(team_dicts: list):
	logger.info(f'Upserting {len(team_dicts)} team(s)')
	with transaction.atomic():
		Team.objects.bulk_create(
			[Team(espn_id=d['espn_id'], league=d['league'], team_key=d['team_key'], name=d['name'])
			 for d in team_dicts],
			update_conflicts=True,
			unique_fields=['team_key'],
			update_fields=['espn_id', 'league', 'name'],
		)


@shared_task(queue='scraping')
def sync_schedule(sport: str, league: str):
	logger.info('Syncing ESPN schedule...')
	client = ESPNClient(sport, league)
	_, upsert_events = client.get_upcoming_events()
	if upsert_events:
		upsert_events_db.delay([e.to_dict() for e in upsert_events])


@shared_task(queue='database')
def upsert_events_db(event_dicts: list):
	logger.info(f'Upserting {len(event_dicts)} event(s)')

	def _parse_start_time(s):
		dt = datetime.fromisoformat(s)
		return make_aware(dt, timezone.utc) if is_naive(dt) else dt

	with transaction.atomic():
		Event.objects.bulk_create(
			[Event(
				espn_id=d['espn_id'],
				league=d['league'],
				season=d['season'],
				season_type=d['season_type'],
				event_key=d['event_key'],
				away_team=d['away_team'],
				home_team=d['home_team'],
				start_time=_parse_start_time(d['start_time']),
				status=d['status'],
			) for d in event_dicts],
			update_conflicts=True,
			unique_fields=['event_key'],
			update_fields=['espn_id', 'league', 'season', 'season_type', 'away_team', 'home_team', 'start_time', 'status'],
		)


@shared_task(queue='scraping')
def sync_players(sport: str, league: str, team_key: str):
	logger.info(f'Syncing {team_key} roster...')
	client = ESPNClient(sport, league)
	_, upsert_players = client.get_players(team_key)
	if upsert_players:
		upsert_players_db.delay([p.to_dict() for p in upsert_players])


@shared_task(queue='database')
def upsert_players_db(player_dicts: list):
	logger.info(f'Upserting {len(player_dicts)} player(s)')
	with transaction.atomic():
		Player.objects.bulk_create(
			[Player(
				espn_id=d['espn_id'],
				league=d['league'],
				player_key=d['player_key'],
				team_key=d['team_key'],
				name=d['name'],
				position=d['position'],
			) for d in player_dicts],
			update_conflicts=True,
			unique_fields=['player_key'],
			update_fields=['espn_id', 'league', 'team_key', 'name', 'position'],
		)
