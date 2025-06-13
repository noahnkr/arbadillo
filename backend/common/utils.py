from common.constants import LEAGUE_ALIASES, MARKET_ALIASES, CLIENT_MAP, SPORTS_LEAGUES, STATUS_ALIASES
from common.exceptions import NormalizationError
from datetime import datetime
from dateutil import tz
import importlib
import hashlib
import json
import re

# ---------- String Helpers -----------

def clean_str(raw: str) -> str:
    """Trim and normalize input string extracted from web and JSON"""
    raw = re.sub(r"[-_e/\\]", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip().lower()


def extract_float(raw: str) -> float | None:
    """Exctracts the float value from collected sportsbook data."""
    try:
        match = re.search(r'[-+]?\d*\.\d+|\d+', raw)
        return float(match.group()) if match else None
    except Exception:
        return None

# ---------- Sportsbook Helpers -----------

def create_event_key(league: str, date: str, away:str, home:str,) -> str:
    """Generate event key (primary ID) for database and Redis."""
    return f'{league}:{date}:{away}@{home}'


def create_market_key(market: str, line: float = None, player: str = None, prop: str = None) -> str:
    """Creates an index on a specific market selection across sportsbooks."""
    components = [market]
    if line: components.append(str(line))
    if player: components.append(player)
    if prop: components.append(prop)
    return ':'.join(components)


def generate_data_hash(data: dict) -> str:
    """Create a hash of the input data"""
    raw = json.dumps(data, sort_keys=True)
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

    return int(american_odds)


def normalize_team_name(name: str, league: str) -> str:
    """Normalizes a team name to a slugified standard."""
    team_aliases = LEAGUE_ALIASES[league]
    for standard, aliases in team_aliases.items():
        if clean_str(name) in map(clean_str, aliases):
            return standard
    raise NormalizationError(f'Unkown team name `{name}` for league `{league}`')


def normalize_market_name(market: str) -> str:
    """Normalizes a sportsbook's market name to a standard."""
    for standard, aliases in MARKET_ALIASES.items():
        if clean_str(market) in map(clean_str, aliases):
            return standard
    raise NormalizationError(f'Unkown market name `{market}`')


def normalize_status_name(status: str) -> str:
    """Normalizes a sportbook's event status to a standard format."""
    for standard, statuses in STATUS_ALIASES.items():
        if clean_str(status) in map(clean_str, statuses):
            return standard
    raise NormalizationError(f'Unkown status name `{status}`')


def get_sport_from_league(league: str) -> str:
    """Gets the league's respective sport."""
    for sport, leagues in SPORTS_LEAGUES.items():
        if clean_str(league) in map(clean_str, leagues):
            return sport
    raise NormalizationError(f'Unknown league `{league}`')


def format_odds(odds_data: dict) -> str:
    """Formats odds data into a readable string."""
    market = odds_data['market']
    outcome = odds_data['outcome']
    line = odds_data['line']
    value = decimal_to_american(odds_data['value'])
    player = odds_data['player']
    prop = odds_data['prop']
    if market == 'moneyline':
        odds_str = f'{outcome} ({value})'
    elif  market == 'spread' or market == 'total':
        odds_str = f'{outcome} {line} ({value})'
    else:
        odds_str = f'({player} {outcome} {line} {prop} ({value})'
    return odds_str

# ---------- Time Helpers -----------

def current_timestamp() -> str:
    """Return current UTC timestamp as ISO string."""
    central = tz.gettz('America/Chicago')
    return datetime.now(tz=central).isoformat()


def utc_to_cst(time: str) -> str:
    """Converts a time string in UTC to CST."""
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Chicago')

    # Handle different datetime formats
    try:
        utc = datetime.strptime(time, '%Y-%m-%dT%H:%MZ')
    except Exception:
        # Remove ms if present
        if '.' in time:
            time = time.split('.')[0] + 'Z'
        utc = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return datetime.strftime(central, '%Y-%m-%dT%H:%MZ')


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