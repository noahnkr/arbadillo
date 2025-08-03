import hashlib

from dataclasses import dataclass, field, fields, asdict
from datetime import datetime 

from django.utils.timezone import now

@dataclass(frozen=True)
class TeamData:
    espn_id: int
    league: str
    team_key: str
    name: str
    
    def __repr__(self) -> str:
        return f'{self.name} ({self.league})'

    def __hash__(self) -> int:
        parts = [str(getattr(self, f.name)) for f in fields(self)]
        raw = '|'.join(parts)
        return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], 'big')
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PlayerData:
    espn_id: int
    league: str
    player_key: str
    team_key: str
    name: str
    position: str
    
    def __repr__(self) -> str:
        return f'{self.name} ({self.team_key})'

    def __hash__(self) -> int:
        parts = [str(getattr(self, f.name)) for f in fields(self)]
        raw = '|'.join(parts)
        return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], 'big')
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EventData:
    espn_id: int
    league: str
    season: int
    season_type: str
    event_key: str
    away_team: str
    home_team: str
    start_time: datetime
    status: str
    collected_at: datetime = field(default_factory=now)
    
    def __repr__(self) -> str:
        return f'[{self.league} - {self.season} - {self.season_type}] {self.start_time.strftime("%Y-%m-%d")} - {self.away_team} @ {self.home_team}'

    def __hash__(self) -> int:
        parts = [
            str(getattr(self, f.name))
            for f in fields(self)
            if f.name != 'collected_at'
        ]
        raw = '|'.join(parts)
        return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], 'big')
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['start_time'] = d['start_time'].isoformat()
        d['collected_at'] = d['collected_at'].isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict): 
        return cls(
            start_time=datetime.fromisoformat(d['start_time']),
            collected_at=datetime.fromisoformat(d['collected_at']),
            **{k: v for k,v in d.items() if k not in {'start_time','collected_at'}}
        )


@dataclass(frozen=True)
class EventResultData:
    league: str
    event_key: str
    away_score: int
    home_score: int
    total: int
    margin: int
    winner: str

    def __repr__(self) -> str:
        return f'[{self.event_key}] {self.away_score} - {self.home_score}'
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class PlayerStatData:
    league: str
    event_key: str
    player_key: str
    stat_name: str
    value: float

    def __hash__(self):
        return hash((self.league, self.event_key, self.player_key, self.stat_name))
    
    def __eq__(self, other):
        return (
            isinstance(other, PlayerStatData) and
            self.league == other.league and
            self.event_key == other.event_key and
            self.player_key == other.player_key and
            self.stat_name == other.stat_name
        )

    def  __repr__(self) -> str:
        return f'{self.player_key} ({self.team_key}) | {self.stat_name} - {self.value}'

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class TeamStatData:
    league: str
    event_key: str
    team_key: str
    stat_name: str
    value: float

    def __hash__(self):
        return hash((self.league, self.event_key, self.team_key, self.stat_name))
    
    def __eq__(self, other):
        return (
            isinstance(other, TeamStatData) and
            self.league == other.league and
            self.event_key == other.event_key and
            self.team_key == other.team_key and
            self.stat_name == other.stat_name
        )
    def  __repr__(self) -> str:
        return f'{self.team_key} ({self.league}) | {self.stat_name} - {self.value}'

    def to_dict(self) -> dict:
        return asdict(self)