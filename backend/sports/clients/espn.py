import json
import requests
import logging

from datetime import datetime, timedelta
from dateutil import tz
from redis import Redis
from django.conf import settings

from sports.dto import (
    TeamData, 
    PlayerData, 
    EventData
)
from common.utils.sportsbook_helpers import (
    create_event_key, 
	get_team_key,
	normalize_status_name, 
)
from common.constants.sportsbook_definitions import EVENT_TTL, EVENT_STATUSES
from common.exceptions import NormalizationError

class ESPNClient:
	NAME = 'espn'
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
		self.logger = logging.getLogger(self.NAME)

	def _get(self, path: str, params: dict = None):
		url = f'{self.BASE_URL}/{self.sport}/{self.league}{path}'
		response = requests.get(url, params=params)
		response.raise_for_status()
		return response.json()

	def get_teams(self) -> tuple[list[TeamData], list[TeamData]]:
		teams = []

		raw = self._get('/teams')
		for team in raw['sports'][0]['leagues'][0]['teams']:
			try:
				teams.append(self.parse_team(team['team']))
			except NormalizationError as e:
				self.logger.warning(e)
				continue

		upsert_teams = []
		for team in teams:
			self.redis.sadd(f'teams:{self.league}', team.team_key)

			team_hash = str(hash(team))
			redis_key = f'teams:{self.league}:{team.espn_id}'
			redis_hash_key = f'teams:hashes:{self.league}:{team.espn_id}'
			prev_hash = self.redis.get(redis_hash_key)

			if prev_hash != team_hash:
				upsert_teams.append(team)
				self.redis.set(redis_key, json.dumps(team.to_dict()))
				self.redis.set(redis_hash_key, team_hash)
				self.redis.set(f'teams:keys:{self.league}:{team.espn_id}', team.team_key)
				self.redis.set(f'teams:ids:{self.league}:{team.team_key}', team.espn_id)
				self.logger.debug(f'Updated team {team}')

		self.logger.info(f'Scraped {len(upsert_teams)} team(s) ({self.league})')
		return teams, upsert_teams

	def get_roster(self, team_key) -> tuple[list[PlayerData], list[PlayerData]]:
		team_id = self.redis.get(f'teams:ids:{self.league}:{team_key}')
		if not team_id:
			self.logger.warning(f'Missing ESPN id for {team_key} ({self.league})')
			return []

		raw = self._get(f'/teams/{team_id}/roster')
		players = [self.parse_player(p, team_key) for position in raw['athletes'] for p in position['items']]

		upsert_players = []
		for player in players:
			self.redis.sadd(f'players:{self.league}', player.name)

			player_hash = str(hash(player))
			redis_key = f'players:{self.league}:{player.espn_id}'
			redis_hash_key = f'players:hashes:{self.league}:{player.espn_id}'
			prev_hash = self.redis.get(redis_hash_key)

			if prev_hash != player_hash:
				upsert_players.append(player)
				self.redis.set(redis_key, json.dumps(player.to_dict()))
				self.redis.set(redis_hash_key, player_hash)
				self.redis.set(f'players:keys:{self.league}:{player.espn_id}', player.player_key)
				self.redis.set(f'players:ids:{self.league}:{player.player_key}', player.espn_id)
				self.logger.debug(f'Scraped player {player}')
		
		self.logger.info(f'Scraped {len(upsert_players)} player(s) ({self.league})')
		return players, upsert_players

	def get_schedule(self) -> tuple[list[EventData], list[EventData]]:
		events = []
		central = tz.gettz('America/Chicago')
		for days in range(0, 3):
			date = (datetime.now(tz=central) + timedelta(days=days)).strftime('%Y%m%d')
			raw = self._get('/scoreboard', params={'dates': date})
			events.extend(self.parse_event(e) for e in raw['events'])
		
		upsert_events = []
		for event in events:
			if not event.away_team_key or not event.home_team_key:
				self.logger.warning(f'Missing team(s) for ESPN event id {event.espn_id}')
				continue

			self.redis.sadd(f'events:{self.league}:{event.status}', event.event_key)
			for s in EVENT_STATUSES:
				if s != event.status:
					self.redis.srem(f'events:{self.league}:{s}', event.event_key)

			event_hash = str(hash(event))
			redis_key = f'events:{self.league}:{event.espn_id}'
			redis_hash_key  = f'events:hashes:{self.league}:{event.espn_id}'
			prev_hash = self.redis.get(redis_hash_key)

			if prev_hash != event_hash:
				upsert_events.append(event)
				self.redis.set(redis_key, json.dumps(event.to_dict()), ex=EVENT_TTL)
				self.redis.set(redis_hash_key, event_hash, ex=EVENT_TTL)
				self.redis.set(f'events:keys:{self.league}:{event.espn_id}', event.event_key, ex=EVENT_TTL)
				self.redis.set(f'events:ids:{self.league}:{event.event_key}', event.espn_id, ex=EVENT_TTL)
				self.logger.debug(f'Updated event {event}')

		self.logger.info(f'Scraped {len(upsert_events)} event(s) ({self.league})')
		return events, upsert_events
	
	def parse_team(self, team_json) -> TeamData:
		return TeamData(
			espn_id=int(team_json['id']),
			league=self.league,
			team_key=get_team_key(team_json['displayName'], self.league),
			name=team_json['displayName'],
		)

	def parse_player(self, player_json, team_key) -> PlayerData:
		return PlayerData(
			espn_id=player_json['id'],
			league=self.league,
			player_key=player_json['slug'],
			team_key=team_key,
			name=player_json['displayName'],
			position=player_json['position']['name'],
		)

	def parse_event(self, event_json) -> EventData:
		competitors = event_json['competitions'][0]['competitors']
		away_team_id = competitors[0]['id'] if competitors[0]['homeAway'] == 'away' else competitors[1]['id']
		home_team_id = competitors[0]['id'] if competitors[0]['homeAway'] == 'home' else competitors[1]['id']

		away_team_key = self.redis.get(f'teams:keys:{self.league}:{away_team_id}')
		home_team_key = self.redis.get(f'teams:keys:{self.league}:{home_team_id}')

		start_time = datetime.strptime(event_json['date'], '%Y-%m-%dT%H:%MZ')
		start_date = start_time.strftime('%Y-%m-%d')
		event_key = create_event_key(start_date, away_team_key, home_team_key)

		return EventData(
			espn_id=event_json['id'],
			league=self.league,
			event_key=event_key,
			away_team_key=away_team_key,
			home_team_key=home_team_key,
			start_time=start_time,
			status=normalize_status_name(event_json['status']['type']['state'], is_odds=False),
		)