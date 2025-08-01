EFFICIENCY_STATS = {
    '3rd down efficiency': ('third_down_conversions', 'third_down_attempts'),
    '4th down efficiency': ('fourth_down_conversions', 'fourth_down_attempts'),
    'Red Zone (Made-Att)': ('red_zone_conversions', 'red_zone_attempts'),
    'Comp/Att': ('total_pass_completions', 'total_pass_attempts'),
}

FOOTBALL_STATS_ALIASES = {
    # Team Stats
    'total_first_downs': ['1st Downs',],
    'pass_first_downs': ['Passing 1st downs',],
    'rush_first_downs': ['Rushing 1st downs',],
    'total_plays': ['Total Plays',],
    'total_yards': ['Total Yards',],
    'total_drives': ['Total Drives',],
    'yards_per_play': ['Yards per Play',],
    'turnovers': ['Turnovers',],
    'fumbles': ['Fumbles lost',],
    'def_tds': ['Defensive / Special Teams TDs',],
    'possession_time': ['Possession'],
    # Passing Stats
    'pass_completions': ['Completions',],
    'pass_attempts': ['Passing Attempts',],
    'pass_yards': ['Passing Yards', 'Passing',],
    'pass_yards_per_attempt': ['Yards per pass', 'Yards Per Pass Attempt',],
    'pass_tds': ['Passing Touchdowns',],
    'pass_longest': ['Longest Pass',],
    'interceptions': ['Interceptions', 'Interceptions thrown'],
    'sacks_taken': ['Total Sacks'],
    'passer_rating': ['Passer Rating',],
    'qbr': ['Adjusted QBR',],
    # Rushing Stats
    'rush_attempts': ['Rushing Attempts',],
    'rush_yards': ['Rushing Yards', 'Rushing'],
    'rush_yards_per_attempt': ['Yards per rush', 'Yards Per Rush Attempt'],
    'rush_tds': ['Rushing Touchdowns',],
    'rush_longest': ['Long Rushing',],
    # Receiving Stats
    'receptions': ['Receptions',],
    'targets': ['Receiving Targets',],
    'rec_yards': ['Receiving Yards',],
    'rec_tds': ['Receiving Touchdowns',],
    'rec_longest': ['Long Reception',],
}

BASKETBALL_STATS_ALIASES = {}

BASEBALL_STATS_ALIASES = {}

SOCCER_STATS_ALIASES = {}

HOCKEY_STATS_ALIASES = {}

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
    for standard, aliases in stats_aliases.items():
        for alias in aliases:
            REVERSE_STATS_LOOKUP[(league, alias)] = standard