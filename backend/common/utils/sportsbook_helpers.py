from common.utils.strings import clean_str, extract_float
from common.constants.aliases import (
    REVERSE_MARKET_LOOKUP, REVERSE_TEAM_LOOKUP, EVENT_STATUS_ALIASES, SELECTION_STATUS_ALIASES, 
    MARKET_REGEXES, PRIMARY_MARKET_REGEX, MARKET_OUTCOME_REGEXES,
)
from common.constants.sports_definitions import SPORTS_LEAGUES
from common.exceptions import NormalizationError

def create_event_key(date: str, away:str, home:str) -> str:
    """Generate event key (primary ID) for database and Redis."""
    return f'{date}:{away}@{home}'


def create_market_key(
        market: str, line: float = None, team: str = None, player: str = None
    ) -> str:
    """Creates an index on a specific market selection across sportsbooks."""
    components = [market]
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


def get_market_type(market: str, league: str) -> str:
    """Gets the market type from a market and league name."""
    key = (league, market)
    if key not in REVERSE_MARKET_LOOKUP:
        raise ValueError(f'Unknown market name: {market} ({league})')
    _, market_type = REVERSE_MARKET_LOOKUP[key]
    return market_type


def get_sport_from_league(league: str) -> str:
    """Gets the league's respective sport."""
    for sport, leagues in SPORTS_LEAGUES.items():
        if clean_str(league) in map(clean_str, leagues):
            return sport
    raise NormalizationError(f'Unknown league: {league}')


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


def parse_market_name(market_name: str, league: str) -> tuple[str, str, float | None, str | None, str | None]:
    line, team, player = None, None, None
    primary_match = PRIMARY_MARKET_REGEX.search(market_name)
    prop_match = MARKET_REGEXES[league].search(market_name)
    if primary_match:
        group_keys = ['alternate', 'period', 'market']
        market_key = ' '.join(primary_match.group(k) for k in group_keys if primary_match.group(k))
        line = extract_float(primary_match.group('line'))

        matched_keys = [v for k,v in primary_match.groupdict().items() if v]
        residual = market_name
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
        residual = market_name
        for mk in matched_keys:
            residual = residual.replace(mk, '')
        residual = residual.strip()
        player = residual if residual else None

    elif (league, clean_str(market_name)) not in REVERSE_MARKET_LOOKUP:
            raise NormalizationError(f'Invalid market format: {market_name} ({league})')

    else:
        market_key = market_name

    key = (league, clean_str(market_key))
    if key not in REVERSE_MARKET_LOOKUP:
        raise NormalizationError(f'Unsupported alias: {market_key} ({league})')

    parsed_market_name, market_type = REVERSE_MARKET_LOOKUP[key]
    return parsed_market_name, market_type, line, team, player


def parse_market_outcome(outcome_name: str, market_type: str, league: str) -> tuple[str, str | None, float | None]:
    outcome_regex = MARKET_OUTCOME_REGEXES[market_type]
    match = outcome_regex.match(outcome_name)
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
        raise NormalizationError(f'Invalid outcome format: {outcome_name} [{market_type}] ({league})')


def normalize_status_name(status: str, is_odds=True) -> str:
    """Normalizes a sportbook's event status to a standard format."""
    status_aliases = SELECTION_STATUS_ALIASES if is_odds else EVENT_STATUS_ALIASES
    for standard, statuses in status_aliases.items():
        if clean_str(status) in map(clean_str, statuses):
            return standard
    raise NormalizationError(f'Unknown status name: {status}')


def correct_over_under_line(market_type: str, line) -> float:
    """Adjusts even-number over/under lines (like 2+) to 1.5 if the market is over_under."""
    if isinstance(line, str):
        line = extract_float(line)
    if not line:
        return None
    if market_type == 'over_under' and line % 1 == 0:
        line -= 0.5

    return line

