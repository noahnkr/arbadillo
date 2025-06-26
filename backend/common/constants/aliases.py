import re
from common.utils.strings import clean_str

# ---------- Market Aliases ----------

PRIMARY_MARKET_ALIASES = {
    # Standard & Alternative Markets
    'moneyline': {
        'type': 'moneyline',
        'aliases': ['moneyline', 'money line', 'ml', 'h2h']
    },
    'spread': {
        'type': 'spread',
        'aliases': ['spread', 'point spread', 'spread betting', 'run line', 'puck line', 'handicap', 'line', 'ats']
    },
    'total': {
        'type': 'total',
        'aliases': ['total', 'game total', 'total points', 'match total', 'points total', 'goals total', 'runs total', 'over/under']
    },
    'alt_spread': {
        'type': 'spread',
        'aliases': [
            'alternate spread', 'alt spread', 'alternate line', 'alt. spread',
            'alternate puck line', 'alt puck line',
            'alternate run line', 'alt run line',
            'alternate run lines', 'alt run lines',
        ]
    },
    'alt_total': {
        'type': 'total',
        'aliases': [
            'alternate total', 'alt total', 'alt. total',
            'alternate totals','alt totals', 'alt. totals',
            'alternate game total', 'alternate runs total', 
            'alternate goals total', 'alternate points total',
        ]
    },
    # Stabdard & Alternative Team Markets
    'team_total': {
        'type': 'total',
        'aliases': ['team total', 'team totals',],
    },
    'alt_team_total': {
        'type': 'total',
        'aliases': ['alternate team total', 'alt team total', 'alt. team total', 'team alternate total', 'team alt total', 'team alt. total'],
    },
    # Halves Standard & Alternative Markets
    'moneyline_h1': {
        'type': 'moneyline',
        'aliases': ['1st half moneyline', 'first half moneyline', '1st half money line', 'first half money line']
    },
    'spread_h1': {
        'type': 'spread',
        'aliases': ['1st half spread', 'first half spread']
    },
    'total_h1': {
        'type': 'total',
        'aliases': ['1st half total', 'first half total']
    },
    'alt_spread_h1': {
        'type': 'spread',
        'aliases': ['alternate 1st half spread', 'alt 1st half spread', 'alt spread 1h']
    },
    'alt_total_h1': {
        'type': 'total',
        'aliases': ['alternate 1st half total', 'alt 1st half total', 'alt total 1h']
    },
    'moneyline_h2': {
        'type': 'moneyline',
        'aliases': ['2nd half moneyline', 'second half moneyline', '2nd half money line', 'second half money line']
    },
    'spread_h2': {
        'type': 'spread',
        'aliases': ['2nd half spread', 'second half spread']
    },
    'total_h2': {
        'type': 'total',
        'aliases': ['2nd half total', 'second half total']
    },
    'alt_spread_h2': {
        'type': 'spread',
        'aliases': ['alternate 2nd half spread', 'alt 2nd half spread', 'alt spread 2h']
    },
    'alt_total_h2': {
        'type': 'total',
        'aliases': ['alternate 2nd half total', 'alt 2nd half total', 'alt total 2h']
    },
    # Quarters Standard & Alternative Markets
    'moneyline_q1': {
        'type': 'moneyline',
        'aliases': ['1st quarter moneyline', 'first quarter moneyline', '1st quarter money line', 'first quarter money line']
    },
    'spread_q1': {
        'type': 'spread',
        'aliases': ['1st quarter spread', 'first quarter spread']
    },
    'total_q1': {
        'type': 'total',
        'aliases': ['1st quarter total', 'first quarter total']
    },
    'alt_spread_q1': {
        'type': 'spread',
        'aliases': ['alternate 1st quarter spread', 'alt 1st quarter spread', 'alt spread q1']
    },
    'alt_total_q1': {
        'type': 'total',
        'aliases': ['alternate 1st quarter total', 'alt 1st quarter total', 'alt total q1']
    },
    'moneyline_q2': {
        'type': 'moneyline',
        'aliases': ['2nd quarter moneyline', 'second quarter moneyline', '2nd quarter money line', 'second quarter money line']
    },
    'spread_q2': {
        'type': 'spread',
        'aliases': ['2nd quarter spread', 'second quarter spread']
    },
    'total_q2': {
        'type': 'total',
        'aliases': ['2nd quarter total', 'second quarter total']
    },
    'alt_spread_q2': {
        'type': 'spread',
        'aliases': ['alternate 2nd quarter spread', 'alt 2nd quarter spread', 'alt spread q2']
    },
    'alt_total_q2': {
        'type': 'total',
        'aliases': ['alternate 2nd quarter total', 'alt 2nd quarter total', 'alt total q2']
    },
    'moneyline_q3': {
        'type': 'moneyline',
        'aliases': ['3rd quarter moneyline', 'third quarter moneyline', '3rd quarter money line', 'third quarter money line']
    },
    'spread_q3': {
        'type': 'spread',
        'aliases': ['3rd quarter spread', 'third quarter spread']
    },
    'total_q3': {
        'type': 'total',
        'aliases': ['3rd quarter total', 'third quarter total']
    },
    'alt_spread_q3': {
        'type': 'spread',
        'aliases': ['alternate 3rd quarter spread', 'alt 3rd quarter spread', 'alt spread q3']
    },
    'alt_total_q3': {
        'type': 'total',
        'aliases': ['alternate 3rd quarter total', 'alt 3rd quarter total', 'alt total q3']
    },
    'moneyline_q4': {
        'type': 'moneyline',
        'aliases': ['4th quarter moneyline', 'fourth quarter moneyline', '4th quarter money line', 'fourth quarter money line']
    },
    'spread_q4': {
        'type': 'spread',
        'aliases': ['4th quarter spread', 'fourth quarter spread']
    },
    'total_q4': {
        'type': 'total',
        'aliases': ['4th quarter total', 'fourth quarter total']
    },
    'alt_spread_q4': {
        'type': 'spread',
        'aliases': ['alternate 4th quarter spread', 'alt 4th quarter spread', 'alt spread q4']
    },
    'alt_total_q4': {
        'type': 'total',
        'aliases': ['alternate 4th quarter total', 'alt 4th quarter total', 'alt total q4']
    },
    # Baseball - Period Markets
    'moneyline_f5': {
        'type': 'moneyline',
        'aliases': ['first 5 innings moneyline', 'f5 moneyline', 'first 5 innings money line']
    },
    'spread_f5': {
        'type': 'spread',
        'aliases': ['first 5 innings spread', 'f5 spread', 'first 5 innings run line']
    },
    'total_f5': {
        'type': 'total',
        'aliases': ['first 5 innings total', 'f5 total']
    },
    'alt_spread_f5': {
        'type': 'spread',
        'aliases': ['alternate first 5 innings spread', 'alternate first 5 innings run line', 'alternate first 5 innings run lines']
    },
    'alt_total_f5': {
        'type': 'total',
        'aliases': ['alternate first 5 innings total', 'alt f5 total']
    },
    'moneyline_f7': {
        'type': 'moneyline',
        'aliases': ['first 7 innings moneyline', 'f7 moneyline']
    },
    'spread_f7': {
        'type': 'spread',
        'aliases': ['first 7 innings spread', 'f7 spread']
    },
    'total_f7': {
        'type': 'total',
        'aliases': ['first 7 innings total', 'f7 total']
    },
    'alt_spread_f7': {
        'type': 'spread',
        'aliases': ['alternate first 7 innings spread', 'alt f7 spread']
    },
    'alt_total_f7': {
        'type': 'total',
        'aliases': ['alternate first 7 innings total', 'alt f7 total']
    },
    'total_1st': {
        'type': '',
        'aliases': ['1st inning over/under'],
    },
    'total_2nd': {
        'type': '',
        'aliases': ['2nd inning over/under'],
    },
    'total_3rd': {
        'type': '',
        'aliases': ['3rd inning over/under'],
    },
    'total_4th': {
        'type': '',
        'aliases': ['4th inning over/under'],
    },
    'total_5th': {
        'type': '',
        'aliases': ['5th inning over/under'],
    },
    'total_6th': {
        'type': '',
        'aliases': ['6th inning over/under'],
    },
    'total_7th': {
        'type': '',
        'aliases': ['7th inning over/under'],
    },
    'total_8th': {
        'type': '',
        'aliases': ['8th inning over/under'],
    },
    'total_9th': {
        'type': '',
        'aliases': ['9th inning over/under'],
    },
    # Hockey - Period Markets
    'moneyline_p1': {
        'type': 'moneyline',
        'aliases': ['1st period moneyline', 'first period moneyline']
    },
    'spread_p1': {
        'type': 'spread',
        'aliases': ['1st period spread', 'first period spread']
    },
    'total_p1': {
        'type': 'total',
        'aliases': ['1st period total', 'first period total']
    },
    'alt_spread_p1': {
        'type': 'spread',
        'aliases': ['alternate 1st period spread', 'alt period 1 spread', 'alt p1 spread']
    },
    'alt_total_p1': {
        'type': 'total',
        'aliases': ['alternate 1st period total', 'alt p1 total']
    },
    'moneyline_p2': {
        'type': 'moneyline',
        'aliases': ['2nd period moneyline', 'second period moneyline']
    },
    'spread_p2': {
        'type': 'spread',
        'aliases': ['2nd period spread', 'second period spread']
    },
    'total_p2': {
        'type': 'total',
        'aliases': ['2nd period total', 'second period total']
    },
    'alt_spread_p2': {
        'type': 'spread',
        'aliases': ['alternate 2nd period spread', 'alt p2 spread']
    },
    'alt_total_p2': {
        'type': 'total',
        'aliases': ['alternate 2nd period total', 'alt p2 total']
    },
    'moneyline_p3': {
        'type': 'moneyline',
        'aliases': ['3rd period moneyline', 'third period moneyline']
    },
    'spread_p3': {
        'type': 'spread',
        'aliases': ['3rd period spread', 'third period spread']
    },
    'total_p3': {
        'type': 'total',
        'aliases': ['3rd period total', 'third period total']
    },
    'alt_spread_p3': {
        'type': 'spread',
        'aliases': ['alternate 3rd period spread', 'alt p3 spread']
    },
    'alt_total_p3': {
        'type': 'total',
        'aliases': ['alternate 3rd period total', 'alt p3 total']
    },
}

FOOTBALL_MARKET_ALIASES = {}

BASKETBALL_MARKET_ALIASES = {
    'player_points': {
        'type': 'over_under',
        'aliases': ['points', 'point', 'pts', 'player points', 'total points', 'points milestones']
    },
    'player_rebounds': {
        'type': 'over_under',
        'aliases': ['rebounds', 'rebound', 'reb', 'player rebounds', 'total rebounds', 'rebounds milestones']
    },
    'player_assists': {
        'type': 'over_under',
        'aliases': ['assists', 'assist', 'ast', 'player assists', 'total assists', 'assists milestones']
    },
    'player_threes': {
        'type': 'over_under',
        'aliases': ['threes', 'three', '3-point field goals', '3-pointers', 'player threes', 'total 3-point field goals', 'threes milestones']
    },
    'player_steals': {
        'type': 'over_under',
        'aliases': ['steals', 'steal', 'stl', 'player steals', 'total steals', 'steals milestones']
    },
    'player_blocks': {
        'type': 'over_under',
        'aliases': ['blocks', 'block', 'blk', 'player blocks', 'total blocks', 'blocks milestones']
    },
    'player_turnovers': {
        'type': 'over_under',
        'aliases': ['turnovers', 'turnover', 'tov','player turnovers', 'total turnovers', 'turnovers milestones']
    },
    'player_points_rebounds_assists': {
        'type': 'over_under',
        'aliases': [
            'points + rebounds + assists', 'pts + reb + ast',
            'points, rebounds, and assists',
            'total points, rebounds, and assists',
            'player points, rebounds, and assists',
            'points + rebounds + assists milestones'
        ]
    },
    'player_points_rebounds': {
        'type': 'over_under',
        'aliases': [
            'points + rebounds', 'pts + reb',
            'points and rebounds', 'total points and rebounds',
            'player points and rebounds',
            'points + rebounds milestones'
        ]
    },
    'player_points_assists': {
        'type': 'over_under',
        'aliases': [
            'points + assists', 'pts + ast',
            'points and assists', 'total points and assists',
            'player points and assists',
            'points + assists milestones'
        ]
    },
    'player_rebounds_assists': {
        'type': 'over_under',
        'aliases': [
            'rebounds + assists', 'reb + ast',
            'rebounds and assists', 'total rebounds and assists',
            'player rebounds and assists',
            'rebounds + assists milestones'
        ]
    },
    'player_steals_blocks': {
        'type': 'over_under',
        'aliases': [
            'steals + blocks', 'stl + blk',
            'steals and blocks', 'total steals and blocks',
            'player steals and blocks',
            'steals + blocks milestones'
        ]
    },
    'player_double_double': {
        'type': 'yes_no',
        'aliases': ['double double', 'to record a double double']
    },
    'player_triple_double': {
        'type': 'yes_no',
        'aliases': ['triple double', 'to record a triple double']
    },
}

BASEBALL_MARKET_ALIASES = {
    'batter_home_runs': {
        'type': 'over_under',
        'aliases': ['home runs', 'home run', 'batter home runs', 'player home runs', 'total home runs', 'total home runs hit', 'home runs milestones']
    },
    'batter_hits': {
        'type': 'over_under',
        'aliases': ['hits', 'hit', 'batter hits', 'player hits'],
    },
    'batter_total_bases': {
        'type': 'over_under',
        'aliases': ['total bases', 'bases', 'base', 'batter total bases', 'batter total base', 'player bases', 'player base', 'player total bases', 'player total base', 'total bases milestones']
    },
    'batter_rbis': {
        'type': 'over_under',
        'aliases': ['rbi', 'rbis', 'batter rbis', 'batter rbi', 'player rbis', 'player rbi', 'total rbis', 'total rbi', 'rbis milestones']
    },
    'batter_singles': {
        'type': 'over_under',
        'aliases': ['singles', 'single', 'batter singles', 'batter single', 'player singles', 'player single', 'total singles hit', 'singles milestones']
    },
    'batter_doubles': {
        'type': 'over_under',
        'aliases': ['doubles', 'double', 'batter doubles', 'batter double', 'player doubles', 'player double', 'total doubles hit', 'doubles milestones']
    },
    'batter_triples': {
        'type': 'over_under',
        'aliases': ['triples', 'triple', 'batter triples', 'batter triple', 'player triples', 'player triple', 'total triples hit', 'triples milestones']
    },
    'batter_runs_scored': {
        'type': 'over_under',
        'aliases': ['run', 'runs', 'batter runs', 'batter run', 'player runs', 'player run' 'batter total runs', 'batter total runs scored'],
    },
    'batter_hits_runs_rbis': {
        'type': 'over_under',
        'aliases': ['hits + runs + rbis', 'batter hits + runs + rbis', 'player hits + runs + rbis', 'total hits + runs + rbis', 'hits + runs + rbis milestones']
    },
    'batter_stolen_bases': {
        'type': 'over_under',
        'aliases': ['stolen bases', 'stolen base', 'batter stolen bases', 'batter stolen base', 'player stolen bases', 'player stolen base', 'total stolen bases', 'total stolen base', 'stolen bases milestones']
    },
    'pitcher_strikeouts': {
        'type': 'over_under',
        'aliases': ['strikeouts', 'strikeout', 'pitcher strikeouts', 'player strikeouts', 'total strikeouts', 'strikeouts milestones']
    },
    'pitcher_walks': {
        'type': 'over_under',
        'aliases': ['walks', 'walk', 'walks allowed', 'pitcher walks', 'player walks', 'total walks allowed', 'walks milestones']
    },
    'pitcher_hits_allowed': {
        'type': 'over_under',
        'aliases': ['hits allowed', 'pitcher hits allowed', 'player hits allowed', 'total hits allowed', 'hits allowed milestones']
    },
    'pitcher_outs': {
        'type': 'over_under',
        'aliases': ['outs', 'out', 'outs recorded', 'pitcher outs', 'player outs', 'total outs recorded', 'outs milestones']
    }
}

SOCCER_MARKET_ALIASES = {}

HOCKEY_MARKET_ALIASES = {}

MARKET_ALIASES = {
    'nfl': {**FOOTBALL_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'nba': {**BASKETBALL_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'mlb': {**BASEBALL_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'mls': {**SOCCER_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'nhl': {**HOCKEY_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'ncaaf': {**FOOTBALL_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'ncaab': {**BASKETBALL_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
    'ncaaw': {**BASKETBALL_MARKET_ALIASES, **PRIMARY_MARKET_ALIASES},
}

REVERSE_MARKET_LOOKUP = {}
for league, league_aliases in MARKET_ALIASES.items():
    for standard, mapping in league_aliases.items():
        REVERSE_MARKET_LOOKUP[(league, standard)] = (standard, mapping['type'])
        for alias in mapping['aliases']:
            REVERSE_MARKET_LOOKUP[(league, clean_str(alias))] = (standard, mapping['type'])

# ---------- Market Regexes ----------

PRIMARY_MARKET_REGEX = re.compile(r'''
    ^.*?
    (?P<period>
        (?:
            1st|first|2nd|second|3rd|third|4th|fourth|5th|6th|7th|8th|9th|
            first\s+5|first\s+7)\s+
        (?:half|quarter|period|innings?|set|game)
    )?\s*
    (?P<alternate>alternate|alt\.?)?\s*
    (?P<market>
        money\s?lines? |
        spreads? |
        point\sspreads? |
        game\sspreads? |
        run\slines? |
        puck\slines? |
        totals? |
        over/under
    )\s*
    (?P<line>
        \(?\d+(?:\.\d+)?\+?\)?
    )?\s*
    (?P<suffix>line|points|runs|goals)?$
''', re.IGNORECASE | re.VERBOSE)

FOOTBALL_MARKET_REGEX = None

BASKETBALL_MARKET_REGEX = re.compile(r'''
    .*?
    (?:(?P<period>
        (?:1st|first|2nd|second|3rd|third|4th|fourth)\s+
        (?:half|quarter|game)
    ))?\s*
    (?P<scope>team|player)?\s*
    (?:to\s*score|to\s*make|to\s*record)?\s*
    (?P<line>a|an|\d+\+)?\s*
    (?:alternate|alt\.?)?\s*
    (?:total|made)?\s*
    (?P<market>
        (?:
            (?:points|pts|rebounds|reb|assists|ast|blocks|blks|steals|stls)
            \s*(?:\+|,|and)?\s*
            (?:points|pts|rebounds|reb|assists|ast|blocks|blks|steals|stls)?
            \s*(?:\+|,|and)?\s*
            (?:points|pts|rebounds|reb|assists|ast|blocks|blks|steals|stls)?
        ) | 
        (?:threes|3\s*-\s*pointers) | (?:turnovers|tovs) | (?:free\s*-?\s*throws|fts?) |
        (?:field\s*-?\s*goals|fgs?) | (?:(?:double|triple)\s*-?\s*double)
    )\s*
    (?:made)?\s*
    (?:o/u|over/under)?
''', re.IGNORECASE | re.VERBOSE)

BASEBALL_MARKET_REGEX = re.compile(r'''
    ^.*?
    (?P<dash>-)?
    (?:(?P<scope>team|player|pitcher|batter))?\s*
    (?P<task>to\s*(?:score|hit|record|allow))?\s*
    (?P<line>a|an|\d+\+)?\s*
    (?P<alternate>alternate|alt\.?)?\s*
    (?P<total>total)?\s*
    (?P<market>
        strikeouts? |
        earned\s*runs |
        home\s*runs? |
        stolen\s*bases? |
        total\s*bases? |
        singles? | doubles? | triples? |
        walks? | win |
        hits? |
        runs? |
        rbis? |
        hits\s*\+\s*runs\s*\+\s*rbis
    )
    (?P<suffix>\s+(?:hit|allowed|scored|recorded|thrown))?
    (?P<ou>\s*(?:o/u|over/under))?
    \s*$
''', re.IGNORECASE | re.VERBOSE)

SOCCER_MARKET_REGEX = None

HOCKEY_MARKET_REGEX = None

MARKET_REGEXES = {
    'nfl': FOOTBALL_MARKET_REGEX,
    'nba': BASKETBALL_MARKET_REGEX,
    'mlb': BASEBALL_MARKET_REGEX,
    'mls': SOCCER_MARKET_REGEX,
    'nhl': HOCKEY_MARKET_REGEX,
    'ncaaf': FOOTBALL_MARKET_REGEX,
    'ncaab': BASKETBALL_MARKET_REGEX,
    'ncaaw': BASKETBALL_MARKET_REGEX,
}

MONEYLINE_OUTCOME_REGEX = re.compile(r'^(?P<outcome>.+?)$', re.IGNORECASE)

SPREAD_OUTCOME_REGEX = re.compile(r'''
    ^\s*
    (?P<outcome>[A-Za-z .\-']+?)\s*
    (?:\(?(?P<line>[+-]?\d+(?:\.\d+)?)\)?)?
    \s*$
''', re.IGNORECASE | re.VERBOSE)

TOTAL_OVER_UNDER_OUTCOME_REGEX = re.compile(r'''
    ^(?:(?P<player>
        (?!over|under)\b
        [\wÀ-ÿ'`´\-]+
        (?:\s+(?!over|under)[\wÀ-ÿ'`´\-]+)*
    ))?\s*
    (?P<outcome>\b(?:over|under)\b)?\s*
    (?P<line>
        \(?\d+(?:\.\d+)?\+?\)?
    )?
    (?:\s+[A-Za-z ]+)?$
''', re.IGNORECASE | re.VERBOSE)

YES_NO_OUTCOME_REGEX = re.compile(r'''
    ^\s*
    (?P<player>.+?)?\s*
    (?P<outcome>\b(?:yes|no)\b)?
    \s*$
''', re.IGNORECASE | re.VERBOSE)

MARKET_OUTCOME_REGEXES = {
    'moneyline': MONEYLINE_OUTCOME_REGEX,
    'spread': SPREAD_OUTCOME_REGEX,
    'total': TOTAL_OVER_UNDER_OUTCOME_REGEX,
    'over_under': TOTAL_OVER_UNDER_OUTCOME_REGEX,
    'yes_no': YES_NO_OUTCOME_REGEX,
}

# ---------- Statuses ----------

EVENT_STATUS_ALIASES = {
    'upcoming': ['upcoming', 'scheduled', 'pre'],
    'active': ['active', 'current', 'LIVE', 'commenced', 'in'],
    'completed': ['completed', 'post',]
}

ODDS_STATUS_ALIASES = {
    'active': ['active', 'open', 'current', 'live', 'in'],
    'suspended': ['suspended', 'closed'],
}