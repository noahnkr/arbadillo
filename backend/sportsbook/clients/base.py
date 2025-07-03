import logging
import requests
import json

from abc import ABC, abstractmethod
from django.conf import settings
from urllib.parse import urlencode
from redis import Redis

from sportsbook.dto import SelectionData

from common.utils.sportsbook_helpers import (
    create_market_key, 
    get_team_key,
    parse_market_name, 
    parse_market_outcome, 
    correct_over_under_line, 
    normalize_status_name, 
)
from common.utils.client import init_browser
from common.constants.sportsbook_definitions import EVENT_TTL, ODDS_TTL
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
        self.context = init_browser().new_context()
        self.logger = logging.getLogger(self.name)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        self.context.close()

    def _get(self, url, headers=None, params=None, method='request', intercept_query=None):
        default_headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		}
        final_headers = { **default_headers, **(headers or {}) }

        self.logger.info(f'Yielding request to {url} ({self.league})')
        try:
            if method == 'request':
                response = self.context.request.get(url, headers=final_headers, params=params)
                return response.json()

            elif method == 'page_evaluate_fetch':
                page = self.context.new_page()
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

            elif method == 'page_intercept':
                if not intercept_query:
                    raise ValueError('Parameter intercept_query is required for method=`page_intercept`')

                page = self.context.new_page() 
                found = False
                data = None

                def handle_response(response):
                    nonlocal found, data
                    if intercept_query in response.url:
                        body = response.text()
                        parsed = json.loads(body)
                        data = parsed
                        found = True
                
                page.on('response', handle_response)
                page.goto(url)

                while not found:
                    page.wait_for_timeout(500)

                return data

            else:
                raise ValueError(f'Unknown method `{method}`')

        except Exception as e:
            self.logger.exception(f'An error occured while yielding request to {url}: {e} ({self.league})')
            return {}

    def match_espn_key(self, event_key, event_id):
        if self.redis.exists(f'events:ids:{self.league}:{event_key}'):
            self.redis.set(f'{self.name}:keys:{self.league}:{event_id}', event_key, ex=EVENT_TTL)
            self.redis.set(f'{self.name}:ids:{self.league}:{event_key}', event_id, ex=EVENT_TTL)
            self.logger.info(f'Matched {event_key} to ESPN schedule ({self.league})')
        else:
            self.logger.warning(f'Unable to match {event_key} to ESPN schedule ({self.league})')
    
    def compare_and_update_selection(self, selection: SelectionData) -> bool:
        selection_hash = str(hash(selection))
        redis_key = f'{self.name}:selections:{self.league}:{selection.event_key}:{selection.market_key}:{selection.outcome}'
        redis_hash_key = f'{self.name}:hashes:{self.league}:{selection.event_key}:{selection.market_key}:{selection.outcome}'
        prev_hash = self.redis.get(redis_hash_key)

        if prev_hash != selection_hash:
            self.redis.set(redis_key, json.dumps(selection.to_dict()), ex=ODDS_TTL)
            self.redis.set(redis_hash_key, selection_hash, ex=ODDS_TTL)
            self.logger.debug(f'Updated {selection} for {selection.event_key} ({self.league})')
            return True

        return False

    def parse_selection(self, event_key, market_name, outcome_name, value=0, line=None, team=None, player=None, status='active'):
        market, market_type, market_line, market_team, market_player = parse_market_name(market_name, self.league)
        outcome, outcome_player, outcome_line = parse_market_outcome(outcome_name, market_type, self.league)

        if not line:
            line = correct_over_under_line(market_type, market_line) if market_line else correct_over_under_line(market_type, outcome_line)

        if not player:
            player = market_player if market_player else outcome_player

        if not team:
            team = market_team
        else:
            team = get_team_key(team, self.league)

        if outcome == team:
            team = None # Remove redundant 'team' value
        
        value = float(round(value, 3))
        status = normalize_status_name(status)
        market_key = create_market_key(market, line, team, player)

        selection = SelectionData(
            sportsbook=self.name,
            league=self.league,
			event_key=event_key,
			market_key=market_key,
			market=market,
			outcome=outcome,
			value=value,
            line=line,
			team=team,
			player=player,
			status=status,
		)

        # Validate selection format
        invalid_selection = (
            (market_type in {'spread','total','over_under'} and not line) or
            (market_type in {'total','over_under'} and outcome not in {'over','under'}) or
            (market_type == 'yes_no' and outcome not in {'yes','no'})
        )
        if invalid_selection:
            raise NormalizationError(f'Selection is invalid: {selection} ({self.league})')

        if player and not self.redis.sismember(f'players:{self.league}', player):
            raise NormalizationError(f'Unknown player: {player}')

        return selection

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
    def parse_markets(self, event_key) -> list[SelectionData]:
        pass

    @abstractmethod
    def export_markets(self, event_key):
        pass