FOOTBALL_STATS_ALIASES = {
    # Team Stats
    'points_scored':  {
        'type': 'volume',
        'aliases': [],
    },
    'points_allowed':  {
        'type': 'volume',
        'aliases': [],
    },
    'total_first_downs': {
        'type': 'volume',
        'aliases': ['1st Downs'],
    },
    'pass_first_downs': {
        'type': 'volume',
        'aliases': ['Passing 1st downs'],
    },
    'rush_first_downs': {
        'type': 'volume',
        'aliases': ['Rushing 1st downs'],
    },
    'total_plays': {
        'type': 'volume',
        'aliases': ['Total Plays'],
    },
    'total_yards': {
        'type': 'volume',
        'aliases': ['Total Yards'],
    },
    'total_drives': {
        'type': 'volume',
        'aliases': ['Total Drives'],
    },
    'yards_per_play': {
        'type': 'rate',
        'aliases': ['Yards per Play'],
    },
    'third_down_conversions': {
        'type': 'volume',
        'aliases': [],
    },
    'third_down_attempts': {
        'type': 'volume',
        'aliases': [],
    },
    'third_down_efficiency': {
        'type': 'efficiency',
        'aliases': [('third_down_conversions', 'third_down_attempts'),],
    },
    'fourth_down_conversions': {
        'type': 'volume',
        'aliases': [],
    },
    'fourth_down_attempts': {
        'type': 'volume',
        'aliases': [],
    },
    'fourth_down_efficiency': {
        'type': 'efficiency',
        'aliases': [('fourth_down_conversions', 'fourth_down_attempts'),],
    },
    'red_zone_conversions': {
        'type': 'volume',
        'aliases': [],
    },
    'red_zone_attempts': {
        'type': 'efficiency',
        'aliases': [],
    },
    'red_zone_efficiency': {
        'type': 'efficiency',
        'aliases': [('red_zone_conversions', 'red_zone_attempts'),],
    },
    'turnovers': {
        'type': 'volume',
        'aliases': ['Turnovers'],
    },
    'fumbles': {
        'type': 'volume',
        'aliases': ['Fumbles lost'],
    },
    'def_tds': {
        'type': 'volume',
        'aliases': ['Defensive / Special Teams TDs'],
    },
    'possession_time': {
        'type': 'time',
        'aliases': ['Possession'],
    },
    # Passing Stats
    'pass_completions': {
        'type': 'volume',
        'aliases': ['Completions'],
    },
    'pass_attempts': {
        'type': 'volume',
        'aliases': ['Passing Attempts'],
    },
    'pass_yards': {
        'type': 'volume',
        'aliases': ['Passing Yards', 'Passing'],
    },
    'pass_yards_per_attempt': {
        'type': 'rate',
        'aliases': ['Yards per pass', 'Yards Per Pass Attempt'],
    },
    'pass_tds': {
        'type': 'volume',
        'aliases': ['Passing Touchdowns'],
    },
    'pass_longest': {
        'type': 'rate',
        'aliases': ['Longest Pass'],
    },
    'pass_efficiency': {
        'type': 'efficiency',
        'aliases': [('pass_completions', 'pass_attempts'),],
    },
    'interceptions': {
        'type': 'volume',
        'aliases': ['Interceptions', 'Interceptions thrown'],
    },
    'sacks_taken': {
        'type': 'volume',
        'aliases': ['Total Sacks'],
    },
    'passer_rating': {
        'type': 'rate',
        'aliases': ['Passer Rating'],
    },
    'qbr': {
        'type': 'rate',
        'aliases': ['Adjusted QBR'],
    },
    # Rushing Stats
    'rush_attempts': {
        'type': 'volume',
        'aliases': ['Rushing Attempts'],
    },
    'rush_yards': {
        'type': 'volume',
        'aliases': ['Rushing Yards', 'Rushing'],
    },
    'rush_yards_per_attempt': {
        'type': 'rate',
        'aliases': ['Yards per rush', 'Yards Per Rush Attempt'],
    },
    'rush_tds': {
        'type': 'volume',
        'aliases': ['Rushing Touchdowns'],
    },
    'rush_longest': {
        'type': 'rate',
        'aliases': ['Long Rushing'],
    },
    # Receiving Stats
    'receptions': {
        'type': 'volume',
        'aliases': ['Receptions'],
    },
    'targets': {
        'type': 'volume',
        'aliases': ['Receiving Targets'],
    },
    'rec_yards': {
        'type': 'volume',
        'aliases': ['Receiving Yards'],
    },
    'rec_tds': {
        'type': 'volume',
        'aliases': ['Receiving Touchdowns'],
    },
    'rec_longest': {
        'type': 'rate',
        'aliases': ['Long Reception'],
    },
}

BASKETBALL_STATS_ALIASES = {}

BASEBALL_STATS_ALIASES = {}

SOCCER_STATS_ALIASES = {}

HOCKEY_STATS_ALIASES = {}

EFFICIENCY_ALIASES = {
    '3rd down efficiency': ('third_down_conversions', 'third_down_attempts'),
    '4th down efficiency': ('fourth_down_conversions', 'fourth_down_attempts'),
    'Red Zone (Made-Att)': ('red_zone_conversions', 'red_zone_attempts'),
    'Comp/Att': ('pass_completions', 'pass_attempts'),
}

STATS_ALIASES = {
    'nfl': FOOTBALL_STATS_ALIASES,
    'nba': BASKETBALL_STATS_ALIASES,
    'mlb': BASEBALL_STATS_ALIASES,
    'mls': SOCCER_STATS_ALIASES,
    'nhl': HOCKEY_STATS_ALIASES,
    'ncaaf': FOOTBALL_STATS_ALIASES,
    'ncaab': BASKETBALL_STATS_ALIASES,
    'ncaaw': BASKETBALL_STATS_ALIASES,
}

REVERSE_STATS_LOOKUP = {}
for league, stats_aliases in STATS_ALIASES.items():
    for standard, mapping in stats_aliases.items():
        REVERSE_STATS_LOOKUP[(league, standard)] = (standard, mapping['type'])
        for alias in mapping['aliases']:
            REVERSE_STATS_LOOKUP[(league, alias)] = (standard, mapping['type'])