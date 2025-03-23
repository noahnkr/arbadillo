NBA_ALIASES = {
    # Atlanta Hawks
    "atlanta": "atlanta-hawks",
    "hawks": "atlanta-hawks",
    "atlanta-hawks": "atlanta-hawks",
    "atl": "atlanta-hawks",

    # Boston Celtics
    "boston": "boston-celtics",
    "celtics": "boston-celtics",
    "boston-celtics": "boston-celtics",
    "bos": "boston-celtics",

    # Brooklyn Nets
    "brooklyn": "brooklyn-nets",
    "nets": "brooklyn-nets",
    "brooklyn-nets": "brooklyn-nets",
    "bkn": "brooklyn-nets",

    # Charlotte Hornets
    "charlotte": "charlotte-hornets",
    "hornets": "charlotte-hornets",
    "charlotte-hornets": "charlotte-hornets",
    "cha": "charlotte-hornets",

    # Chicago Bulls
    "chicago": "chicago-bulls",
    "bulls": "chicago-bulls",
    "chicago-bulls": "chicago-bulls",
    "chi": "chicago-bulls",

    # Cleveland Cavaliers
    "cleveland": "cleveland-cavaliers",
    "cavaliers": "cleveland-cavaliers",
    "cleveland-cavaliers": "cleveland-cavaliers",
    "cle": "cleveland-cavaliers",

    # Dallas Mavericks
    "dallas": "dallas-mavericks",
    "mavericks": "dallas-mavericks",
    "dallas-mavericks": "dallas-mavericks",
    "dal": "dallas-mavericks",

    # Denver Nuggets
    "denver": "denver-nuggets",
    "nuggets": "denver-nuggets",
    "denver-nuggets": "denver-nuggets",
    "den": "denver-nuggets",

    # Detroit Pistons
    "detroit": "detroit-pistons",
    "pistons": "detroit-pistons",
    "detroit-pistons": "detroit-pistons",
    "det": "detroit-pistons",

    # Golden State Warriors
    "golden-state": "golden-state-warriors",
    "warriors": "golden-state-warriors",
    "golden-state-warriors": "golden-state-warriors",
    "gsw": "golden-state-warriors",

    # Houston Rockets
    "houston": "houston-rockets",
    "rockets": "houston-rockets",
    "houston-rockets": "houston-rockets",
    "hou": "houston-rockets",

    # Indiana Pacers
    "indiana": "indiana-pacers",
    "pacers": "indiana-pacers",
    "indiana-pacers": "indiana-pacers",
    "ind": "indiana-pacers",

    # LA Clippers
    "la": "la-clippers",
    "clippers": "la-clippers",
    "la-clippers": "la-clippers",
    "lac": "la-clippers",

    # Los Angeles Lakers
    "los-angeles": "los-angeles-lakers",
    "lakers": "los-angeles-lakers",
    "los-angeles-lakers": "los-angeles-lakers",
    "lal": "los-angeles-lakers",

    # Memphis Grizzlies
    "memphis": "memphis-grizzlies",
    "grizzlies": "memphis-grizzlies",
    "memphis-grizzlies": "memphis-grizzlies",
    "mem": "memphis-grizzlies",

    # Miami Heat
    "miami": "miami-heat",
    "heat": "miami-heat",
    "miami-heat": "miami-heat",
    "mia": "miami-heat",

    # Milwaukee Bucks
    "milwaukee": "milwaukee-bucks",
    "bucks": "milwaukee-bucks",
    "milwaukee-bucks": "milwaukee-bucks",
    "mil": "milwaukee-bucks",

    # Minnesota Timberwolves
    "minnesota": "minnesota-timberwolves",
    "timberwolves": "minnesota-timberwolves",
    "minnesota-timberwolves": "minnesota-timberwolves",
    "min": "minnesota-timberwolves",

    # New Orleans Pelicans
    "new-orleans": "new-orleans-pelicans",
    "pelicans": "new-orleans-pelicans",
    "new-orleans-pelicans": "new-orleans-pelicans",
    "nop": "new-orleans-pelicans",

    # New York Knicks
    "new-york": "new-york-knicks",
    "knicks": "new-york-knicks",
    "new-york-knicks": "new-york-knicks",
    "nyk": "new-york-knicks",

    # Oklahoma City Thunder
    "oklahoma-city": "oklahoma-city-thunder",
    "thunder": "oklahoma-city-thunder",
    "oklahoma-city-thunder": "oklahoma-city-thunder",
    "okc": "oklahoma-city-thunder",

    # Orlando Magic
    "orlando": "orlando-magic",
    "magic": "orlando-magic",
    "orlando-magic": "orlando-magic",
    "orl": "orlando-magic",

    # Philadelphia 76ers
    "philadelphia": "philadelphia-76ers",
    "76ers": "philadelphia-76ers",
    "philadelphia-76ers": "philadelphia-76ers",
    "phi": "philadelphia-76ers",

    # Phoenix Suns
    "phoenix": "phoenix-suns",
    "suns": "phoenix-suns",
    "phoenix-suns": "phoenix-suns",
    "phx": "phoenix-suns",

    # Portland Trail Blazers
    "portland": "portland-trail-blazers",
    "trail-blazers": "portland-trail-blazers",
    "portland-trail-blazers": "portland-trail-blazers",
    "por": "portland-trail-blazers",

    # Sacramento Kings
    "sacramento": "sacramento-kings",
    "kings": "sacramento-kings",
    "sacramento-kings": "sacramento-kings",
    "sac": "sacramento-kings",

    # San Antonio Spurs
    "san-antonio": "san-antonio-spurs",
    "spurs": "san-antonio-spurs",
    "san-antonio-spurs": "san-antonio-spurs",
    "sas": "san-antonio-spurs",

    # Toronto Raptors
    "toronto": "toronto-raptors",
    "raptors": "toronto-raptors",
    "toronto-raptors": "toronto-raptors",
    "tor": "toronto-raptors",

    # Utah Jazz
    "utah": "utah-jazz",
    "jazz": "utah-jazz",
    "utah-jazz": "utah-jazz",
    "uta": "utah-jazz",

    # Washington Wizards
    "washington": "washington-wizards",
    "wizards": "washington-wizards",
    "washington-wizards": "washington-wizards",
    "was": "washington-wizards",
}

LEAGUE_ALIASES = {
    "nba": NBA_ALIASES,
}

def normalize_team_name(name, league=None):
    name = name.strip().lower().replace(" ", "-")
    league_aliases = LEAGUE_ALIASES.get(league, {})
    normalized_name = league_aliases.get(name)
    return normalized_name if normalized_name is not None else name


