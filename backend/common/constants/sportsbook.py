# ---------- Sportsbook Attributes ----------

SPORTSBOOKS = { 'espnbet', 'fanduel', 'draftkings', 'betmgm', 'bet365', 'caesars', 'fanatics', 'betrivers', }

SPORTS = { 'football', 'basketball', 'baseball', 'soccer', 'hockey', }

LEAGUES = { 'nfl', 'nba', 'mlb', 'mls', 'nhl', 'ncaaf', 'ncaab', 'ncaaw' }

SPORTS_LEAGUES = {
    'football': {'nfl', 'ncaaf',},
    'basketball': {'nba', 'ncaab', 'ncaaw',},
    'baseball': {'mlb',},
    'soccer': {'mls'},
    'hockey': {'nhl',},
}

EVENT_STATUSES = { 'upcoming', 'active', 'completed' }

ODDS_STATUSES = { 'active', 'suspended' }

PRIMARY_MARKETS = { 'moneyline', 'spread', 'total' }

MARKET_TYPES = { 'moneyline', 'spread', 'total', 'over_under', 'yes_no', }

# ---------- Clients ----------

SPORTSBOOK_CLIENTS = { 'espnbet', 'fanduel', 'draftkings' }

CLIENT_LEAGUES = { 'mlb', }

CLIENT_MAP = {
    'espnbet': 'oddsdata.apiclients.espnbet.ESPNBetClient',
    'draftkings': 'oddsdata.apiclients.draftkings.DraftKingsClient',
    'fanduel': 'oddsdata.apiclients.fanduel.FanDuelClient',
}

# ---------- Redis TTLs ----------

EVENT_TTL = 60 * 60 * 24

ODDS_TTL = 60 * 60