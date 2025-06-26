import json

from .base import OddsClient

from common.utils.sportsbook import create_event_key, normalize_team_name, format_odds
from common.constants.urls import ESPNBET_URLS, ESPNBET_AUTH_TOKEN
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError
from common.utils.client import PlaywrightSessionManager


class ESPNBetClient(OddsClient):

    def __init__(self, league):
        super().__init__('espnbet', league)


    def parse_schedule(self):
        base_url = ESPNBET_URLS['base']
        league_url = ESPNBET_URLS[self.league]

        page = PlaywrightSessionManager.new_page(force_context=True)
        headers = {
            'origin': 'https://thescore.bet',
            'referer': 'https://thescore.bet',
            'cookie': page.context.cookies(),
            'x-anonymous-authorization': ESPNBET_AUTH_TOKEN,
        }
        variables = {
            'canonicalUrl': league_url,
            'oddsFormat': 'AMERICAN',
            'includeRichEvent': True,
            'includeRecommendedProps': True,
            'includeSectionDefaultField': True,
            'includeTableMarketCard': True,
            'pageType': 'PAGE',
        }
        params = {
            'operationName': 'Marketplace',
            'variables': json.dumps(variables),
        }

        data = self.fetch_data(
            base_url, headers=headers, params=params, method='page_evaluate_fetch', page=page
        ).get('data', {}).get('page', {}).get('defaultChild', {})
        events_section = next(
            (s for s in data.get('sectionChildren', {}) if s.get('__typename', '') == 'MarketplaceShelf'),
            None
        )

        if not events_section:
            self.logger.warning(f'unable to locate events section ({self.league})')
            return

        event_count = len(events_section.get('marketplaceShelfChildren', []))
        self.logger.info(f'fetched {event_count} events ({self.league})')

        if not event_count:
            return

        events = events_section.get('marketplaceShelfChildren', [])
        for event in events:
            try:
                event_data = event['fallbackEvent']
                event_id = event_data['id'].split(':')[1]

                teams = event_data['name'].split('@')
                away = normalize_team_name(teams[0], self.league)
                home = normalize_team_name(teams[1], self.league)

                start_time = utc_to_cst(event_data['startTime'])
                start_date = start_time.split('T')[0]

                event_key = create_event_key(self.league, start_date, away, home)
                self.match_espn_key(event_key, event_id)

            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as E:
                self.logger.exception(f'an error occured while scraping events ({self.league}): {e}')
    

    def parse_primary_odds(self, status):
        base_url = ESPNBET_URLS['base']
        league_url = ESPNBET_URLS[self.league]

        page = PlaywrightSessionManager.new_page(force_context=True)
        headers = {
            'origin': 'https://thescore.bet',
            'referer': 'https://thescore.bet',
            'cookie': page.context.cookies(),
            'x-anonymous-authorization': ESPNBET_AUTH_TOKEN,
        }
        variables = {
            'canonicalUrl': league_url,
            'oddsFormat': 'AMERICAN',
            'includeRichEvent': True,
            'includeRecommendedProps': True,
            'includeSectionDefaultField': True,
            'includeTableMarketCard': True,
            'pageType': 'PAGE',
        }
        params = {
            'operationName': 'Marketplace',
            'variables': json.dumps(variables),
        }

        data = self.fetch_data(
            base_url, headers=headers, params=params, method='page_evaluate_fetch', page=page
        ).get('data', {}).get('page', {}).get('defaultChild', {})
        events_section = next(
            (s for s in data.get('sectionChildren', {}) if s.get('__typename', '') == 'MarketplaceShelf'),
            None
        )

        if not events_section:
            self.logger.warning(f'unable to locate events section ({self.league})')
            return

        event_count = len(events_section.get('marketplaceShelfChildren', []))
        self.logger.info(f'fetched {event_count} events ({self.league})')

        if not event_count:
            return

        status_keys = self.redis.smembers(f'espn:events:{self.league}:{status}')

        odds = []
        events = (events_section.get('marketplaceShelfChildren', []) or [])
        for event in events:
            try:
                event_id = event['fallbackEvent']['id'].split(':')[1]
                event_key = self.redis.get(f'{self.name}:keys:{event_id}')

                if not event_key or event_key not in status_keys:
                    continue

                markets = event.get('markets', [])
                for market in markets:
                    market_name = market['name']

                    selections = market.get('selections', [])
                    for selection in (selections or []):
                        outcome_name = selection['name']['cleanName']

                        line = (selection.get('points') or {}).get('decimalPoints')
                        value = selection['odds']['numerator'] / selection['odds']['denominator']
                        status = selection['status']

                        odds_data = self.parse_selection(event_key, market_name, outcome_name, line=line, value=value, status=status)
                        self.logger.info(f'name={market_name} | outcome={outcome_name} | line={line} | team=None | player=None -> {format_odds(odds_data)}')
                        if self.compare_and_update_odds_cache(odds_data):
                            odds.append(odds_data)

            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as e:
                self.logger.exception(f'an error occured while scraping primary markets ({self.league}): {e}')
        
        self.upsert_odds(odds)
    

    def parse_props(self, status):
        base_url = ESPNBET_URLS['base']
        league_url = ESPNBET_URLS[self.league]

        status_keys = self.redis.smembers(f'espn:events:{status}')

        odds = []
        for event_key in status_keys:
            event_id = self.redis.get(f'{self.name}:ids:{event_key}')
            if not event_id:
                self.logger.warning(f'unknown event id for {event_key} ({self.league})')
                continue
            
            league_url += f'/event/{event_id}/sections/player_props'

            page = PlaywrightSessionManager.new_page(force_context=True)
            headers = {
                'origin': 'https://thescore.bet',
                'referer': 'https://thescore.bet',
                'cookie': page.context.cookies(),
                'x-anonymous-authorization': ESPNBET_AUTH_TOKEN,
            }
            variables = {
                'canonicalUrl': league_url,
                'oddsFormat': 'AMERICAN',
                'includeRichEvent': True,
                'includeRecommendedProps': False,
                'includeSectionDefaultField': True,
                'includeTableMarketCard': True,
                'pageType': 'PAGE',
            }
            params = {
                'operationName': 'Marketplace',
                'variables': json.dumps(variables),
            }

            data = self.fetch_data(
                base_url, headers=headers, params=params, method='page_evaluate_fetch', page=page
            ).get('data', {}).get('page', {}).get('defaultChild', {})

            market_count = len(data.get('sectionChildren', []))
            self.logger.info(f'fetched {market_count} markets ({self.league})')

            if not market_count:
                continue
            
            markets = data.get('sectionChildren', [])
            for market in markets:
                market_name = market['labelText']
                try:
                    market_children = market['drawerChildren'][0].get('marketplaceShelfChildren', [])
                    for market_child in market_children if market_children else []:
                        player_container = market_child.get('participant', {})
                        player = player_container.get('fullName') if player_container else None

                        sub_markets = market_child.get('markets', [])
                        for sub_market in sub_markets:
                            selections = sub_market.get('selections', [])
                            for selection in selections:
                                outcome_name = selection['name']['cleanName']

                                line = (selection.get('points') or {}).get('decimalPoints')
                                team = (selection.get('participant') or {}).get('fullName')
                                value = selection['odds']['numerator'] / selection['odds']['denominator']
                                status = selection['status']

                                odds_data = self.parse_selection(
                                    event_key, 
                                    market_name, 
                                    outcome_name, 
                                    line=line, 
                                    value=value, 
                                    team=team, 
                                    player=player, 
                                    status=status
                                )
                                self.logger.info(f'name={market_name} | outcome={outcome_name} | line={line} | team={team} | player={player} -> {format_odds(odds_data)}')
                                if self.compare_and_update_odds_cache(odds_data):
                                    odds.append(odds_data)

                except NormalizationError as e:
                    self.logger.debug(e)
                except Exception as e:
                    self.logger.exception(f'an error occured while scraping prop markets ({self.league}): {e}')
            
        self.upsert_odds(odds)
                        
 
    def export_markets(self, event_keys=[]):
        base_url = ESPNBET_URLS['base']
        league_url = ESPNBET_URLS[self.league]

        markets = { 'sportsbook': self.name, 'events': [] }
        for event_key in event_keys:
            event_markets = { 'event_key': event_key, 'markets': []}
            event_id = self.redis.get(f'{self.name}:ids:{event_key}')
            if not event_id:
                continue
            
            league_url += f'/event/{event_id}/section/sgp'

            page = PlaywrightSessionManager.new_page(force_context=True)
            headers = {
                'origin': 'https://thescore.bet',
                'referer': 'https://thescore.bet',
                'cookie': page.context.cookies(),
                'x-anonymous-authorization': ESPNBET_AUTH_TOKEN,
            }
            variables = {
                'canonicalUrl': league_url,
                'oddsFormat': 'AMERICAN',
                'includeRichEvent': True,
                'includeRecommendedProps': False,
                'includeSectionDefaultField': True,
                'includeTableMarketCard': True,
                'pageType': 'PAGE',
            }
            params = {
                'operationName': 'Marketplace',
                'variables': json.dumps(variables),
            }

            data = self.fetch_data(
                base_url, headers=headers, params=params, method='page_evaluate_fetch', page=page
            ).get('data', {}).get('page', {}).get('defaultChild', {})

            for market in data.get('sectionChildren', []):
                market_name = market['labelText']

                sub_market = market['drawerChildren'][0]['marketplaceShelfChildren'][0]
                if not sub_market:
                    continue

                participant = sub_market.get('participant')
                player = participant.get('fullName') if participant else None

                market_selection = sub_market.get('markets', [{}])[0]
                if not market_selection or not isinstance(market_selection, dict):
                    continue

                selection = market_selection['selections'][0]
                if not selection:
                    continue

                outcome = selection['name']['cleanName']
                points = selection.get('points')
                line = points.get('decimalPoints') if points else None

                participant = selection.get('participant')
                team = participant.get('mediumName') if participant else None

                event_markets['markets'].append({
                    'name': market_name,
					'outcome': outcome,
					'line': line,
					'team': team,
					'player': player,
                    'expected_outcome': {},
                    'expected_exception': False,
                })
            
            markets['events'].append(event_markets)
    
        return markets