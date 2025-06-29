import hashlib

from dataclasses import dataclass, field, fields, asdict
from datetime import datetime

from django.utils.timezone import now

from common.utils.sportsbook_helpers import get_market_type

@dataclass(frozen=True)
class SelectionData:
    sportsbook: str
    league: str
    event_key: str
    market_key: str
    market: str
    outcome: str
    value: float
    status: str
    line: float = field(default=None)
    team: str = field(default=None)
    player: str = field(default=None)
    collected_at: datetime = field(default_factory=now)

    def __repr__(self) -> str:
        market_type = get_market_type(self.market, self.league)
        if market_type == 'moneyline': 
            return f'{self.outcome} {self.market} ({self.value})'
        elif market_type in {'spread', 'total'}:
            return f'{self.team if self.team else ""} {self.outcome} {self.line} {self.market} ({self.value})'.strip()
        elif market_type == 'over_under':
            team_or_player = (self.team or self.player) if self.team or self.player else ''
            return f'{team_or_player} {self.outcome} {self.line} {self.market} ({self.value})'.strip()
        else:
            team_or_player = (self.team or self.player) if self.team or self.player else ''
            return f'{team_or_player} {self.outcome} {self.line} {self.market} ({self.value})'.strip()
        
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
        d['collected_at'] = d['collected_at'].isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict): 
        return cls(
            collected_at=datetime.fromisoformat(d['collected_at']),
            **{k: v for k,v in d.items() if k != 'collected_at'}
        )

