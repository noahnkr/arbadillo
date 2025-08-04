FOOTBALL_MARKET_TO_STATS = {
    'moneyline': {
        'context': 'team',
        'label': 'winner',
        'stats': [
            'points_scored', 'points_allowed', 
            'total_plays', 'total_yards', 'total_drives',
            'yards_per_play', 'turnovers', 'possession_time',
            'third_down_efficiency', 'fourth_down_efficiency', 'red_zone_efficiency'
        ]
    },
    'spread': {
        'context': 'team',
        'label': 'margin',
        'stats': [
            'points_scored', 'points_allowed', 'total_yards',
            'turnovers', 'third_down_conversions', 'third_down_attempts',
            'fourth_down_conversions', 'fourth_down_attempts',
            'total_plays', 'yards_per_play', 'total_drives',
        ]
    },
    'total': {
        'context': 'team',
        'label': 'total',
        'stats': [
            'points_scored', 'points_allowed',
            'total_yards', 'total_plays', 'total_drives',
            'yards_per_play', 'turnovers', 'possession_time',
            'red_zone_conversions', 'red_zone_attempts', 'def_tds', 
        ]
    },
}

BASKETBALL_MARKET_TO_STATS = {}

BASEBALL_MARKET_TO_STATS = {}

SOCCER_MARKET_TO_STATS = {}

HOCKEY_MARKET_TO_STATS = {}

MARKET_TO_STATS = {
    'nfl': FOOTBALL_MARKET_TO_STATS,
    'nba': BASKETBALL_MARKET_TO_STATS,
    'mlb': BASEBALL_MARKET_TO_STATS,
    'mls': SOCCER_MARKET_TO_STATS,
    'nhl': HOCKEY_MARKET_TO_STATS,
    'ncaaf': FOOTBALL_MARKET_TO_STATS,
    'ncaab': BASKETBALL_MARKET_TO_STATS,
    'ncaaw': BASKETBALL_MARKET_TO_STATS,
}