import hashlib

class ScrapedEvent:
    def __init__(self, league: str, away_team: str, home_team: str, start_time: str, active: bool = False):
        self.league = league
        self.away_team = away_team
        self.home_team = home_team
        self.start_time = start_time
        self.active = active
        self.id = self.generate_id()
        self.books = []

    def __str__(self):
        return f'{self.league}_{self.away_team}@{self.home_team}_{self.start_time}'
    
    def __eq__(self, other):
        if isinstance(other, ScrapedEvent):
            return (
                self.away_team == other.away_team
                and self.home_team == other.home_team
                and self.start_time == other.start_time
                and self.active == other.active
            )
        return False

    def generate_id(self):
        event_string = self.__str__()
        return hashlib.sha256(event_string.encode()).hexdigest()

class ScrapedPick:
    def __init__(self, market: str, team: str, line: int, odds: float, outcome: str = None, player: str = None):
        self.market = market
        self.team = team
        self.line = line
        self.odds = odds
        self.outcome = outcome
        self.player = player

    def __str__(self):
        return f'{self.market}_{self.team}_{self.line}_{self.odds}_{self.outcome}_{self.player}'

    def __eq__(self, other):
        if isinstance(other, ScrapedPick):
            return (
                self.market == other.market
                and self.team == other.team
                and self.line == other.line
                and self.odds == other.odds
                and self.outcome == other.outcome
                and self.player == other.player
            )
        return False