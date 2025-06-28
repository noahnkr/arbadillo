import logging

from celery import shared_task
from django.utils.dateparse import parse_datetime

from sportsdata.models import Team, Player, Event
from sportsdata.apiclients.espn import ESPNClient

logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def sync_teams(sport: str, league: str):
	logger.info('Syncing teams...')
	client = ESPNClient(sport, league)
	teams = client.get_teams()

	logger.info(f'Upserting {len(teams)} team(s)')
	for team in teams:
		Team.objects.update_or_create(
			team_key=team['team_key'],
			defaults={
				'espn_id': team['espn_id'],
				'league': team['league'],
				'name': team['name'],
			}
		)
	
	return teams


@shared_task(queue='scraping')
def sync_schedule(sport: str, league: str):
	logger.info('Syncing ESPN schedule...')
	client = ESPNClient(sport, league)
	events = client.get_schedule()

	logger.info(f'Upserting {len(events)} event(s)')
	for event in events:
		try:
			away_team = Team.objects.get(team_key=event['away_team_key'])
			home_team = Team.objects.get(team_key=event['home_team_key'])

			Event.objects.update_or_create(
				event_key=event['event_key'],
				defaults={
					'espn_id': event['espn_id'],
					'league': event['league'],
					'away_team': away_team,
					'home_team': home_team,
					'start_time': parse_datetime(event['start_time']),
					'status': event['status'],
				}
			)
		except Team.DoesNotExist:
			logger.warning(f'Missing team(s) record for event {event["event_key"]} ({league})')
			continue


@shared_task(queue='scraping')
def sync_players(sport: str, league: str, team_id: str):
	logger.info(f'Syncing team {team_id} roster...')
	client = ESPNClient(sport, league)
	players = client.get_roster(team_id)

	logger.info(f'Upserting {len(players)} player(s)')
	for player in players:
		try:
			team = Team.objects.get(team_key=player['team_key'])

			Player.objects.update_or_create(
				espn_id=player['espn_id'],
				defaults={
					'league': player['league'],
					'name': player['name'],
					'team': team,
					'player_key': player['player_key'],
					'position': player['position'],
				}
			)
		except Team.DoesNotExist:
			logger.warning(f'Missing team record for player {player["name"]} ({league})')
			continue