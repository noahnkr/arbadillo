import json
import unittest
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from sportsbook.apiclients.espnbet import ESPNBetClient
from sportsbook.apiclients.draftkings import DraftKingsClient
from sportsbook.apiclients.fanduel import FanDuelClient
from sportsbook.apiclients.betrivers import BetRiversClient

CLIENTS = {
    'espnbet': ESPNBetClient('baseball', 'mlb'),
    'draftkings': DraftKingsClient('baseball', 'mlb'),
    'fanduel': FanDuelClient('baseball', 'mlb'),
    'betrivers': BetRiversClient('baseball', 'mlb')
}

def export_markets_to_file(event_key, output):
    export = { 'event_key': event_key }

    for sportsbook, client in CLIENTS.items():
        export_markets = client.export_markets(event_key)

        if export.get(sportsbook):
            export[sportsbook].extend(export_markets)
        else:
            export[sportsbook] = export_markets

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2)


class MarketTest(unittest.TestCase):

    def setUp(self):
        with open('data/market_test_data.json', 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
    
    def test_parse_selection(self):
        failures = []

        event_key = self.test_data['event_key']
        for sportsbook, client in CLIENTS.items():
            for market in self.test_data[sportsbook]:
                market_name = market['market_name']
                outcome_name = market['outcome_name']
                line = market['line']
                team = market.get('team')
                player = market.get('player')
                expected = market['expected']
                expect_exception = market['expected_exception']

                try:
                    actual_selection = client.parse_selection(
                        event_key, 
                        market_name, 
                        outcome_name, 
                        line=line,
                        team=team,
                        player=player
                    )

                    if expect_exception:
                        failures.append(f'[FAIL] ({sportsbook}) Expected exception for {actual_selection}:\n')
                    else:
                        actual = actual_selection.to_dict()
                        for key in ['sportsbook', 'league', 'event_key', 'market_key', 'status', 'value', 'collected_at']:
                            actual.pop(key, None)

                        if expected != actual:
                            failures.append(f'[FAIL] ({sportsbook}) Mismatch for {market_name} | {outcome_name} | line={line}, team={team}, player={player}:\n  Expected: {expected}\n  Got: {actual}\n')

                except Exception as e:
                    if not expect_exception:
                        failures.append(f'[FAIL] ({sportsbook}) Unexpected exception for {market_name} | {outcome_name} | line={line}, team={team}, player={player}\n')
            
            if failures:
                self.fail('\n\n' + '\n'.join(failures))


if __name__ == '__main__':
    event_key = '2025-07-02:new-york-yankees@toronto-blue-jays'
    #export_markets_to_file(event_key, f'data/{event_key.replace(":", "_")}_markets.json')
    unittest.main()