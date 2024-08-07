from datetime import datetime
import hashlib

class Event:
    def __init__(self, league: str, away_team: str, home_team: str, event_time: str, active: bool = False):
        self.league = league
        self.away_team = away_team
        self.home_team = home_team
        self.event_time = event_time
        self.active = active
        self.id = self.generate_id()
        self.books = []

    def generate_id(self):
        event_string = f'{self.away_team}_{self.home_team}_{self.league}_{self.event_time}_{self.active}'
        return hashlib.sha256(event_string.encode()).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'league': self.league,
            'away_team': self.away_team,
            'home_team': self.home_team,
            'event_time': self.event_time,
            'books': self.books
        }

class Pick:
    def __init__(
            self, market: str, team: str, line: int, odds: float,
            outcome: str = None, player: str = None):
        self.market = market
        self.team = team
        self.line = line
        self.odds = odds
        self.outcome = outcome
        self.player = player
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            'market': self.market,
            'team': self.team,
            'line': self.line,
            'odds': self.odds,
            'outcome': self.over_under,
            'player': self.player,
            'timestamp': self.timestamp
        }