from dataclasses import dataclass, field, asdict
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
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EventData:
    espn_id: int
    league: str
    event_key: str
    away_team_key: int
    home_team_key: int
    start_time: datetime
    status: str
    collected_at: datetime = field(default_factory=now, hash=False, compare=False)
    
    def __repr__(self) -> str:
        return f'{self.start_time.strftime("%Y-%m-%d")} - {self.away_team_key} @ {self.home_team_key} ({self.league})'
    
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

