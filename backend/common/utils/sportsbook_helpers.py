import hashlib
import json

from common.utils.strings import clean_str, extract_float
from common.constants.aliases import (
    REVERSE_MARKET_LOOKUP, REVERSE_TEAM_LOOKUP, EVENT_STATUS_ALIASES, ODDS_STATUS_ALIASES, 
    MARKET_REGEXES, PRIMARY_MARKET_REGEX, MARKET_OUTCOME_REGEXES,
)
from common.constants.sportsbook_definitions import SPORTS_LEAGUES, PRIMARY_MARKETS
from common.exceptions import NormalizationError

def create_event_key(league: str, date: str, away:str, home:str) -> str:
    """Generate event key (primary ID) for database and Redis."""
    return f'{league}:{date}:{away}@{home}'


def create_market_key(
        market: str, line: float = None, team: str = None, player: str = None
    ) -> str:
    """Creates an index on a specific market selection across sportsbooks."""
    components = [market]
    if market not in PRIMARY_MARKETS:
        if line: components.append(str(line))
        if player: components.append(player)
        if team: components.append(team)
    return ':'.join(components)


def get_team_key(name: str, league: str) -> str:
    if name is None:
        return None

    key = (league, clean_str(name))
    if key not in REVERSE_TEAM_LOOKUP:
        raise NormalizationError(f'Unkown team alias `{name}` for league `{league}`')
    
    return REVERSE_TEAM_LOOKUP[key]


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


def normalize_market_name(name: str, league: str) -> tuple[str, str, float | None, str | None, str | None]:
    line, team, player = None, None, None
    primary_match = PRIMARY_MARKET_REGEX.search(name)
    prop_match = MARKET_REGEXES[league].search(name)
    if primary_match:
        group_keys = ['alternate', 'period', 'market']
        market_key = ' '.join(primary_match.group(k) for k in group_keys if primary_match.group(k))
        line = extract_float(primary_match.group('line'))

        matched_keys = [v for k,v in primary_match.groupdict().items() if v]
        residual = name
        for mk in matched_keys:
            residual = residual.replace(mk, '')
        residual = residual.strip()
        team = residual if residual else None
        if team:
            market_key = f'team {market_key}'
            team = get_team_key(team, league)
        
    elif prop_match:
        group_keys = ['scope', 'market'] 
        market_key = ' '.join(prop_match.group(k) for k in group_keys if prop_match.group(k))
        line = prop_match.group('line')
        if (line or '').lower() in {'a', 'an'}:
            line = 1.0
        
        matched_keys = [v for k,v in prop_match.groupdict().items() if v]
        residual = name
        for mk in matched_keys:
            residual = residual.replace(mk, '')
        residual = residual.strip()
        player = residual if residual else None

    elif (league, clean_str(name)) not in REVERSE_MARKET_LOOKUP:
            raise NormalizationError(f'Invalid market format: {name} ({league})')

    else:
        market_key = name

    key = (league, clean_str(market_key))
    if key not in REVERSE_MARKET_LOOKUP:
        raise NormalizationError(f'Unsupported alias: {market_key} ({league})')

    market_name, market_type = REVERSE_MARKET_LOOKUP[key]
    return market_name, market_type, line, team, player


def normalize_market_outcome(market_outcome: str, market_type: str, league: str) -> tuple[str, str | None, float | None]:
    outcome_regex = MARKET_OUTCOME_REGEXES[market_type]
    match = outcome_regex.match(market_outcome)
    if match:
        outcome = match.groupdict().get('outcome', None)
        player = match.groupdict().get('player', None)
        line = match.groupdict().get('line', None)

        if market_type in {'moneyline', 'spread'}:
            outcome = get_team_key(outcome, league)
            line = extract_float(line)
        elif market_type in {'total', 'over_under'}:
            if not outcome:
                outcome = 'over'
            outcome = outcome.lower().strip()
            line = correct_over_under_line(market_type, line)
        return outcome, player, line
    else:
        raise NormalizationError(f'Invalid outcome format: {market_outcome} [{market_type}] ({league})')


def correct_over_under_line(market_type: str, line) -> float:
    """Adjusts even-number over/under lines (like 2+) to 1.5 if the market is over_under."""
    if isinstance(line, str):
        line = extract_float(line)
    if not line:
        return None
    if market_type == 'over_under' and line % 1 == 0:
        line -= 0.5

    return line


def get_market_type(market: str, league: str) -> str:
    """Gets the market type from a market and league name."""
    key = (league, market)
    if key not in REVERSE_MARKET_LOOKUP:
        raise NormalizationError(f'Unknown market name: {market} ({league})')
    _, market_type = REVERSE_MARKET_LOOKUP[key]
    return market_type


def normalize_status_name(status: str, is_odds=True) -> str:
    """Normalizes a sportbook's event status to a standard format."""
    status_aliases = ODDS_STATUS_ALIASES if is_odds else EVENT_STATUS_ALIASES
    for standard, statuses in status_aliases.items():
        if clean_str(status) in map(clean_str, statuses):
            return standard
    raise NormalizationError(f'Unknown status name: {status}')


def get_sport_from_league(league: str) -> str:
    """Gets the league's respective sport."""
    for sport, leagues in SPORTS_LEAGUES.items():
        if clean_str(league) in map(clean_str, leagues):
            return sport
    raise NormalizationError(f'Unknown league: {league}')


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
        team_or_blank = team if team else ''
        odds_str = f'{team_or_blank} {outcome} {line} {market} ({value})'.strip()
    elif market_type == 'over_under':
        team_or_player = (team or player) if team or player else ''
        odds_str = f'{team_or_player} {outcome} {line} {market} ({value})'.strip()
    elif market_type == 'yes_no':
        team_or_player = (team or player) if team or player else ''
        odds_str = f'{team_or_player} {outcome} {market} ({value})'.strip()
    else:
        raise ValueError(f'Unknown market type for market: {market}')

    return odds_str