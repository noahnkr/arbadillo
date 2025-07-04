import json
import unittest
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from sportsbook.clients.espnbet import ESPNBetClient
from sportsbook.clients.draftkings import DraftKingsClient
from sportsbook.clients.fanduel import FanDuelClient
from sportsbook.clients.betrivers import BetRiversClient
from sportsbook.clients.betmgm import BetMGMClient

SPORT = 'baseball'

LEAGUE = 'mlb'

CLIENTS = {
    'espnbet': ESPNBetClient(SPORT, LEAGUE),
    'draftkings': DraftKingsClient(SPORT, LEAGUE),
    'fanduel': FanDuelClient(SPORT, LEAGUE),
    'betrivers': BetRiversClient(SPORT, LEAGUE),
    'betmgm': BetMGMClient(SPORT, LEAGUE),
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
                        failures.append(f'[FAIL] ({sportsbook}) Expected exception for {market_name} | {outcome_name} | line={line}, team={team}, player={player}\n Got: {actual_selection}:\n')
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
    event_key = '2025-07-04:detroit-tigers@cleveland-guardians'
    #export_markets_to_file(event_key, f'data/market_test_data.json')
    unittest.main()