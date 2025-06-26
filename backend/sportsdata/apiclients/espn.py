import json
import requests
import logging

from typing import Any
from datetime import datetime, timedelta
from dateutil import tz
from redis import Redis
from django.conf import settings

from sportsdata.parsers.espn import parse_team, parse_event, parse_player
from common.utils.sportsbook import create_event_key, generate_data_hash, normalize_status_name
from common.constants.sportsbook import EVENT_TTL, EVENT_STATUSES

class ESPNClient:
	BASE_URL = 'https://site.api.espn.com/apis/site/v2/sports'

	def __init__(self, sport: str, league: str):
		self.sport = sport
		self.league = league
		self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
		self.logger = logging.getLogger(__name__)
	

	def _get(self, path: str, params: dict = None) -> Any:
		url = f'{self.BASE_URL}/{self.sport}/{self.league}{path}'
		response = requests.get(url, params=params)
		response.raise_for_status()
		return response.json()
	

	def get_teams(self) -> list:
		raw = self._get('/teams')
		teams = [parse_team(team['team']) for team in raw['sports'][0]['leagues'][0]['teams']]
		for team in teams:
			self.redis.sadd(f'teams:{self.league}', team['team_key'])
			self.redis.set(f'teams:{self.league}:{team["team_key"]}', json.dumps(team))
			self.redis.set(f'teams:keys:{self.league}:{team["espn_id"]}', team['team_key'])
			self.redis.set(f'teams:ids:{self.league}:{team["team_key"]}', team['espn_id'])
			for alias in team['aliases']:
				self.redis.set(f'teams:aliases:{self.league}:{alias}', team['team_key'])
			self.logger.debug(f'Scraped team {team["team_key"]} ({self.league})')

		self.logger.info(f'Scraped {len(teams)} team(s) ({self.league})')
		return teams
	

	def get_schedule(self) -> list:
		raw_events = []
		central = tz.gettz('America/Chicago')
		for days in range(0, 7):
			date = (datetime.now(tz=central) + timedelta(days=days)).strftime('%Y%m%d')
			raw = self._get('/scoreboard', params={'date': date})
			raw_events.extend(parse_event(event, self.league) for event in raw['events'])
		
		events = []
		for event in raw_events:
			away_team_key = self.redis.get(f'teams:keys:{self.league}:{event["away_team_id"]}')
			home_team_key = self.redis.get(f'teams:keys:{self.league}:{event["home_team_id"]}')

			if not away_team_key or not home_team_key:
				self.logger.warning(f'Missing team(s) cache for espn event id={event["espn_id"]} ({self.league})')

			start_date = event['start_time'].split('T')[0]
			event_key = create_event_key(self.league, start_date, away_team_key, home_team_key)

			status = normalize_status_name(event['status'], is_odds=False)
			self.redis.sadd(f'events:{self.league}:{status}')
			for s in EVENT_STATUSES:
				if s != status:
					self.redis.srem(f'events:{self.league}:{s}')

			event_data = {
				'espn_id': event['espn_id'],
				'event_key': event_key,
				'league': self.league,
				'away_team_key': away_team_key,
				'home_team_key': home_team_key,
				'status': status
			}

			event_hash = generate_data_hash(event_data)
			prev_hash = self.redis.get(f'events:hashes:{event_key}')
			if prev_hash != event_hash:
				# Event data has changed, cache event and update DB
				events.append(event_data)
				self.redis.set(f'events:{event_key}', json.dumps(event_data), ex=EVENT_TTL)
				self.redis.set(f'events:keys:{event_data["espn_id"]}', event_key, ex=EVENT_TTL)
				self.redis.set(f'events:ids:{event_key}', event_data["espn_id"], ex=EVENT_TTL)
				self.redis.set(f'events:hashes:{event_key}', event_hash, ex=EVENT_TTL)
				self.logger.debug(f'Scraped event {event_key} ({self.league})')

		self.logger.info(f'Scraped {len(events)} event(s) ({self.league})')
		return events

	
	def get_roster(self, team_id) -> list:
		raw = self._get(f'/teams/{team_id}/roster')
		raw_players = [parse_player(player) for position in raw['athletes'] for player in position['items']]

		players = []
		for player in raw_players:
			team_key  = self.redis.get(f'teams:keys:{self.league}:{team_id}')

			if not team_key:
				self.logger.warning(f'Missing team cache for espn player id={player["espn_id"]} ({self.league})')

			player_data = {'team_key': team_key, **player}

			player_hash = generate_data_hash(player_data)
			prev_hash = self.redis.get(f'players:hashes:{self.league}:{player_data["espn_id"]}')
			if prev_hash != player_hash:
				players.append(player_data)
				self.redis.set(f'players:{self.league}:{player_data["espn_id"]}', json.dumps(player_data))
				self.redis.set(f'players:keys:{self.league}:{player_data["espn_id"]}', player_data["player_key"])
				self.redis.set(f'players:ids:{self.league}:{player_data["player_key"]}', player_data["espn_id"])
				self.redis.set(f'players:hashes:{self.league}:{player_data["espn_id"]}', player_hash)
				self.logger.debug(f'Scraped player {player_data["name"]} ({self.league})')
		
		self.logger.info(f'Scraped {len(players)} player(s) ({self.league})')
		return players