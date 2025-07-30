import logging

from django.utils.timezone import is_naive, make_aware
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

	logger.info(f'Upserting {len(upsert_teams)} team(s)')
	for team in upsert_teams:
		Team.objects.update_or_create(
			team_key=team.team_key,
			defaults={
				'espn_id': team.espn_id,
				'league': team.league,
				'name': team.name,
			}
		)
	return [t.to_dict() for t in teams]


@shared_task(queue='scraping')
def sync_schedule(sport: str, league: str):
	logger.info('Syncing ESPN schedule...')
	client = ESPNClient(sport, league)
	_, upsert_events = client.get_upcoming_events()

	logger.info(f'Upserting {len(upsert_events)} event(s)')
	for event in upsert_events:
		Event.objects.update_or_create(
			event_key=event.event_key,
			defaults={
				'espn_id': event.espn_id,
				'league': event.league,
				'away_team': event.away_team,
				'home_team': event.home_team,
				'start_time': make_aware(event.start_time, timezone.utc) if is_naive(event.start_time) else event.start_time,
				'status': event.status,
				'collected_at': event.collected_at,
			}
		)


@shared_task(queue='scraping')
def sync_players(sport: str, league: str, team_key: str):
	logger.info(f'Syncing {team_key} roster...')
	client = ESPNClient(sport, league)
	_, upsert_players = client.get_players(team_key)

	logger.info(f'Upserting {len(upsert_players)} player(s)')

	for player in upsert_players:
		Player.objects.update_or_create(
			player_key=player.player_key,
			defaults={
				'espn_id': player.espn_id,
				'league': player.league,
				'team_key': player.team_key,
				'name': player.name,
				'position': player.position,
			}
		)