import logging

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
	_, upsert_events = client.get_schedule()

	logger.info(f'Upserting {len(upsert_events)} event(s)')
	for event in upsert_events:
		try:
			away_team = Team.objects.get(team_key=event.away_team_key)
			home_team = Team.objects.get(team_key=event.home_team_key)

			start_time = event.start_time.replace(tzinfo=timezone.utc)

			Event.objects.update_or_create(
				event_key=event.event_key,
				defaults={
					'espn_id': event.espn_id,
					'league': event.league,
					'away_team': away_team,
					'home_team': home_team,
					'start_time': start_time,
					'status': event.status,
				}
			)
		except Team.DoesNotExist:
			logger.warning(f'Missing team(s) record for {event}')


@shared_task(queue='scraping')
def sync_players(sport: str, league: str, team_key: str):
	logger.info(f'Syncing {team_key} roster...')
	client = ESPNClient(sport, league)
	_, upsert_players = client.get_roster(team_key)

	logger.info(f'Upserting {len(upsert_players)} player(s)')
	try:
		team = Team.objects.get(team_key=team_key)
	except Team.DoesNotExist:
		logger.warning(f'Missing team record for {team_key}')
		return

	for player in upsert_players:
		Player.objects.update_or_create(
			espn_id=player.espn_id,
			defaults={
				'league': player.league,
				'name': player.name,
				'team': team,
				'player_key': player.player_key,
				'position': player.position,
			}
		)