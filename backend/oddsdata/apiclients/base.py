import logging
import requests
import json

from abc import ABC, abstractmethod
from django.conf import settings
from urllib.parse import urlencode
from redis import Redis

from common.utils.sportsbook import (
    generate_data_hash, format_odds, normalize_market_name, normalize_market_outcome, normalize_team_name, correct_over_under_line, normalize_status_name,
    create_market_key
)
from common.constants.sportsbook import EVENT_TTL, ODDS_TTL
from oddsdata.tasks import batch_upsert_events, batch_upsert_odds

class OddsClient(ABC):

    def __init__(self, name, league):
        self.name = name
        self.league = league
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.logger = logging.getLogger(f'oddsdata.apiclients.{self.name}')


    def fetch_data(self, url, headers=None, params=None, method='requests', context=None, page=None) -> dict:
        default_headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		}
        final_headers = { **default_headers, **(headers or {}) }

        self.logger.info(f'yielding request to {url} ({self.league})')
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
            self.logger.exception(f'an error occured while yielding request to {url}: {e} ({self.league})')
            return {}


    def match_espn_key(self, event_key, event_id):
        if self.redis.exists(f'espn:events:{event_key}'):
            self.redis.set(f'{self.name}:keys:{event_id}', event_key, ex=EVENT_TTL)
            self.redis.set(f'{self.name}:ids:{event_key}', event_id, ex=EVENT_TTL)
            self.logger.info(f'matched {event_key} to ESPN schedule ({self.league})')
        else:
            self.logger.warning(f'unable to match {event_key} to ESPN schedule ({self.league})')
        
    
    def compare_and_update_odds_cache(self, odds_data) -> bool:
        odds_hash = generate_data_hash(odds_data)
        redis_key = f'{self.name}:odds:{odds_data["event_key"]}:{odds_data["market_key"]}:{odds_data["outcome"]}'
        redis_hash_key = f'{self.name}:hashes:{odds_data["event_key"]}:{odds_data["market_key"]}:{odds_data["outcome"]}'
        prev_hash = self.redis.get(redis_hash_key)

        if prev_hash != odds_hash:
            # Odds data have changed, cache odds and update DB
            self.redis.set(redis_key, json.dumps(odds_data), ex=ODDS_TTL)
            self.redis.set(redis_hash_key, odds_hash, ex=ODDS_TTL)
            #self.logger.info(f'updated {format_odds(odds_data)} for {odds_data["event_key"]}')
            return True
        else:
            return False


    def upsert_data(self, data, is_odds=True):
        if not data:
            self.logger.info(f'no new {"odds" if is_odds else "events"} to upsert ({self.league})')
        elif is_odds:
            self.logger.info(f'upserting {len(data)} odds ({self.league})')
            batch_upsert_odds.delay(data)
        else:
            self.logger.info(f'upserting {len(data)} events ({self.league})')
            batch_upsert_events.delay(data)


    def parse_selection(self, event_key, market_name, outcome_name, line=None, value=0, team=None, player=None,  status='active'):
        standard_name, market_type, market_line, market_team, market_player = normalize_market_name(market_name, self.league)
        standard_outcome, outcome_player, outcome_line = normalize_market_outcome(outcome_name, market_type, self.league)

        if not line:
            line = correct_over_under_line(market_type, market_line) if market_line else correct_over_under_line(market_type, outcome_line)

        if not player:
            player = market_player if market_player else outcome_player

        if not team:
            team = market_team if market_team else None

        if team:
            team = normalize_team_name(team, self.league)
            if standard_outcome == team:
                team = None

        value = float(round(value, 3))
        status = normalize_status_name(status)

        market_key = create_market_key(standard_name, line, team, player)

        return {
			'event_key': event_key,
			'market_key': market_key,
			'sportsbook': self.name,
			'market': standard_name,
			'outcome': standard_outcome,
			'line': line,
			'value': value,
			'team': team,
			'player': player,
			'status': status
		}

    @abstractmethod
    def parse_schedule(self):
        pass


    @abstractmethod
    def parse_primary_odds(self, status):
        pass


    @abstractmethod
    def parse_props(self, status):
        pass


    def export_markets(self, event_keys=[]):
        pass