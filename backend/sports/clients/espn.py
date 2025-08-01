import json
import requests
import logging
import time

from requests import HTTPError
from datetime import datetime, timedelta
from dateutil import tz
from redis import Redis
from django.conf import settings

from sports.dto import (
    TeamData, 
    PlayerData, 
    EventData,
	EventResultData,
	PlayerStatData,
	TeamStatData,
)
from common.constants.aliases import (
	EFFICIENCY_STATS, REVERSE_STATS_LOOKUP,
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
	V2_BASE_URL = 'https://site.api.espn.com/apis/site/v2/sports'
	V3_BASE_URL = 'https://site.web.api.espn.com/apis/common/v3/sports'

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

	def _get(self, path: str, params: dict = None, v2: bool = True):
		base_url = self.V2_BASE_URL if v2 else self.V3_BASE_URL
		url = f'{base_url}/{self.sport}/{self.league}{path}'

		retries = 3
		got_response = False
		while retries > 0 and not got_response:
			try:
				response = requests.get(url, params=params)
				response.raise_for_status()
				got_response = True
			except HTTPError:
				self.logger.warning(f'A HTTPError occured while yielding request to {url}. Retrying {retries} more times...')
				retries -= 1
				time.sleep(3)
		
		if retries == 0 and not got_response:
			self.logger.critical(f'Unable to recieve response from {url}')
			return {}

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

	def get_players(self, team_key) -> tuple[list[PlayerData], list[PlayerData]]:
		team_id = self.redis.get(f'teams:ids:{self.league}:{team_key}')
		if not team_id:
			self.logger.warning(f'Missing ESPN id for {team_key} players ({self.league})')
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

	def get_events(self, team_key, season) -> list[EventData]:
		team_id = self.redis.get(f'teams:ids:{self.league}:{team_key}')
		if not team_id:
			self.logger.warning(f'Unknown ESPN id for {team_key} events ({self.league})')
			return []

		events = []
		for season_type in range(2, 4):
			raw = self._get(f'/teams/{team_id}/schedule', params={'season': season, 'seasontype': season_type})
			events.extend([
				self.parse_event(competition)
				for event in raw['events']
				for competition in event['competitions']
			])
		
		for event in events:
			self.redis.set(f'events:keys:{self.league}:{event.espn_id}', event.event_key, ex=EVENT_TTL)
			self.redis.set(f'events:ids:{self.league}:{event.event_key}', event.espn_id, ex=EVENT_TTL)
		
		self.logger.info(f'Scraped {len(events)} events for {season} {team_key} ({self.league})')
		return events

	def get_upcoming_events(self, days=3) -> tuple[list[EventData], list[EventData]]:
		events = []
		central = tz.gettz('America/Chicago')
		for days in range(0, days):
			date = (datetime.now(tz=central) + timedelta(days=days)).strftime('%Y%m%d')
			raw = self._get('/scoreboard', params={'dates': date})
			events.extend([
				self.parse_event(competition)
				for event in raw['events']
				for competition in event['competitions']
			])
		
		upsert_events = []
		for event in events:
			if not event.away_team or not event.home_team:
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
	
	def get_event_stats(self, event_key) -> tuple[EventResultData, list[TeamStatData], list[TeamStatData]]:
		event_id = self.redis.get(f'events:ids:{self.league}:{event_key}')
		if not event_id:
			self.logger.warning(f'Missing ESPN id for {event_key} stats ({self.league})')
			return [], []

		raw = self._get(f'/summary', params={'event': event_id})
		event_results, away_team_stats, home_team_stats = self.parse_event_stats(raw, event_key)
		self.logger.info(f'Scraped {len(away_team_stats + home_team_stats)} stats for {event_key} ({self.league})')

		return event_results, away_team_stats, home_team_stats

	def get_player_stats(self, player_key, season) -> list[PlayerStatData]:
		player_id = self.redis.get(f'players:ids:{self.league}:{player_key}')
		if not player_id:
			self.logger.warning(f'Missing ESPN id for {player_key} stats ({self.league})')
			return []
		
		raw = self._get(f'/athletes/{player_id}/gamelog', params={'season': season, 'seasontype': '2,3'}, v2=False)
		player_stats = self.parse_player_stats(raw, player_key)

		self.logger.info(f'Scraped {len(player_stats)} stats for {season} {player_key} ({self.league})')
		return player_stats

	def parse_team(self, team_json) -> TeamData:
		return TeamData(
			espn_id=int(team_json['id']),
			league=self.league,
			team_key=get_team_key(team_json['displayName'], self.league),
			name=team_json['displayName'],
		)

	def parse_event_stats(self, event_stats_json, event_key) -> tuple[EventResultData, list[TeamStatData], list[TeamStatData]]:
		away_team_stats, home_team_stats = [], []

		# Collect event results stats for labels
		event_results_kwargs = { 'league': self.league, 'event_key': event_key }
		event_scoring_kwargs = { 'away_team': {}, 'home_team': {} }

		for team in event_stats_json['header']['competitions'][0]['competitors']:
			team_key = self.redis.get(f'teams:keys:{self.league}:{team["id"]}')
			is_away = team['homeAway'] == 'away'
			is_winner = team['winner']

			if is_winner:
				event_results_kwargs['winner'] = team_key

			score_key = ('away_score' if is_away else 'home_score')
			score = int(team['score'])
			event_results_kwargs[score_key] = score

			event_scoring_kwargs[('away_team' if is_away else 'home_team')]['team_key'] = team_key
			event_scoring_kwargs[('away_team' if is_away else 'home_team')]['points_scored'] = score
			event_scoring_kwargs[('home_team' if is_away else 'away_team')]['points_allowed'] = score

		event_results_kwargs['margin_of_victory'] = abs(event_results_kwargs['away_score'] - event_results_kwargs['home_score'])
		event_results_kwargs['total_points'] = event_results_kwargs['away_score'] + event_results_kwargs['home_score']
		event_results = EventResultData(**event_results_kwargs)

		# Collect team scoring results for features
		for home_away, scoring in event_scoring_kwargs.items():
			is_away = home_away == 'away_team'

			(away_team_stats if is_away else home_team_stats).extend([
				TeamStatData(
					league=self.league,
					event_key=event_key,
					team_key=scoring['team_key'],
					stat_name='points_scored',
					value=scoring['points_scored']
				),
				TeamStatData(
					league=self.league,
					event_key=event_key,
					team_key=scoring['team_key'],
					stat_name='points_allowed',
					value=scoring['points_allowed']
				)
			])

		# Collect team event stats
		for team in event_stats_json['boxscore']['teams']:
			team_key = self.redis.get(f'teams:keys:{self.league}:{team["team"]["id"]}')
			is_away = team['homeAway'] == 'away'

			for team_stat in team['statistics']:
				label = team_stat['label']
				value = team_stat['displayValue']

				if label in EFFICIENCY_STATS:
					try:
						sep = '-' if '-' in value else '/'
						num, denom = map(int, value.split(sep))
						conv_name, att_name = EFFICIENCY_STATS[label]

						conv_stat = TeamStatData(
							league=self.league,
							event_key=event_key,
							team_key=team_key,
							stat_name=conv_name,
							value=float(num),
						)

						att_stat = TeamStatData(
							league=self.league,
							event_key=event_key,
							team_key=team_key,
							stat_name=att_name,
							value=float(denom),
						)

						(away_team_stats if is_away else home_team_stats).extend([conv_stat, att_stat])
					except Exception as e:
						self.logger.warning(f'Failed to parse efficiency stat {label} ({value}): {e}')

				else:
					try:
						stat_name = REVERSE_STATS_LOOKUP.get((self.league, label))
						if stat_name is None or '-' in value:
							continue
						
						# Parse time stat
						if ':' in value:
							mins, secs = value.split(':')
							value = int(mins) * 60 + int(secs)

						stat = TeamStatData(
							league=self.league,
							event_key=event_key,
							team_key=team_key,
							stat_name=stat_name,
							value=round(float(value), 3)
						)

						(away_team_stats if is_away else home_team_stats).append(stat)
					except Exception as e:
						self.logger.warning(f'Failed to parse stat {label} ({value}): {e}')
		
		return event_results, away_team_stats, home_team_stats

	def parse_player(self, player_json, team_key) -> PlayerData:
		return PlayerData(
			espn_id=player_json['id'],
			league=self.league,
			player_key=player_json['slug'],
			team_key=team_key,
			name=player_json['displayName'],
			position=player_json['position']['name'],
		)

	def parse_player_stats(self, player_stats_json, player_key) -> list[PlayerStatData]:
		try:
			stat_names = [
				REVERSE_STATS_LOOKUP[(self.league, name)]
				if (self.league, name) in REVERSE_STATS_LOOKUP
				else None
				for name in player_stats_json.get('displayNames', [])
			]
			events = [
				event
				for season_type in player_stats_json.get('seasonTypes', [])
				for category in season_type.get('categories', [])
				for event in category.get('events', [])
			]
		except Exception as e:
			self.logger.warning(f'An error occured while collecting game log for {player_key} ({self.league}): {e}')
			return []

		player_stats = []
		for event in events:
			event_key = self.redis.get(f'events:keys:{self.league}:{event["eventId"]}')

			if event_key is None:
				self.logger.warning(f'Unknown event key for ESPN id {event["eventId"]} for {player_key} ({self.league})')
				continue

			stats = event.get('stats', [])
			for i, value in enumerate(stats):
				if stat_names[i] is None or '-' in value:
					continue

				player_stats.append(PlayerStatData(
					league=self.league,
					event_key=event_key,
					player_key=player_key,
					stat_name=stat_names[i],
					value=round(float(value), 3)
				))
		
		return player_stats

	def parse_event(self, event_json) -> EventData:
		competitors = event_json['competitors']
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
			away_team=away_team_key,
			home_team=home_team_key,
			start_time=start_time,
			status=normalize_status_name(event_json['status']['type']['state'], is_odds=False),
		)