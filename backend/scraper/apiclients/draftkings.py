import json
import requests
from .base import SportsbookClient
from common.constants import SPORTSBOOK_URLS
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, 
	current_timestamp, generate_odds_hash,
)
from common.logging import configure_logging
from scraper.items import OddsItem

logger = configure_logging(__name__)

class DraftKingsClient(SportsbookClient):
	name = 'draftkings'

	def __init__(self, league=None):
		super().__init__(league)


	def fetch_data(self, url):
		headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		}
		response = requests.get(url, headers=headers)
		response.raise_for_status()
		data =  response.json()
		return data

	
	def parse_schedule(self):
		url = SPORTSBOOK_URLS[self.name][self.league]
		if url:
			logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
			try:
				data = self.fetch_data(url)
			except Exception as e:
				logger.critical(f'({self.name}) {e} occured while yielding schedule request | league={self.league}, url={url}')

			for event in data['events']:
				try:
					event_id = event['id']

					name = event['name']
					participants = name.split('@')
					away = normalize_team_name(participants[0], self.league)
					home = normalize_team_name(participants[1], self.league)

					start_time = event['startEventDate']
					start_date = start_time.split('T')[0]

					event_key = create_event_key(self.league, start_date, away, home)

					if self.redis.hexists('schedule:events', event_key) and self.redis.sismember('schedule:events:active', event_key):
						# Match event to ESPN schedule
						self.redis.sadd(f'{self.name}:events', event_key)
						self.redis.set(f'{self.name}:events:{event_id}', event_key, ex=60 * 60 * 24)
						logger.info(f'({self.name}) successfully matched event key to schedule | event_key={event_key}')
					else:
						logger.warning(f'({self.name}) unable to match event key to schedule | event_key={event_key}')
				except Exception as e:
					logger.critical(f'({self.name}) {e.with_traceback()} occured while scraping event in schedule | league={self.league}')
					continue

			
		
	def parse_odds(self):
		url = SPORTSBOOK_URLS[self.name][self.league]
		if url:
			logger.info(f'({self.name}) starting odds request | league={self.league}, url={url}')
			try:
				data = self.fetch_data(url)
			except Exception as e:
				logger.critical(f'({self.name}) {e} occured while yielding odds request | league={self.league}, url={url}')
			
			for market in data['markets']:
				try:
					market_id = market['id']
					event_id = market['eventId']
					market = normalize_market_name(market['name'])

					self.redis.set(
						f'{self.name}:markets:{market_id}', 
						json.dumps({
							'event_id': event_id,
							'market':  market,
					}))
				except Exception as e:
					logger.critical(f'({self.name}) {e.with_traceback()} occured while scraping markets | league={self.league}')

			for selection in data['selections']:
				try:
					market_id = selection['marketId']
					selection_data = json.loads(
						self.redis.get(f'{self.name}:markets:{market_id}')
					)

					event_id = selection_data['event_id']
					event_key = self.redis.get(f'{self.name}:events:{event_id}')
					if not event_key or not self.redis.sismember(f'{self.name}:events', event_key):
						continue

					market = selection_data['market']
					if market == 'moneyline':
						outcome = normalize_team_name(selection['label'])
						line = None
					elif market == 'spread':
						outcome = normalize_market_name(selection['label'])
						line = selection['points']
					else:
						outcome = selection['label'].lower()
						line = selection['points']
					
					value = selection['trueOdds']

					odds = OddsItem(
						event_key=event_key,
						sportsbook=self.name,
						market=market,
						outcome=outcome,
						line=line,
						value=value,
						player=None,
						prop=None,
						collected_at=current_timestamp()
					)
					odds_hash = generate_odds_hash(dict(odds))
					prev_odds = self.redis.hget(f'{self.name}:odds:{event_key}', odds_hash)

					if prev_odds is None:
						# Odds haven't been cached yet, insert row into DB
						pass
					elif odds_hash != generate_odds_hash(json.loads(prev_odds)):
						# Odds have changed, update row in DB
						pass

					# Update odds in hash
					self.redis.hset(f'{self.name}:odds:{event_key}', odds_hash, json.dumps(dict(odds)))

					logger.info(f'({self.name}) successfully scraped {market} odds | event_key={event_key}')
				except Exception as e:
					logger.critical(f'({self.name}) {e.with_traceback()} occured while scraping odds | league={self.league}')

