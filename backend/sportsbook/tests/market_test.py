import json
import unittest
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from sportsbook.apiclients.espnbet import ESPNBetClient
from sportsbook.apiclients.draftkings import DraftKingsClient
from sportsbook.apiclients.fanduel import FanDuelClient
from common.constants.aliases import BASEBALL_MARKET_REGEX

CLIENTS = {
    'espnbet': ESPNBetClient('mlb'),
    'draftkings': DraftKingsClient('mlb'),
    'fanduel': FanDuelClient('mlb')
}

class MarketTest(unittest.TestCase):

    def setUp(self):
        with open('backend/data/mlb_markets_test.json', 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
    

    def test_parse_selection(self):
        failures = []

        for client_data in self.test_data:
            sportsbook = client_data['sportsbook']
            client = CLIENTS[sportsbook]

            if not client:
                continue

            for event in client_data['events']:
                event_key = event['event_key']

                for market in event['markets']:
                    market_name = market['market_name']
                    outcome_name = market['outcome_name']
                    line = market['line']
                    team = market.get('team')
                    player = market.get('player')
                    expected = market['expected_outcome']
                    expect_exception = market['expected_exception']

                    try:
                        result = client._parse_selection(event_key, market_name, outcome_name, line, team, player, 2.0, 'active')

                        if expect_exception:
                            failures.append(f'[FAIL] Expected exception for {sportsbook} - {market_name}:\n  {str(e)}')
                        else:
                            actual = {
                                'market': result['market'],
                                'outcome': result['outcome'],
                                'line': result['line'],
                                'team': result['team'],
                                'player': result['player']
                            }
                            if expected != actual:
                                failures.append(f'[FAIL] Mismatch in {sportsbook} - {market_name} ({outcome_name}):\n  Expected: {expected}\n  Got: {actual}')

                    except Exception as e:
                        if not expect_exception:
                            failures.append(f'[FAIL] Unexpected exception for {sportsbook} - {market_name} ({outcome_name}):\n  {str(e)}')
        
        if failures:
            self.fail('\n\n' + '\n'.join(failures))


if __name__ == '__main__':
    unittest.main()