import logging
import requests
import json

from abc import ABC, abstractmethod
from django.conf import settings
from urllib.parse import urlencode
from redis import Redis

from common.utils.sportsbook import (
    generate_data_hash, format_odds, normalize_market_name, normalize_market_outcome, 
    correct_over_under_line, normalize_status_name, create_market_key, get_team_key
)
from common.constants.sportsbook import EVENT_TTL, ODDS_TTL
from common.exceptions import NormalizationError

class SportsbookClient(ABC):

    def __init__(self, name: str, sport: str, league: str):
        self.name = name
        self.sport = sport
        self.league = league
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.logger = logging.getLogger(f'oddsdata.apiclients.{self.name}')

    def _get(self, url, headers=None, params=None, method='requests', context=None, page=None):
        default_headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		}
        final_headers = { **default_headers, **(headers or {}) }

        self.logger.info(f'Yielding request to {url} ({self.league})')
        try:
            if method == 'requests':
                response = requests.get(url, headers=final_headers, params=params)
                response.raise_for_status()
                return response.json()

            elif method == 'playwright_request':
                if not context:
                    raise ValueError('Playwright context is required for method=`playwright_request`')
                response = context.request.get(url, headers=final_headers, params=params)
                return response.json()

            elif method == 'page_evaluate_fetch':
                if not page:
                    raise ValueError('Playwright page is required for method=`page_evaluate_fetch`')

                query_str = '?' + urlencode(params or {}, doseq=True)
                js  = f"""
                    async () => {{
                        const res = await fetch("{url}{query_str}", {{
                            method: 'GET',
                            headers: {final_headers}
                        }});
                        return await res.json();
                    }}
                """
                return page.evaluate(js)

            else:
                raise ValueError(f'Unknown method `{method}`')

        except Exception as e:
            self.logger.exception(f'An error occured while yielding request to {url}: {e} ({self.league})')
            return {}

    def match_espn_key(self, event_key, event_id):
        if self.redis.exists(f'events:{event_key}'):
            self.redis.set(f'{self.name}:keys:{event_id}', event_key, ex=EVENT_TTL)
            self.redis.set(f'{self.name}:ids:{event_key}', event_id, ex=EVENT_TTL)
            self.logger.info(f'Matched {event_key} to ESPN schedule ({self.league})')
        else:
            self.logger.debug(f'Unable to match {event_key} to ESPN schedule ({self.league})')
    
    def compare_and_update_odds_cache(self, odds_data) -> bool:
        odds_hash = generate_data_hash(odds_data)
        redis_key = f'{self.name}:odds:{odds_data["event_key"]}:{odds_data["market_key"]}:{odds_data["outcome"]}'
        redis_hash_key = f'{self.name}:hashes:{odds_data["event_key"]}:{odds_data["market_key"]}:{odds_data["outcome"]}'
        prev_hash = self.redis.get(redis_hash_key)

        if prev_hash != odds_hash:
            # Odds data have changed, cache odds and update DB
            self.redis.set(redis_key, json.dumps(odds_data), ex=ODDS_TTL)
            self.redis.set(redis_hash_key, odds_hash, ex=ODDS_TTL)
            self.logger.info(f'Updated {format_odds(odds_data)} for {odds_data["event_key"]}')
            return True

        return False

    def parse_selection(self, event_key, name, outcome, line=None, value=0, team=None, player=None, status='active'):
        market_name, market_type, market_line, market_team, market_player = normalize_market_name(name, self.league)
        outcome_name, outcome_player, outcome_line = normalize_market_outcome(outcome, market_type, self.league)

        if not line:
            line = correct_over_under_line(market_type, market_line) if market_line else correct_over_under_line(market_type, outcome_line)

        if not player:
            player = market_player if market_player else outcome_player

        if not team:
            team = market_team if market_team else None
            team = get_team_key(team, self.league)
        elif outcome_name == team:
            team = None # Remove redundant 'team' value
            outcome_name = get_team_key(outcome_name, self.league)
        
        value = float(round(value, 3))
        status = normalize_status_name(status)
        market_key = create_market_key(market_name, line, team, player)

        odds_data = {
			'event_key': event_key,
			'market_key': market_key,
			'sportsbook': self.name,
			'market': market_name,
			'outcome': outcome_name,
			'line': line,
			'value': value,
			'team': team,
			'player': player,
			'status': status
		}

        # Validate selection format
        invalid_selection = (
            (market_type in {'spread','total','over_under'} and not line) or
            (market_type in {'total','over_under'} and outcome_name not in {'over','under'}) or
            (market_type == {'yes_no'} and outcome not in {'yes','no'})
        )
        if invalid_selection:
            raise NormalizationError(f'Parsed selection is invalid: {format_odds(odds_data)} ({self.league})')

        if player and not self.redis.sismember(f'players:{self.league}', player):
            raise NormalizationError(f'Unknown player: {player}')

        return odds_data

    @abstractmethod
    def get_events(self):
        pass

    @abstractmethod
    def parse_events(self):
        pass

    @abstractmethod
    def get_markets(self, event_key):
        pass

    @abstractmethod
    def parse_markets(self, event_key):
        pass