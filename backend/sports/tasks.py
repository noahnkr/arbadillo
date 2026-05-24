import logging

from django.utils.timezone import is_naive, make_aware
from django.db import transaction
from celery import shared_task
from datetime import timezone

from sports.models import Team, Player, Event
from sports.clients.espn import ESPNClient

logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def sync_teams(sport: str, league: str):
	logger.info('Syncing teams...')
	client = ESPNClient(sport, league)
	teams, upsert_teams = client.get_teams()

	if upsert_teams:
		logger.info(f'Upserting {len(upsert_teams)} team(s)')
		with transaction.atomic():
			Team.objects.bulk_create(
				[Team(espn_id=t.espn_id, league=t.league, team_key=t.team_key, name=t.name)
				 for t in upsert_teams],
				update_conflicts=True,
				unique_fields=['team_key'],
				update_fields=['espn_id', 'league', 'name'],
			)
	return [t.to_dict() for t in teams]


@shared_task(queue='scraping')
def sync_schedule(sport: str, league: str):
	logger.info('Syncing ESPN schedule...')
	client = ESPNClient(sport, league)
	_, upsert_events = client.get_upcoming_events()

	if upsert_events:
		logger.info(f'Upserting {len(upsert_events)} event(s)')
		with transaction.atomic():
			Event.objects.bulk_create(
				[Event(
					espn_id=e.espn_id,
					league=e.league,
					season=e.season,
					season_type=e.season_type,
					event_key=e.event_key,
					away_team=e.away_team,
					home_team=e.home_team,
					start_time=make_aware(e.start_time, timezone.utc) if is_naive(e.start_time) else e.start_time,
					status=e.status,
				) for e in upsert_events],
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
		logger.info(f'Upserting {len(upsert_players)} player(s)')
		with transaction.atomic():
			Player.objects.bulk_create(
				[Player(
					espn_id=p.espn_id,
					league=p.league,
					player_key=p.player_key,
					team_key=p.team_key,
					name=p.name,
					position=p.position,
				) for p in upsert_players],
				update_conflicts=True,
				unique_fields=['player_key'],
				update_fields=['espn_id', 'league', 'team_key', 'name', 'position'],
			)