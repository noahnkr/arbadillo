from .constants import LEAGUE_ALIASES, MARKET_ALIASES, CLIENT_MAP
from .exceptions import NormalizationError
from .logging import configure_logging
from datetime import datetime
import importlib
import hashlib
import json
import re

logger = configure_logging(__name__)

# ---------- String Helpers -----------

def clean_str(name: str) -> str:
    """Trim and normalize team names."""
    name = re.sub(r"[-_./\\]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip().lower()


def normalize_team_name(name: str, league: str) -> str:
    """Normalizes a team name to a slugified standard."""
    team_aliases = LEAGUE_ALIASES[league]
    for standard, aliases in team_aliases.items():
        if clean_str(name) in map(str.lower, aliases):
            return standard
    raise NormalizationError(f'Unkown team name `{name}` for league `{league}`')


def normalize_market_name(market: str) -> str:
    """Normalizes a sportsbook's market name to a standard."""
    for standard, aliases in MARKET_ALIASES.items():
        if clean_str(market) in map(str.lower, aliases):
            return standard
    raise NormalizationError(f'Unkown market name `{market}`')


def extract_float(raw: str) -> float | None:
    """Exctracts the float value from collected sportsbook data."""
    try:
        match = re.search(r"[-+]?\d*\.\d+|\d+", raw)
        return float(match.group()) if match else None
    except Exception:
        return None

# ---------- Event & Odds Helpers -----------

def create_event_key(league:str, date: str, away:str, home:str,) -> str:
    """Generate event key (primary ID) for database and Redis."""
    return f'{league}:{date}:{away}@{home}'


def generate_events_hash(event_data: dict) -> str:
    """Create a hash representing the event's meaningful state."""
    fields = ['event_key', 'league', 'start_time', 'away_team', 'home_team', 'status']
    relevant = {k: event_data[k] for k in fields if k in event_data}
    raw = json.dumps(relevant, sort_keys=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def generate_odds_hash(odds_data: dict) -> str:
    """Create a hash to uniquely identify a specific odds line."""
    fields = ['event_key', 'market', 'outcome', 'line', 'value', 'player', 'prop']
    relevant = {k: odds_data[k] for k in fields if k in odds_data}
    raw = json.dumps(relevant, sort_keys=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def american_to_decimal(american_odds: int) -> float:
    """
    Convert American odds to Decimal odds.
    +150 -> 2.50
    -120 -> 1.83
    """
    if american_odds > 0:
        return round((american_odds / 100) + 1, 2)
    else:
        return round((100 / american_odds) + 1, 2)


def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert Decimal odds to American odds rounded to nearest 5.
    2.50 -> +150
    1.83 -> -120
    """
    if decimal_odds >= 2.0:
        american_odds = (decimal_odds - 1) * 100
    else:
        american_odds = -100 / (decimal_odds - 1)

    return int(round(american_odds / 5.0) * 5)

# ---------- Time Helpers -----------

def current_timestamp() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now().isoformat()


def iso_to_unix(iso_str: str) -> int:
    """Convert ISO time string to UNIX timestamp."""
    return int(datetime.fromisoformat(iso_str).timestamp())


def unix_to_iso(ts: int) -> str:
    """Convert UNIX timestamp to ISO format."""
    return datetime.fromtimestamp(ts).isoformat()


def time_diff_minutes(t1: str, t2: str) -> float:
    """Return time diff in minutes between two ISO timestamps."""
    dt1 = datetime.fromisoformat(t1)
    dt2 = datetime.fromisoformat(t2)
    return abs((dt1 - dt2).total_seconds()) / 60.0

# ---------- Import Helpers ----------

def get_class_from_path(path: str):
    module_path, class_name = path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def get_client(sportsbook: str, league: str):
    class_path = CLIENT_MAP.get(sportsbook.lower())
    if not class_path:
        raise ValueError(f'No client found for sportsbook: {sportsbook}')
    ClientClass = get_class_from_path(class_path)
    return ClientClass(league)