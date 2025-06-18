SPORTSBOOKS = { 'espn', 'fanduel', 'draftkings', 'betmgm', 'bet365', 'caesars', 'fanatics', 'betrivers', }

SPORTS = { 'football', 'basketball', 'baseball', 'soccer', 'hockey', }

LEAGUES = { 'nfl', 'nba', 'mlb', 'mls', 'nhl', 'ncaaf', 'ncaab', 'ncaaw', }

SPORTS_LEAGUES = {
    'football': ['nfl', 'ncaaf',],
    'basketball': ['nba', 'ncaab', 'ncaaw',],
    'baseball': ['mlb',],
    'soccer': ['mlb'],
    'hockey': ['nhl',],
}

EVENT_STATUSES = { 'upcoming', 'active', 'completed' }

ODDS_STATUSES = { 'active', 'suspended' }

PRIMARY_MARKETS = { 'moneyline', 'spread', 'total' }

MARKET_TYPES = { 'moneyline', 'spread', 'total', 'over_under', 'yes_no', }

# ---------- Redis TTLs ----------

EVENT_EXPIRATION_TIME = 60 * 60 * 24

ODDS_EXPIRATION_TIME = 60 * 60

PLAYER_EXPIRATION_TIME = 60 * 60 * 24 * 7

TEAM_EXPIRATION_TIME = 60 * 60 * 24 * 7

CLIENT_SCRAPERS = { 'espn', 'draftkings', 'fanduel', }

CLIENT_MAP = {
    'espn': 'scraper.apiclients.espn.ESPNClient',
    'draftkings': 'scraper.apiclients.draftkings.DraftKingsClient',
    'fanduel': 'scraper.apiclients.fanduel.FanDuelClient',
}