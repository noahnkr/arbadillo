import hashlib

class Event:
    def __init__(self, league: str, away_team: str, home_team: str, start_time: str, is_live: bool = False):
        self.league = league
        self.away_team = away_team
        self.home_team = home_team
        self.start_time = start_time
        self.is_live = is_live
        self.id = self.generate_id()
        self.books = []

    def __str__(self):
        book_strs = '\n'.join(str(book) for book in self.books)
        return f'{self.league.upper()}_{self.away_team}@{self.home_team}_{self.start_time}{"_LIVE" if self.is_live else ""}\n{book_strs}'

    def generate_id(self):
        event_string = f'{self.away_team}_{self.home_team}_{self.league}_{self.start_time}{"_LIVE" if self.is_live else ""}'
        return hashlib.sha256(event_string.encode()).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'league': self.league,
            'away_team': self.away_team,
            'home_team': self.home_team,
            'start_time': self.start_time,
            'self': self.active,
            'books': self.books
        }

class Pick:
    def __init__(self, market: str, team: str, line: int, odds: float, outcome: str = None, player: str = None):
        self.market = market
        self.team = team
        self.line = line
        self.odds = odds
        self.outcome = outcome
        self.player = player

    def __str__(self):
        return f'{self.market}_{self.team}_{self.line}_{self.odds}_{self.outcome}_{self.player}'

    def to_dict(self):
        return {
            'market': self.market,
            'team': self.team,
            'line': self.line,
            'odds': self.odds,
            'outcome': self.outcome,
            'player': self.player,
        }
