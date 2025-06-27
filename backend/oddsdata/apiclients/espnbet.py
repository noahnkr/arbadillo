import json

from .base import SportsbookClient

from common.utils.sportsbook import create_event_key, normalize_team_name, format_odds
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError
from common.utils.client import PlaywrightSessionManager

class ESPNBetClient(SportsbookClient):
    BASE_URL = 'https://sportsbook-tsb.ca-default.thescore.bet/graphql/persisted_queries/4e63acef22373225db328b8fc6534a998cd73a90745758017559fa4b43e1fe66'
    AUTH_TOKEN = 'Bearer eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYifQ.I90O69ULGH1ehEsPEpXv88G-0YYSnvlTKb2NL-38EvZU66NSOWsxWZXkOg4QpbAuyooucKAhMYmSwQmIJ2iEJ0U-NZP7upAyI1-riFZM26h5i5i58cXGDFqTYqU3sg6imTgsh0CFo_LsSwMAzcUAubpeCXH_TaPtHneme2jjPoYvo-fwt_OanVcMVqQnVwbd7rQktGDM-NBYQO2DQdegCA_n9lyQKeJHgoYgXnN426od2-MCVpc--E7fwz1-0fQo4eeaI0BEi3Oxaykxc3aPD4dtJA4CpGL9VKxe-DCa_A-e3TYGrzKRbtUgjlyHNAXtjP8XF6PBR3Dk2FG_VKyBZuZwQdSwtNT5cbi6OjSa-n32ArCXueqMygz_51Fc-kP34sU2mxC_XoN9bvSOXIu3iyLXZfVdGZOpRNwAMxH0yhmRx0KB89Vr9nSwbTAyqX693bnkIeNoaASK_iuptNXcVsg6HyE93xceTrT7ALmQrZW5Z0V2brTWNnhdgypRYy9fMxYb6Y0T3nbeuNvMSHtQUj5H9ZERJuhDk4oe7Eu6s-U2bfjSO9R2yxUs6i-VS58cqUPnK0HxSzSFiwVUYRu7x6ZLEW7ZXL5vgYe4A13uTc-CTyoJiIHi_xuHcPfUX2pHfXsVa-kcXBls_Bljr4NBNdhEzC3OS28K2H7sD4gv3T8.DAZz4Z6i1ZeSoknKSeNayA.3dlCcWPnwYjTpjirq3ml7b_3Ry_9Y9lev7sDh6yS-Ty_clXkn9ULinDnxVUQQYzIW69HFf7CKO6UmHO1tGgVPNjhCN9_nQbbRrv4GbcnhfHQ7-r6VdsscX7ikwKyGTfYPzHDWzUg6z8uZBd_llb747myH55kt_fpzUNEwd3y530-6NZ1MhZHymIG8htWzf-JvbcmU_ff7V15p6iMHByeSR11aJQ0nAhURlw0fTuvg9N4SSmMWh3I-Wg5YvvrmFq0kmsO71vxuSJABKnp7yG7FQ.LAZPf8A0B73LnIZIn40Fmw'

    def __init__(self, sport: str, league: str):
        super().__init__('espnbet', sport, league)

    def _get(self, path):
        page = PlaywrightSessionManager.new_page(force_context=True)
        headers = {
            'origin': 'https://thescore.bet',
            'referer': 'https://thescore.bet',
            'cookie': page.context.cookies(),
            'x-anonymous-authorization': self.AUTH_TOKEN,
        }
        variables = {
            'canonicalUrl': path,
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
        return super()._get(
            self.BASE_URL, 
            headers=headers, 
            params=params, 
            method='page_evaluate_fetch',
            page=page
        ).get('data', {}).get('page', {}).get('defaultChild', {})

    def get_events(self):
        league_url = f'/sport/{self.sport}/organization/united-states/competition/{self.league}',
        data = self._get(league_url)
        events_section = next(
            (s for s in data.get('sectionChildren', {}) if s.get('__typename', '') == 'MarketplaceShelf'),
            None
        )
        if not events_section:
            self.logger.warning(f'Unable to locate events section ({self.league})')
            return []
        
        events = events_section.get('marketplaceShelfChildren', [])
        self.logger.info(f'Fetched {len(events)} events ({self.league})')

        return events

    def parse_events(self):
        events = self.get_events()
        for event in events:
            try:
                event_data = event['fallbackEvent']
                event_id = event_data['id'].split(':')[1]

                away_team = event_data['awayParticipant']['fullName']
                home_team = event_data['homeParticipant']['fullName']
                away_team_key = self.redis.get(f'teams:aliases:{self.league}:{away_team}')
                home_team_key = self.redis.get(f'teams:aliases:{self.league}:{home_team}')

                if not away_team_key or not home_team_key:
                    self.logger.warning(f'Missing team(s) aliases for {away_team} and/or {home_team} ({self.league})')
                    continue

                start_time = utc_to_cst(event_data['startTime'])
                start_date = start_time.split('T')[0]

                event_key = create_event_key(self.league, start_date, away_team_key, home_team_key)
                self.match_espn_key(event_key, event_id)

            except Exception as e:
                self.logger.exception(f'An error occured while parsing events ({self.league}): {e}') 

    def get_markets(self, event_key):
        event_id = self.redis.get(f'{self.name}:ids:{event_key}')
        if not event_id:
            self.logger.warning(f'Unknown event id for {event_key} ({self.league})')
            return []

        event_url = f'/sport/{self.sport}/organization/united-states/competition/{self.league}/event/{event_id}/sections/player_props',
        data = self._get(event_url)

        markets = data.get('sectionChildren', [])
        self.logger.info(f'fetched {len(markets)} markets for {event_key} ({self.league})')
        return markets

    def parse_markets(self, event_key):
        odds = []
        
        markets = self.get_markets(event_key)
        for market in markets:
            market_name = market['labelText']
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

                        try:
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
                            if self.compare_and_update_odds_cache(odds_data):
                                odds.append(odds_data)

                        except Exception as e:
                            self.logger.exception(f'An error occured while parsing markets for {event_key} ({self.league}): {e}')

        return odds