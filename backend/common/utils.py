from common.constants.sportsbook import SPORTS_LEAGUES, CLIENT_MAP
from common.constants.aliases import (
    REVERSE_TEAM_LOOKUP, REVERSE_MARKET_LOOKUP, EVENT_STATUS_ALIASES, ODDS_STATUS_ALIASES, 
    MARKET_EXACT_RESULT_PATTERN, MARKET_OVER_UNDER_PATTERN, MARKET_SCOPE_INCLUDED_PATTERN,
)
from common.exceptions import NormalizationError
from datetime import datetime
from dateutil import tz
import importlib
import hashlib
import json
import re

# ---------- String Helpers -----------

def extract_float(raw: str) -> float | None:
    """Extracts the first numeric value from a string and returns it as a float."""
    match = re.search(r'\d+(?:\.\d+)?', raw)
    return float(match.group()) if match else None


def extract_text(raw: str) -> str | None:
    """Extracts the first alpha values from a string."""
    match = re.search(r'[a-z\s]*', raw)
    return float(match.group().strip()) if match else None

def clean_str(raw: str) -> str:
    """Trim and normalize input string extracted from web and JSON"""
    raw = re.sub(r"[-_e/\\]", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip().lower()

# ---------- Sportsbook Helpers -----------

def create_event_key(league: str, date: str, away:str, home:str) -> str:
    """Generate event key (primary ID) for database and Redis."""
    return f'{league}:{date}:{away}@{home}'


def create_market_key(
        market: str, line: float = None, team: str = None, player: str = None
    ) -> str:
    """Creates an index on a specific market selection across sportsbooks."""
    components = [market]
    if player: components.append(player)
    if team: components.append(team)
    if line: components.append(str(line))
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
    try:
        return REVERSE_TEAM_LOOKUP[(league, clean_str(name))]
    except KeyError:
        raise NormalizationError(f'Unknown team name `{name}` for league `{league}`')


def normalize_market_name(market: str, league: str) -> tuple[str, str, str, float | None, str | None]:
    """
    Normalize a raw sportsbook market name into a standardized canonical format.

    This function attempts to identify the standardized market key (e.g., 'player_points'),
    the associated market type (e.g., 'over_under'), its scope ('team' or 'player'), and any 
    applicable line value (e.g., 9.5 from 'To Score 10+ Points') and its outcome (e.g., yes/no, over/under).

    Parameters:
        market (str): The raw market name string from the sportsbook (e.g., "To Record 2+ Hits").
        league (str): The league key (e.g., "nba", "mlb") used for league-specific alias mappings.

    Returns:
        tuple[str, str, float | None]: A tuple of (market_name, market_type, line), where:
            - market_name: standardized slug identifier (e.g., 'player_points')
            - market_type: general market category (e.g., 'over_under', 'moneyline', 'yes_no')
            - scope: the scope of the market (e.g., 'player')
            - line: float line value if extracted (e.g., 1.5), otherwise None
            - outcome: outcome of the prop if extracted (e.g., 'over'), otherwise None

    Raises:
        NormalizationError: If no known or pattern-matched alias can be identified for the input.
    """
    key = (league, clean_str(market))
    if key in REVERSE_MARKET_LOOKUP:
        market_name, market_type, market_scope = REVERSE_MARKET_LOOKUP[key]
        return market_name, market_type, market_scope, None, None

    exact_result = MARKET_EXACT_RESULT_PATTERN.search(market)
    if exact_result:
        # Convert a counting prop in yes format into its respective over format
        # (e.g., To Record 2+ Hits -> Over 1.5 Hits)
        raw_line = exact_result.group('line')
        raw_market = exact_result.group('market')

        if not raw_line or not raw_market:
            raise NormalizationError(f'Invalid format in market with line: `{market}`')

        line = 1 if raw_line.lower() in {'a', 'an'} else float(raw_line.replace('+', ''))
        line -= 0.5

        key = (league, clean_str(raw_market))
        if key not in REVERSE_MARKET_LOOKUP:
            raise NormalizationError(f'Unknown exact result market `{raw_market}`')

        market_name, market_type, market_scope = REVERSE_MARKET_LOOKUP[key]
        outcome = 'over' if market_type == 'over_under' else 'yes'
        return market_name, market_type, market_scope, line, outcome

    over_under = MARKET_OVER_UNDER_PATTERN.search(market)
    if over_under:
        raw_scope = over_under.groupdict().get('scope', '')
        raw_market = over_under.group('market')
        line, outcome = None, None # These will be determined later

        if not raw_market:
            raise NormalizationError(f'Invalid format in market without line: `{market}`')

        combined = f'{raw_scope} {raw_market}'.strip() if raw_scope else raw_market
        key = (league, clean_str(combined))
        if key not in REVERSE_MARKET_LOOKUP:
            raise NormalizationError(f'Unknown over/under market `{combined}`')

        market_name, market_type, market_scope = REVERSE_MARKET_LOOKUP[key]
        return market_name, market_type, market_scope, line, outcome

    scope_included = MARKET_SCOPE_INCLUDED_PATTERN.search(market)
    if scope_included:
        raw_scope = scope_included.group('scope')
        raw_market = scope_included.group('market')
        line, outcome = None, None # These will be determined later

        key = (league, clean_str(raw_market))
        if key not in REVERSE_MARKET_LOOKUP:
            raise NormalizationError(f'Unknown scope-included market `{market}` in scope-based format')

        market_name, market_type, _ = REVERSE_MARKET_LOOKUP[key]
        return market_name, market_type, raw_scope, line, outcome

    raise NormalizationError(f'Unknown market name `{market}` for league `{league}`')


def get_market_type(market: str, league: str) -> str:
    """Gets the market type from a market and league name."""
    key = (league, market)
    if key not in REVERSE_MARKET_LOOKUP:
        raise NormalizationError(f'Unknown market name `{market}` for league `{league}`')
    _, market_type, _ = REVERSE_MARKET_LOOKUP[key]
    return market_type


def normalize_status_name(status: str, event: bool) -> str:
    """Normalizes a sportbook's event status to a standard format."""
    status_aliases = EVENT_STATUS_ALIASES if event else ODDS_STATUS_ALIASES
    for standard, statuses in status_aliases.items():
        if clean_str(status) in map(clean_str, statuses):
            return standard
    raise NormalizationError(f'Unknown status name `{status}`')


def get_sport_from_league(league: str) -> str:
    """Gets the league's respective sport."""
    for sport, leagues in SPORTS_LEAGUES.items():
        if clean_str(league) in map(clean_str, leagues):
            return sport
    raise NormalizationError(f'Unknown league `{league}`')


def format_odds(odds_data: dict) -> str:
    """Formats odds data into a readable string."""
    market = odds_data['market']
    league = odds_data['event_key'].split(':')[0]
    market_type = get_market_type(market, league)
    outcome = odds_data['outcome']
    line = odds_data['line']
    value = decimal_to_american(odds_data['value'])
    team = odds_data['team']
    player = odds_data['player']
    if market_type == 'moneyline':
        odds_str = f'{outcome} {market} ({value})'
    elif market_type in ['spread', 'total']:
        odds_str = f'{outcome} {line} {market} ({value})'
    elif market_type == 'over_under':
        team_or_player = (team or player) if team or player else ''
        seperator = ' ' if team_or_player else ''
        odds_str = f'{team_or_player}{seperator}{outcome} {line} {market} ({value})'
    elif market_type == 'yes_no':
        team_or_player = (team or player) if team or player else ''
        seperator = ' ' if team_or_player else ''
        odds_str = f'{team_or_player}{seperator}{outcome} {market} ({value})'
    else:
        raise NormalizationError(f'Unknown market type for `{market}`')
    
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