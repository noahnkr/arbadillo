LEAGUES = {'nba', 'mlb', 'nfl'}

SPORTS = {
    'nfl': 'football',
    'ncaaf': 'football',
    'mlb': 'baseball',
    'nba': 'basketball',
}

BOOKS = {'fanduel', 'caesars', 'draftkings', 'betmgm', 'betrivers', 'pointsbet', 'espnbet'}

REGIONS = {'us', 'uk', 'au', 'eu'}

BOOK_REGIONS = {
	'us': {'fanduel', 'caesars', 'draftkings', 'betmgm', 'betrivers', 'pointsbet', 'espnbet'},
	'uk': {},
	'au': {},
	'eu': {},
}

SCHEDULE_BASE_URL = {
    'mlb': 'https://www.espn.com/mlb/schedule'
}

BOOK_BASE_URL = {
	'fanduel': {},
	'caesars': {
        'mlb': 'https://sportsbook.caesars.com/us/il/bet/baseball?id=04f90892-3afa-4e84-acce-5b89f151063d'
	},
	'draftkings': {
        'mlb': 'https://sportsbook.draftkings.com/leagues/baseball/mlb'
	},
	'betmgm': {
        'mlb': 'https://sports.il.betmgm.com/en/sports/baseball-23/betting/usa-9/mlb-75',
	},
	'betrivers': {},
	'pointsbet': {},
	'espnbet': {},
}

MARKETS = {
	# Game Lines
	'moneyline', 'spread', 'total',
	# Alternate Game Lines
	'alt_spread', 'alt_total', 'team_total', 
	# Batting Props
	'batter_hits', 'batter_rbis', 'batter_total_bases', 'batter_runs', 
	'batter_singles', 'batter_doubles', 'batter_triples', 'batter_home_runs', 
	'batter_walks', 'batter_stolen_bases', 'batter_hits_runs_rbis'
	# Pitching Props
	'pitcher_outs', 'pitcher_strikeouts', 'pitcher_earned_runs', 'pitcher_walks',
	'pitcher_hits_allowed',
}

BOOK_MARKETS = {
	'fanduel': {},
	'caesars': {},
	'draftkings': {},
	'betmgm': {
	},
	'betrivers': {},
	'pointsbet': {},
	'espnbet': {},
}


TEAM_ACRONYMS = {
	# NBA
	'ATLANTA HAWKS': 'ATL', 'ATLANTA': 'ATL', 'HAWKS': 'ATL', 'ATL': 'ATL',
	'BOSTON CELTICS': 'BOS', 'BOSTON': 'BOS', 'CELTICS': 'BOS', 'BOS': 'BOS',
	'BROOKLYN NETS': 'BKN', 'BROOKLYN':'BKN', 'NETS': 'BKN', 'BKN': 'BKN',
	'CHARLOTTE HORNETS': 'CHA', 'CHARLOTTE': 'CHA', 'HORNETS': 'CHA', 'CHA': 'CHA',
	'CHICAGO BULLS': 'CHI', 'CHICAGO': 'CHI', 'BULLS': 'CHI', 'CHI': 'CHI',
	'CLEVELAND CAVALIERS': 'CLE', 'CLEVELAND': 'CLE', 'CAVALIERS': 'CLE', 'CLE': 'CLE',
	'DALLAS MAVERICKS': 'DAL', 'DALLAS': 'DAL', 'MAVERICKS': 'DAL', 'DAL': 'DAL',
	'DENVER NUGGETS': 'DEN', 'DENVER': 'DEN', 'NUGGETS': 'DEN', 'DEN': 'DEN',
	'DETROIT PISTONS': 'DET', 'DETROIT': 'DET', 'PISTONS': 'DET', 'DET': 'DET',
	'GOLDEN STATE WARRIORS': 'GSW', 'GOLDEN STATE': 'GSW', 'WARRIORS': 'GSW', 'GSW': 'GSW',
	'HOUSTON ROCKETS': 'HOU', 'HOUSTON': 'HOU', 'ROCKETS': 'HOU', 'HOU': 'HOU',
	'INDIANA PACERS': 'IND', 'INDIANA': 'IND', 'PACERS': 'IND', 'IND': 'IND',
	'LOS ANGELES CLIPPERS': 'LAC', 'LA': 'LAC', 'CLIPPERS': 'LAC', 'LAC': 'LAC',
	'LOS ANGELES LAKERS': 'LAL', 'LOS ANGELES': 'LAL', 'LAKERS': 'LAL', 'LAL': 'LAL',
	'MEMPHIS GRIZZLIES': 'MEM', 'MEMPHIS': 'MEM', 'GRIZZLIES': 'MEM', 'MEM': 'MEM',
	'MIAMI HEAT': 'MIA', 'MIAMI': 'MIA', 'HEAT': 'MIA', 'MIA': 'MIA',
	'MILWAUKEE BUCKS': 'MIL', 'MILWAUKEE': 'MIL', 'BUCKS': 'MIL', 'MIL': 'MIL',
	'MINNESOTA TIMBERWOLVES': 'MIN', 'MINNESOTA': 'MIN', 'TIMBERWOLVES': 'MIN', 'MIN': 'MIN',
	'NEW ORLEANS PELICANS': 'NOP', 'NEW ORLEANS': 'NOP', 'PELICANS': 'NOP', 'NOP': 'NOP',
	'NEW YORK KNICKS': 'NYK', 'NEW YORK': 'NYK', 'KNICKS': 'NYK', 'NYK': 'NYK',
	'OKLAHOMA CITY THUNDER': 'OKC', 'OKLAHOMA CITY': 'OKC', 'THUNDER': 'OKC', 'OKC': 'OKC',
	'ORLANDO MAGIC': 'ORL', 'ORLANDO': 'ORL', 'MAGIC': 'ORL', 'ORL': 'ORL',
	'PHILADELPHIA 76ERS': 'PHI', 'PHILADELPHIA': 'PHI', '76ERS': 'PHI', 'PHI': 'PHI',
	'PHOENIX SUNS': 'PHX', 'PHOENIX': 'PHX', 'SUNS': 'PHX', 'PHX': 'PHX',
	'PORTLAND TRAIL BLAZERS': 'POR', 'PORTLAND TRAILBLAZERS': 'POR', 'PORTLAND': 'POR', 'TRAIL BLAZERS': 'POR', 'TRAILBLAZERS': 'POR', 'POR': 'POR',
	'SACRAMENTO KINGS': 'SAC', 'SACRAMENTO': 'SAC', 'KINGS': 'SAC', 'SAC': 'SAC',
	'SAN ANTONIO SPURS': 'SAS', 'SAN ANTONIO': 'SAS', 'SPURS': 'SAS', 'SAS': 'SAS',
	'TORONTO RAPTORS': 'TOR', 'TORONTO': 'TOR', 'RAPTORS': 'TOR', 'TOR': 'TOR',
	'UTAH JAZZ': 'UTA', 'UTAH': 'UTA', 'JAZZ': 'UTA', 'UTA': 'UTA',
	'WASHINGTON WIZARDS': 'WAS', 'WASHINGTON': 'WAS', 'WIZARDS': 'WAS', 'WAS': 'WAS',

	# NFL
	'ARIZONA CARDINALS': 'ARI', 'ARIZONA': 'ARI', 'CARDINALS': 'ARI', 'ARI': 'ARI',
	'ATLANTA FALCONS': 'ATL', 'ATLANTA': 'ATL', 'FALCONS': 'ATL', 'ATL': 'ATL',
	'BALTIMORE RAVENS': 'BAL', 'BALTIMORE': 'BAL', 'RAVENS': 'BAL', 'BAL': 'BAL',
	'BUFFALO BILLS': 'BUF', 'BUFFALO': 'BUF', 'BILLS': 'BUF', 'BUF': 'BUF',
	'CAROLINA PANTHERS': 'CAR', 'CAROLINA': 'CAR', 'PANTHERS': 'CAR', 'CAR': 'CAR',
	'CHICAGO BEARS': 'CHI', 'CHICAGO': 'CHI', 'BEARS': 'CHI', 'CHI': 'CHI',
	'CINCINNATI BENGALS': 'CIN', 'CINCINNATI': 'CIN', 'BENGALS': 'CIN', 'CIN': 'CIN',
	'CLEVELAND BROWNS': 'CLE', 'CLEVELAND': 'CLE', 'BROWNS': 'CLE', 'CLE': 'CLE',
	'DALLAS COWBOYS': 'DAL', 'DALLAS': 'DAL', 'COWBOYS': 'DAL', 'DAL': 'DAL',
	'DENVER BRONCOS': 'DEN', 'DENVER': 'DEN', 'BRONCOS': 'DEN', 'DEN': 'DEN',
	'DETROIT LIONS': 'DET', 'DETROIT': 'DET', 'LIONS': 'DET', 'DET': 'DET',
	'GREEN BAY PACKERS': 'GB', 'GREEN BAY': 'GB', 'PACKERS': 'GB', 'GB': 'GB',
	'HOUSTON TEXANS': 'HOU', 'HOUSTON': 'HOU', 'TEXANS': 'HOU', 'HOU': 'HOU',
	'INDIANAPOLIS COLTS': 'IND', 'INDIANAPOLIS': 'IND', 'COLTS': 'IND', 'IND': 'IND',
	'JACKSONVILLE JAGUARS': 'JAX', 'JACKSONVILLE': 'JAX', 'JAGUARS': 'JAX', 'JAX': 'JAX',
	'KANSAS CITY CHIEFS': 'KC', 'KANSAS CITY': 'KC', 'CHIEFS': 'KC', 'KC': 'KC',
	'LOS ANGELES CHARGERS': 'LAC', 'LOS ANGELES C': 'LAC', 'CHARGERS': 'LAC', 'LAC': 'LAC',
	'LOS ANGELES RAMS': 'LAR', 'LOS ANGELES R': 'LAR', 'RAMS': 'LAR', 'LAR': 'LAR',
	'MIAMI DOLPHINS': 'MIA', 'MIAMI': 'MIA', 'DOLPHINS': 'MIA', 'MIA': 'MIA',
	'MINNESOTA VIKINGS': 'MIN', 'MINNESOTA': 'MIN', 'VIKINGS': 'MIN', 'MIN': 'MIN',
	'NEW ENGLAND PATRIOTS': 'NE', 'NEW ENGLAND': 'NE', 'PATRIOTS': 'NE', 'NE': 'NE',
	'NEW ORLEANS SAINTS': 'NO', 'NEW ORLEANS': 'NO', 'SAINTS': 'NO', 'NO': 'NO',
	'NEW YORK GIANTS': 'NYG', 'NEW YORK G': 'NYG', 'GIANTS': 'NYG', 'NYG': 'NYG',
	'NEW YORK JETS': 'NYJ', 'NEW YORK J': 'NYJ', 'JETS': 'NYJ', 'NYJ': 'NYJ',
	'LAS VEGAS RAIDERS': 'LV', 'LAS VEGAS': 'LV', 'RAIDERS': 'LV', 'LV': 'LV',
	'PHILADELPHIA EAGLES': 'PHI', 'PHILADELPHIA': 'PHI', 'EAGLES': 'PHI', 'PHI': 'PHI',
	'PITTSBURGH STEELERS': 'PIT', 'PITTSBURGH': 'PIT', 'STEELERS': 'PIT', 'PIT': 'PIT',
	'SAN FRANCISCO 49ERS': 'SF', 'SAN FRANCISCO': 'SF', '49ERS': 'SF', 'SF': 'SF',
	'SEATTLE SEAHAWKS': 'SEA', 'SEATTLE': 'SEA', 'SEAHAWKS': 'SEA', 'SEA': 'SEA',
	'TAMPA BAY BUCCANEERS': 'TB', 'TAMPA BAY': 'TB', 'BUCCANEERS': 'TB', 'TB': 'TB',
	'TENNESSEE TITANS': 'TEN', 'TENNESSEE': 'TEN', 'TITANS': 'TEN', 'TEN': 'TEN',
	'WASHINGTON FOOTBALL TEAM': 'WAS', 'WASHINGTON': 'WAS', 'WFT': 'WAS', 'WAS': 'WAS',

	# MLB
	'ARIZONA DIAMONDBACKS': 'ARI', 'ARIZONA': 'ARI', 'DIAMONDBACKS': 'ARI', 'ARI': 'ARI',
	'ATLANTA BRAVES': 'ATL', 'ATLANTA': 'ATL', 'BRAVES': 'ATL', 'ATL': 'ATL',
	'BALTIMORE ORIOLES': 'BAL', 'BALTIMORE': 'BAL', 'ORIOLES': 'BAL', 'BAL': 'BAL',
	'BOSTON RED SOX': 'BOS', 'BOSTON': 'BOS', 'RED SOX': 'BOS', 'BOS': 'BOS',
	'CHICAGO WHITE SOX': 'CWS', 'CHICAGO W': 'CWS', 'WHITE SOX': 'CWS', 'CWS': 'CWS',
	'CHICAGO CUBS': 'CHC', 'CHICAGO C': 'CHC', 'CUBS': 'CHC', 'CHC': 'CHC',
	'CINCINNATI REDS': 'CIN', 'CINCINNATI': 'CIN', 'REDS': 'CIN', 'CIN': 'CIN',
	'CLEVELAND GUARDIANS': 'CLE', 'CLEVELAND': 'CLE', 'GUARDIANS': 'CLE', 'CLE': 'CLE',
	'COLORADO ROCKIES': 'COL', 'COLORADO': 'COL', 'ROCKIES': 'COL', 'COL': 'COL',
	'DETROIT TIGERS': 'DET', 'DETROIT': 'DET', 'TIGERS': 'DET', 'DET': 'DET',
	'HOUSTON ASTROS': 'HOU', 'HOUSTON': 'HOU', 'ASTROS': 'HOU', 'HOU': 'HOU',
	'KANSAS CITY ROYALS': 'KC', 'KANSAS CITY': 'KC', 'ROYALS': 'KC', 'KC': 'KC',
	'LOS ANGELES ANGELS': 'LAA', 'LA ANGELS': 'LAA', 'ANGELS': 'LAA', 'LAA': 'LAA',
	'LOS ANGELES DODGERS': 'LAD', 'LA DODGERS': 'LAD', 'DODGERS': 'LAD', 'LAD': 'LAD',
	'MIAMI MARLINS': 'MIA', 'MIAMI': 'MIA', 'MARLINS': 'MIA', 'MIA': 'MIA',
	'MILWAUKEE BREWERS': 'MIL', 'MILWAUKEE': 'MIL', 'BREWERS': 'MIL', 'MIL': 'MIL',
	'MINNESOTA TWINS': 'MIN', 'MINNESOTA': 'MIN', 'TWINS': 'MIN', 'MIN': 'MIN',
	'NEW YORK METS': 'NYM', 'NEW YORK M': 'NYM', 'METS': 'NYM', 'NYM': 'NYM',
	'NEW YORK YANKEES': 'NYY', 'NEW YORK Y': 'NYY', 'YANKEES': 'NYY', 'NYY': 'NYY',
	'OAKLAND ATHLETICS': 'OAK', 'OAKLAND': 'OAK', 'ATHLETICS': 'OAK', 'OAK': 'OAK',
	'PHILADELPHIA PHILLIES': 'PHI', 'PHILADELPHIA': 'PHI', 'PHILLIES': 'PHI', 'PHI': 'PHI',
	'PITTSBURGH PIRATES': 'PIT', 'PITTSBURGH': 'PIT', 'PIRATES': 'PIT', 'PIT': 'PIT',
	'SAN DIEGO PADRES': 'SD', 'SAN DIEGO': 'SD', 'PADRES': 'SD', 'SD': 'SD',
	'SAN FRANCISCO GIANTS': 'SF', 'SAN FRANCISCO': 'SF', 'GIANTS': 'SF', 'SF': 'SF',
	'SEATTLE MARINERS': 'SEA', 'SEATTLE': 'SEA', 'MARINERS': 'SEA', 'SEA': 'SEA',
	'ST. LOUIS CARDINALS': 'STL', 'ST LOUIS': 'STL', 'ST. LOUIS': 'STL', 'CARDINALS': 'STL', 'STL': 'STL',
	'TAMPA BAY RAYS': 'TB', 'TAMPA BAY': 'TB', 'RAYS': 'TB', 'TB': 'TB',
	'TEXAS RANGERS': 'TEX', 'TEXAS': 'TEX', 'RANGERS': 'TEX', 'TEX': 'TEX',
	'TORONTO BLUE JAYS': 'TOR', 'TORONTO': 'TOR', 'BLUE JAYS': 'TOR', 'TOR': 'TOR',
	'WASHINGTON NATIONALS': 'WAS', 'WASHINGTON': 'WAS', 'NATIONALS': 'WAS', 'WAS': 'WAS',
}