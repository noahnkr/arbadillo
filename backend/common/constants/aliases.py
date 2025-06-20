import re
from common.utils.strings import clean_str

# ---------- Teams ----------

NFL_ALIASES = {
    'arizona-cardinals': ['ARI', 'Arizona', 'Cardinals', 'Arizona Cardinals', 'ARI Cardinals'],
    'atlanta-falcons': ['ATL', 'Atlanta', 'Falcons', 'Atlanta Falcons', 'ATL Falcons'],
    'baltimore-ravens': ['BAL', 'Baltimore', 'Ravens', 'Baltimore Ravens', 'BAL Ravens'],
    'buffalo-bills': ['BUF', 'Buffalo', 'Bills', 'Buffalo Bills', 'BUF Bills'],
    'carolina-panthers': ['CAR', 'Carolina', 'Panthers', 'Carolina Panthers', 'CAR Panthers'],
    'chicago-bears': ['CHI', 'Chicago', 'Bears', 'Chicago Bears', 'CHI Bears'],
    'cincinnati-bengals': ['CIN', 'Cincinnati', 'Bengals', 'Cincinnati Bengals', 'CIN Bengals'],
    'cleveland-browns': ['CLE', 'Cleveland', 'Browns', 'Cleveland Browns', 'CLE Browns'],
    'dallas-cowboys': ['DAL', 'Dallas', 'Cowboys', 'Dallas Cowboys', 'DAL Cowboys'],
    'denver-broncos': ['DEN', 'Denver', 'Broncos', 'Denver Broncos', 'DEN Broncos'],
    'detroit-lions': ['DET', 'Detroit', 'Lions', 'Detroit Lions', 'DET Lions'],
    'green-bay-packers': ['GB', 'Green Bay', 'Packers', 'Green Bay Packers', 'GB Packers'],
    'houston-texans': ['HOU', 'Houston', 'Texans', 'Houston Texans', 'HOU Texans'],
    'indianapolis-colts': ['IND', 'Indianapolis', 'Colts', 'Indianapolis Colts', 'IND Colts'],
    'jacksonville-jaguars': ['JAX', 'Jacksonville', 'Jaguars', 'Jacksonville Jaguars', 'JAX Jaguars'],
    'kansas-city-chiefs': ['KC', 'Kansas City', 'Chiefs', 'Kansas City Chiefs', 'KC Chiefs'],
    'las-vegas-raiders': ['LV', 'Las Vegas', 'Raiders', 'Las Vegas Raiders', 'LV Raiders'],
    'los-angeles-chargers': ['LAC', 'LA Chargers', 'Chargers', 'Los Angeles Chargers', 'LA Chargers'],
    'los-angeles-rams': ['LAR', 'LA Rams', 'Rams', 'Los Angeles Rams', 'LA Rams'],
    'miami-dolphins': ['MIA', 'Miami', 'Dolphins', 'Miami Dolphins', 'MIA Dolphins'],
    'minnesota-vikings': ['MIN', 'Minnesota', 'Vikings', 'Minnesota Vikings', 'MIN Vikings'],
    'new-england-patriots': ['NE', 'New England', 'Patriots', 'New England Patriots', 'NE Patriots'],
    'new-orleans-saints': ['NO', 'New Orleans', 'Saints', 'New Orleans Saints', 'NO Saints'],
    'new-york-giants': ['NYG', 'NY Giants', 'Giants', 'New York Giants', 'NY Giants'],
    'new-york-jets': ['NYJ', 'NY Jets', 'Jets', 'New York Jets', 'NY Jets'],
    'philadelphia-eagles': ['PHI', 'Philadelphia', 'Eagles', 'Philadelphia Eagles', 'PHI Eagles'],
    'pittsburgh-steelers': ['PIT', 'Pittsburgh', 'Steelers', 'Pittsburgh Steelers', 'PIT Steelers'],
    'san-francisco-49ers': ['SF', 'San Francisco', '49ers', 'San Francisco 49ers', 'SF 49ers'],
    'seattle-seahawks': ['SEA', 'Seattle', 'Seahawks', 'Seattle Seahawks', 'SEA Seahawks'],
    'tampa-bay-buccaneers': ['TB', 'Tampa Bay', 'Buccaneers', 'Tampa Bay Buccaneers', 'TB Buccaneers'],
    'tennessee-titans': ['TEN', 'Tennessee', 'Titans', 'Tennessee Titans', 'TEN Titans'],
    'washington-commanders': ['WAS', 'Washington', 'Commanders', 'Washington Commanders', 'WAS Commanders'],
}

NBA_ALIASES = { 
    'atlanta-hawks': ['ATL', 'Atlanta', 'Hawks', 'Atlanta Hawks', 'ATL Hawks'],
    'boston-celtics': ['BOS', 'Boston', 'Celtics', 'Boston Celtics', 'BOS Celtics'],
    'brooklyn-nets': ['BKN', 'Brooklyn', 'Nets', 'Brooklyn Nets', 'BKN Nets'],
    'charlotte-hornets': ['CHA', 'Charlotte', 'Hornets', 'Charlotte Hornets', 'CHA Hornets'],
    'chicago-bulls': ['CHI', 'Chicago', 'Bulls', 'Chicago Bulls', 'CHI Bulls'],
    'cleveland-cavaliers': ['CLE', 'Cleveland', 'Cavaliers', 'Cleveland Cavaliers', 'CLE Cavaliers'],
    'dallas-mavericks': ['DAL', 'Dallas', 'Mavericks', 'Dallas Mavericks', 'DAL Mavericks'],
    'denver-nuggets': ['DEN', 'Denver', 'Nuggets', 'Denver Nuggets', 'DEN Nuggets'],
    'detroit-pistons': ['DET', 'Detroit', 'Pistons', 'Detroit Pistons', 'DET Pistons'],
    'golden-state-warriors': ['GSW', 'Golden State', 'Warriors', 'Golden State Warriors', 'GS Warriors'],
    'houston-rockets': ['HOU', 'Houston', 'Rockets', 'Houston Rockets', 'HOU Rockets'],
    'indiana-pacers': ['IND', 'Indiana', 'Pacers', 'Indiana Pacers', 'IND Pacers'],
    'los-angeles-clippers': ['LAC', 'LA Clippers', 'Clippers', 'Los Angeles Clippers', 'LA Clippers'],
    'los-angeles-lakers': ['LAL', 'LA Lakers', 'Lakers', 'Los Angeles Lakers', 'LA Lakers'],
    'memphis-grizzlies': ['MEM', 'Memphis', 'Grizzlies', 'Memphis Grizzlies', 'MEM Grizzlies'],
    'miami-heat': ['MIA', 'Miami', 'Heat', 'Miami Heat', 'MIA Heat'],
    'milwaukee-bucks': ['MIL', 'Milwaukee', 'Bucks', 'Milwaukee Bucks', 'MIL Bucks'],
    'minnesota-timberwolves': ['MIN', 'Minnesota', 'Timberwolves', 'Minnesota Timberwolves', 'MIN Timberwolves'],
    'new-orleans-pelicans': ['NOP', 'New Orleans', 'Pelicans', 'New Orleans Pelicans', 'NO Pelicans'],
    'new-york-knicks': ['NYK', 'NY Knicks', 'Knicks', 'New York Knicks', 'NY Knicks'],
    'oklahoma-city-thunder': ['OKC', 'Oklahoma City', 'Thunder', 'Oklahoma City Thunder', 'OKC Thunder'],
    'orlando-magic': ['ORL', 'Orlando', 'Magic', 'Orlando Magic', 'ORL Magic'],
    'philadelphia-76ers': ['PHI', 'Philadelphia', '76ers', 'Philadelphia 76ers', 'PHI 76ers'],
    'phoenix-suns': ['PHX', 'Phoenix', 'Suns', 'Phoenix Suns', 'PHX Suns'],
    'portland-trail-blazers': ['POR', 'Portland', 'Trail Blazers', 'Portland Trail Blazers', 'POR Trail Blazers'],
    'sacramento-kings': ['SAC', 'Sacramento', 'Kings', 'Sacramento Kings', 'SAC Kings'],
    'san-antonio-spurs': ['SAS', 'San Antonio', 'Spurs', 'San Antonio Spurs', 'SA Spurs'],
    'toronto-raptors': ['TOR', 'Toronto', 'Raptors', 'Toronto Raptors', 'TOR Raptors'],
    'utah-jazz': ['UTA', 'Utah', 'Jazz', 'Utah Jazz', 'UTA Jazz'],
    'washington-wizards': ['WAS', 'Washington', 'Wizards', 'Washington Wizards', 'WAS Wizards'],
}

MLB_ALIASES = {
    'arizona-diamondbacks': ['ARI', 'Arizona', 'Diamondbacks', 'Arizona Diamondbacks', 'ARI Diamondbacks'],
    'atlanta-braves': ['ATL', 'Atlanta', 'Braves', 'Atlanta Braves', 'ATL Braves'],
    'baltimore-orioles': ['BAL', 'Baltimore', 'Orioles', 'Baltimore Orioles', 'BAL Orioles'],
    'boston-red-sox': ['BOS', 'Boston', 'Red Sox', 'Boston Red Sox', 'BOS Red Sox'],
    'chicago-cubs': ['CHC', 'Chicago Cubs', 'Cubs', 'CHI Cubs'],
    'chicago-white-sox': ['CWS', 'CHW', 'Chicago White Sox', 'White Sox', 'Chi White Sox', 'CHI White Sox'],
    'cincinnati-reds': ['CIN', 'Cincinnati', 'Reds', 'Cincinnati Reds', 'CIN Reds'],
    'cleveland-guardians': ['CLE', 'Cleveland', 'Guardians', 'Cleveland Guardians', 'CLE Guardians'],
    'colorado-rockies': ['COL', 'Colorado', 'Rockies', 'Colorado Rockies', 'COL Rockies'],
    'detroit-tigers': ['DET', 'Detroit', 'Tigers', 'Detroit Tigers', 'DET Tigers'],
    'houston-astros': ['HOU', 'Houston', 'Astros', 'Houston Astros', 'HOU Astros'],
    'kansas-city-royals': ['KC', 'Kansas City', 'Royals', 'Kansas City Royals', 'KC Royals'],
    'los-angeles-angels': ['LAA', 'LA Angels', 'Angels', 'Los Angeles Angels', 'LA Angels'],
    'los-angeles-dodgers': ['LAD', 'LA Dodgers', 'Dodgers', 'Los Angeles Dodgers', 'LA Dodgers'],
    'miami-marlins': ['MIA', 'Miami', 'Marlins', 'Miami Marlins', 'Florida Marlins', 'MIA Marlins'],
    'milwaukee-brewers': ['MIL', 'Milwaukee', 'Brewers', 'Milwaukee Brewers', 'MIL Brewers'],
    'minnesota-twins': ['MIN', 'Minnesota', 'Twins', 'Minnesota Twins', 'MIN Twins'],
    'new-york-mets': ['NYM', 'NY Mets', 'Mets', 'New York Mets', 'NY Mets'],
    'new-york-yankees': ['NYY', 'NY Yankees', 'Yankees', 'New York Yankees', 'NY Yankees'],
    'oakland-athletics': ['OAK','ATH', 'Oakland', 'Athletics', 'Oakland A\'s', 'A\'s', 'Oakland Athletics', 'OAK Athletics'],
    'philadelphia-phillies': ['PHI', 'Philadelphia', 'Phillies', 'Philadelphia Phillies', 'PHI Phillies'],
    'pittsburgh-pirates': ['PIT', 'Pittsburgh', 'Pirates', 'Pittsburgh Pirates', 'PIT Pirates'],
    'san-diego-padres': ['SD', 'San Diego', 'Padres', 'San Diego Padres', 'SD Padres'],
    'san-francisco-giants': ['SF', 'San Francisco', 'Giants', 'San Francisco Giants', 'SF Giants'],
    'seattle-mariners': ['SEA', 'Seattle', 'Mariners', 'Seattle Mariners', 'SEA Mariners'],
    'st-louis-cardinals': ['STL', 'St. Louis', 'St Louis', 'Cardinals', 'St. Louis Cardinals', 'St Louis Cardinals', 'STL Cardinals'],
    'tampa-bay-rays': ['TB', 'Tampa Bay', 'Rays', 'Tampa Bay Rays', 'Tampa Rays', 'TB Rays'],
    'texas-rangers': ['TEX', 'Texas', 'Rangers', 'Texas Rangers', 'TEX Rangers'],
    'toronto-blue-jays': ['TOR', 'Toronto', 'Blue Jays', 'Toronto Blue Jays', 'TOR Blue Jays'],
    'washington-nationals': ['WSH', 'WAS', 'Washington', 'Nationals', 'Washington Nationals', 'Nats', 'WAS Nationals']
}

NHL_ALIASES = {
    'anaheim-ducks': ['ANA', 'Anaheim', 'Ducks', 'Anaheim Ducks', 'ANA Ducks'],
    'arizona-coyotes': ['ARI', 'Arizona', 'Coyotes', 'Arizona Coyotes', 'ARI Coyotes'],
    'boston-bruins': ['BOS', 'Boston', 'Bruins', 'Boston Bruins', 'BOS Bruins'],
    'buffalo-sabres': ['BUF', 'Buffalo', 'Sabres', 'Buffalo Sabres', 'BUF Sabres'],
    'calgary-flames': ['CGY', 'Calgary', 'Flames', 'Calgary Flames', 'CGY Flames'],
    'carolina-hurricanes': ['CAR', 'Carolina', 'Hurricanes', 'Carolina Hurricanes', 'Canes', 'CAR Hurricanes'],
    'chicago-blackhawks': ['CHI', 'Chicago', 'Blackhawks', 'Chicago Blackhawks', 'CHI Blackhawks'],
    'colorado-avalanche': ['COL', 'Colorado', 'Avalanche', 'Colorado Avalanche', 'COL Avalanche'],
    'columbus-blue-jackets': ['CBJ', 'Columbus', 'Blue Jackets', 'Columbus Blue Jackets', 'CBJ Blue Jackets'],
    'dallas-stars': ['DAL', 'Dallas', 'Stars', 'Dallas Stars', 'DAL Stars'],
    'detroit-red-wings': ['DET', 'Detroit', 'Red Wings', 'Detroit Red Wings', 'DET Red Wings'],
    'edmonton-oilers': ['EDM', 'Edmonton', 'Oilers', 'Edmonton Oilers', 'EDM Oilers'],
    'florida-panthers': ['FLA', 'Florida', 'Panthers', 'Florida Panthers', 'FLA Panthers'],
    'los-angeles-kings': ['LAK', 'LA Kings', 'Kings', 'Los Angeles Kings', 'LA Kings'],
    'minnesota-wild': ['MIN', 'Minnesota', 'Wild', 'Minnesota Wild', 'MIN Wild'],
    'montreal-canadiens': ['MTL', 'Montreal', 'Canadiens', 'Montreal Canadiens', 'Habs', 'MTL Canadiens'],
    'nashville-predators': ['NSH', 'Nashville', 'Predators', 'Nashville Predators', 'Preds', 'NSH Predators'],
    'new-jersey-devils': ['NJD', 'New Jersey', 'Devils', 'New Jersey Devils', 'NJD Devils'],
    'new-york-islanders': ['NYI', 'NY Islanders', 'Islanders', 'New York Islanders', 'NY Islanders'],
    'new-york-rangers': ['NYR', 'NY Rangers', 'Rangers', 'New York Rangers', 'NY Rangers'],
    'ottawa-senators': ['OTT', 'Ottawa', 'Senators', 'Ottawa Senators', 'Sens', 'OTT Senators'],
    'philadelphia-flyers': ['PHI', 'Philadelphia', 'Flyers', 'Philadelphia Flyers', 'PHI Flyers'],
    'pittsburgh-penguins': ['PIT', 'Pittsburgh', 'Penguins', 'Pittsburgh Penguins', 'Pens', 'PIT Penguins'],
    'san-jose-sharks': ['SJS', 'San Jose', 'Sharks', 'San Jose Sharks', 'SJ Sharks'],
    'seattle-kraken': ['SEA', 'Seattle', 'Kraken', 'Seattle Kraken', 'SEA Kraken'],
    'st-louis-blues': ['STL', 'St. Louis', 'Blues', 'St. Louis Blues', 'STL Blues'],
    'tampa-bay-lightning': ['TBL', 'Tampa Bay', 'Lightning', 'Tampa Bay Lightning', 'Bolts', 'TB Lightning'],
    'toronto-maple-leafs': ['TOR', 'Toronto', 'Maple Leafs', 'Toronto Maple Leafs', 'Leafs', 'TOR Maple Leafs'],
    'vancouver-canucks': ['VAN', 'Vancouver', 'Canucks', 'Vancouver Canucks', 'VAN Canucks'],
    'vegas-golden-knights': ['VGK', 'Vegas', 'Golden Knights', 'Vegas Golden Knights', 'Knights', 'VGK Golden Knights'],
    'washington-capitals': ['WSH', 'Washington', 'Capitals', 'Washington Capitals', 'Caps', 'WSH Capitals'],
    'winnipeg-jets': ['WPG', 'Winnipeg', 'Jets', 'Winnipeg Jets', 'WPG Jets'],
}

MLS_ALIASES = {
    'atlanta-united': ['ATL', 'Atlanta', 'Atlanta United', 'Atlanta United FC', 'United'],
    'austin-fc': ['ATX', 'Austin', 'Austin FC'],
    'cf-montreal': ['MTL', 'Montreal', 'CF Montréal', 'Club de Foot Montreal', 'CF Montreal'],
    'charlotte-fc': ['CLT', 'Charlotte', 'Charlotte FC'],
    'chicago-fire': ['CHI', 'Chicago', 'Chicago Fire', 'Chicago Fire FC', 'Fire'],
    'fc-cincinnati': ['CIN', 'Cincinnati', 'FC Cincinnati', 'FCC'],
    'colorado-rapids': ['COL', 'Colorado', 'Colorado Rapids', 'Rapids'],
    'columbus-crew': ['CLB', 'Columbus', 'Columbus Crew', 'Columbus Crew SC', 'The Crew'],
    'dc-united': ['DC', 'D.C. United', 'DC United', 'D.C.', 'Washington DC'],
    'fc-dallas': ['DAL', 'Dallas', 'FC Dallas'],
    'houston-dynamo': ['HOU', 'Houston', 'Houston Dynamo', 'Houston Dynamo FC', 'Dynamo'],
    'inter-miami': ['MIA', 'Miami', 'Inter Miami', 'Inter Miami CF', 'Club Internacional de Fútbol Miami'],
    'la-galaxy': ['LA', 'LA Galaxy', 'Los Angeles Galaxy', 'Galaxy'],
    'los-angeles-fc': ['LAFC', 'LA FC', 'Los Angeles FC', 'LA Football Club', 'Los Angeles'],
    'minnesota-united': ['MIN', 'Minnesota', 'Minnesota United', 'Minnesota United FC', 'Loons'],
    'nashville-sc': ['NSH', 'Nashville', 'Nashville SC', 'Nashville Soccer Club'],
    'ne-revolution': ['NE', 'New England', 'New England Revolution', 'Revs'],
    'new-york-city-fc': ['NYC', 'NYCFC', 'New York City FC', 'New York City', 'City'],
    'new-york-red-bulls': ['NY', 'NYRB', 'New York Red Bulls', 'Red Bulls'],
    'orlando-city': ['ORL', 'Orlando', 'Orlando City', 'Orlando City SC'],
    'philadelphia-union': ['PHI', 'Philadelphia', 'Philadelphia Union', 'Union'],
    'portland-timbers': ['POR', 'Portland', 'Portland Timbers', 'Timbers'],
    'real-salt-lake': ['RSL', 'Salt Lake', 'Real Salt Lake', 'RSL FC'],
    'san-jose-earthquakes': ['SJ', 'San Jose', 'San Jose Earthquakes', 'Earthquakes', 'Quakes'],
    'seattle-sounders': ['SEA', 'Seattle', 'Seattle Sounders', 'Seattle Sounders FC', 'Sounders'],
    'sporting-kansas-city': ['SKC', 'Kansas City', 'Sporting KC', 'Sporting Kansas City', 'Sporting'],
    'st-louis-city': ['STL', 'St. Louis', 'St. Louis City', 'St. Louis City SC', 'CITY SC'],
    'toronto-fc': ['TOR', 'Toronto', 'Toronto FC', 'TFC'],
    'vancouver-whitecaps': ['VAN', 'Vancouver', 'Vancouver Whitecaps', 'Whitecaps', 'Whitecaps FC'],
}

NCAA_ALIASES = {
    # Big Ten Conference
    'illinois-fighting-illini': ['ILL', 'Illinois', 'Fighting Illini'],
    'indiana-hoosiers': ['IND', 'Indiana', 'Hoosiers'],
    'iowa-hawkeyes': ['IOWA', 'Iowa', 'Hawkeyes'],
    'maryland-terrapins': ['MD', 'Maryland', 'Terrapins', 'Terps'],
    'michigan-wolverines': ['MICH', 'Michigan', 'Wolverines'],
    'michigan-state-spartans': ['MSU', 'Michigan State', 'Spartans'],
    'minnesota-golden-gophers': ['MINN', 'Minnesota', 'Golden Gophers', 'Gophers'],
    'nebraska-cornhuskers': ['NEB', 'Nebraska', 'Cornhuskers', 'Huskers'],
    'northwestern-wildcats': ['NU', 'Northwestern', 'Wildcats'],
    'ohio-state-buckeyes': ['OSU', 'Ohio State', 'Buckeyes'],
    'oregon-ducks': ['ORE', 'Oregon', 'Ducks'],
    'penn-state-nittany-lions': ['PSU', 'Penn State', 'Nittany Lions'],
    'purdue-boilermakers': ['PUR', 'Purdue', 'Boilermakers'],
    'rutgers-scarlet-knights': ['RUT', 'Rutgers', 'Scarlet Knights'],
    'ucla-bruins': ['UCLA', 'UCLA', 'Bruins'],
    'usc-trojans': ['USC', 'USC', 'Trojans'],
    'washington-huskies': ['UW', 'Washington', 'Huskies'],
    'wisconsin-badgers': ['WIS', 'Wisconsin', 'Badgers'],

    # Big 12 Conference
    'arizona-wildcats': ['ARIZ', 'Arizona', 'Wildcats'],
    'arizona-state-sun-devils': ['ASU', 'Arizona State', 'Sun Devils'],
    'baylor-bears': ['BU', 'Baylor', 'Bears'],
    'byu-cougars': ['BYU', 'BYU', 'Cougars'],
    'cincinnati-bearcats': ['CIN', 'Cincinnati', 'Bearcats'],
    'colorado-buffaloes': ['COLO', 'Colorado', 'Buffaloes', 'Buffs'],
    'houston-cougars': ['UH', 'Houston', 'Cougars'],
    'iowa-state-cyclones': ['ISU', 'Iowa State', 'Cyclones'],
    'kansas-jayhawks': ['KU', 'Kansas', 'Jayhawks'],
    'kansas-state-wildcats': ['KSU', 'Kansas State', 'Wildcats'],
    'oklahoma-state-cowboys': ['OKST', 'Oklahoma State', 'Cowboys', 'Pokes'],
    'tcu-horned-frogs': ['TCU', 'TCU', 'Horned Frogs'],
    'texas-tech-red-raiders': ['TTU', 'Texas Tech', 'Red Raiders'],
    'ucf-knights': ['UCF', 'UCF', 'Knights'],
    'utah-utes': ['UTAH', 'Utah', 'Utes'],
    'west-virginia-mountaineers': ['WVU', 'West Virginia', 'Mountaineers'],

    # Southeastern Conference (SEC)
    'alabama-crimson-tide': ['ALA', 'Alabama', 'Crimson Tide'],
    'arkansas-razorbacks': ['ARK', 'Arkansas', 'Razorbacks', 'Hogs'],
    'auburn-tigers': ['AUB', 'Auburn', 'Tigers'],
    'florida-gators': ['UF', 'Florida', 'Gators'],
    'georgia-bulldogs': ['UGA', 'Georgia', 'Bulldogs', 'Dawgs'],
    'kentucky-wildcats': ['UK', 'Kentucky', 'Wildcats'],
    'lsu-tigers': ['LSU', 'LSU', 'Tigers'],
    'mississippi-rebels': ['MISS', 'Ole Miss', 'Rebels'],
    'mississippi-state-bulldogs': ['MSST', 'Mississippi State', 'Bulldogs'],
    'missouri-tigers': ['MIZZ', 'Missouri', 'Tigers'],
    'oklahoma-sooners': ['OU', 'Oklahoma', 'Sooners'],
    'south-carolina-gamecocks': ['SCAR', 'South Carolina', 'Gamecocks'],
    'tennessee-volunteers': ['TENN', 'Tennessee', 'Volunteers', 'Vols'],
    'texas-longhorns': ['TEX', 'Texas', 'Longhorns'],
    'texas-am-aggies': ['TAMU', 'Texas A&M', 'Aggies'],
    'vanderbilt-commodores': ['VAN', 'Vanderbilt', 'Commodores', 'Dores'],

    # Atlantic Coast Conference (ACC)
    'boston-college-eagles': ['BC', 'Boston College', 'Eagles'],
    'california-golden-bears': ['CAL', 'California', 'Golden Bears', 'Cal'],
    'clemson-tigers': ['CLEM', 'Clemson', 'Tigers'],
    'duke-blue-devils': ['DUKE', 'Duke', 'Blue Devils'],
    'florida-state-seminoles': ['FSU', 'Florida State', 'Seminoles', 'Noles'],
    'georgia-tech-yellow-jackets': ['GT', 'Georgia Tech', 'Yellow Jackets'],
    'louisville-cardinals': ['LOU', 'Louisville', 'Cardinals'],
    'miami-hurricanes': ['MIA', 'Miami', 'Hurricanes', 'Canes'],
    'north-carolina-tar-heels': ['UNC', 'North Carolina', 'Tar Heels'],
    'nc-state-wolfpack': ['NCST', 'NC State', 'Wolfpack'],
    'notre-dame-fighting-irish': ['ND', 'Notre Dame', 'Fighting Irish'],
    'pittsburgh-panthers': ['PITT', 'Pittsburgh', 'Panthers'],
    'smu-mustangs': ['SMU', 'SMU', 'Mustangs'],
    'stanford-cardinal': ['STAN', 'Stanford', 'Cardinal'],
    'syracuse-orange': ['SYR', 'Syracuse', 'Orange'],
    'virginia-cavaliers': ['UVA', 'Virginia', 'Cavaliers', 'Wahoos'],
    'virginia-tech-hokies': ['VT', 'Virginia Tech', 'Hokies'],
    'wake-forest-demon-deacons': ['WF', 'Wake Forest', 'Demon Deacons', 'Deacs'],

    # Pac-12 Conference (2025 Members)
    'oregon-state-beavers': ['OSU', 'Oregon State', 'Beavers'],
    'washington-state-cougars': ['WSU', 'Washington State', 'Cougars'],
}

TEAM_ALIASES = {
    'nfl': NFL_ALIASES, 
    'nba': NBA_ALIASES,
    'mlb': MLB_ALIASES,
    'mls': MLS_ALIASES,
    'nhl': NHL_ALIASES,
    'ncaaf': NCAA_ALIASES,
    'ncaab': NCAA_ALIASES,
    'ncaaw': NCAA_ALIASES,
}

REVERSE_TEAM_LOOKUP = {}
for league, league_aliases in TEAM_ALIASES.items():
    for standard, aliases in league_aliases.items():
        REVERSE_TEAM_LOOKUP[(league, standard)] = standard
        for alias in aliases:
            REVERSE_TEAM_LOOKUP[(league, clean_str(alias))] = standard

# ---------- Markets ----------

FOOTBALL_MARKET_ALIASES = {}

BASKETBALL_MARKET_ALIASES = {
    'player_points': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['points', 'player points', 'total points', 'points milestones']
    },
    'player_rebounds': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['rebounds', 'player rebounds', 'total rebounds', 'rebounds milestones']
    },
    'player_assists': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['assists', 'player assists', 'total assists', 'assists milestones']
    },
    'player_threes': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['threes', '3-point field goals', '3-pointers', 'player threes', 'total 3-point field goals', 'threes milestones']
    },
    'player_steals': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['steals', 'player steals', 'total steals', 'steals milestones']
    },
    'player_blocks': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['blocks', 'player blocks', 'total blocks', 'blocks milestones']
    },
    'player_turnovers': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['turnovers', 'player turnovers', 'total turnovers', 'turnovers milestones']
    },
    'player_points_rebounds_assists': {
        'type': 'over_under',
        'scope': 'player',
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
        'scope': 'player',
        'aliases': [
            'points + rebounds', 'pts + reb',
            'points and rebounds', 'total points and rebounds',
            'player points and rebounds',
            'points + rebounds milestones'
        ]
    },
    'player_points_assists': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': [
            'points + assists', 'pts + ast',
            'points and assists', 'total points and assists',
            'player points and assists',
            'points + assists milestones'
        ]
    },
    'player_rebounds_assists': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': [
            'rebounds + assists', 'reb + ast',
            'rebounds and assists', 'total rebounds and assists',
            'player rebounds and assists',
            'rebounds + assists milestones'
        ]
    },
    'player_steals_blocks': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': [
            'steals + blocks', 'stl + blk',
            'steals and blocks', 'total steals and blocks',
            'player steals and blocks',
            'steals + blocks milestones'
        ]
    },
    'player_double_double': {
        'type': 'yes_no',
        'scope': 'player',
        'aliases': ['double double', 'to record a double double']
    },
    'player_triple_double': {
        'type': 'yes_no',
        'scope': 'player',
        'aliases': ['triple double', 'to record a triple double']
    },
    'team_points': {
        'type': 'over_under',
        'scope': 'team',
        'aliases': ['team points', 'team total points']
    },
    'team_threes': {
        'type': 'over_under',
        'scope': 'team',
        'aliases': ['team threes', 'team 3-pointers', 'team total 3-pointers made']
    },
    'team_steals': {
        'type': 'over_under',
        'scope': 'team',
        'aliases': ['team steals', 'team total steals']
    },
    'team_blocks': {
        'type': 'over_under',
        'scope': 'team',
        'aliases': ['team blocks', 'team total blocks']
    }
}

BASEBALL_MARKET_ALIASES = {
    'batter_home_runs': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['home runs', 'batter home runs', 'player home runs', 'total home runs', 'total home runs hit', 'home runs milestones']
    },
    'batter_hits': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['hits', 'batter hits', 'player hits', 'total hits', 'hits milestones']
    },
    'batter_total_bases': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['total bases', 'batter total bases', 'player total bases', 'total bases milestones']
    },
    'batter_rbis': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['rbi', 'rbis', 'batter rbis', 'player rbis', 'total rbis', 'rbis milestones']
    },
    'batter_singles': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['singles', 'batter singles', 'player singles', 'total singles hit', 'singles milestones']
    },
    'batter_runs_scored': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['runs', 'runs scored', 'batter runs', 'player runs', 'total runs scored', 'runs milestones']
    },
    'batter_hits_runs_rbis': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['hits + runs + rbis', 'batter hits + runs + rbis', 'player hits + runs + rbis', 'total hits + runs + rbis', 'hits + runs + rbis milestones']
    },
    'batter_stolen_bases': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['stolen bases', 'batter stolen bases', 'player stolen bases', 'total stolen bases', 'stolen bases milestones']
    },
    'pitcher_strikeouts': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['strikeouts', 'pitcher strikeouts', 'player strikeouts', 'total strikeouts', 'strikeouts milestones']
    },
    'pitcher_walks': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['walks', 'walks allowed', 'pitcher walks', 'player walks', 'total walks allowed', 'walks milestones']
    },
    'pitcher_hits_allowed': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['hits allowed', 'pitcher hits allowed', 'player hits allowed', 'total hits allowed', 'hits allowed milestones']
    },
    'pitcher_outs': {
        'type': 'over_under',
        'scope': 'player',
        'aliases': ['outs', 'outs recorded', 'pitcher outs', 'player outs', 'total outs recorded', 'outs milestones']
    }
}


SOCCER_MARKET_ALIASES = {}

HOCKEY_MARKET_ALIASES = {}

PRIMARY_MARKET_ALIASES = {
    # Standard & Alternative Markets
    'moneyline': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['moneyline', 'ml', 'win', 'to win', 'team to win', 'match winner', 'winner', 'h2h']
    },
    'spread': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['spread', 'point spread', 'spread betting', 'run line', 'puck line', 'handicap', 'line', 'ats']
    },
    'total': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['total', 'game total', 'total points', 'o/u', 'over/under', 'over', 'under', 'match total', 'points total', 'goals total', 'runs total']
    },
    'alt_spread': {
        'type': 'spread',
        'scope': 'team',
        'aliases': [
            'alternate spread', 'alt spread', 'alternate line', 'alt line',
            'alternate puck line', 'alt puck line',
            'alternate run line', 'alt run line'
        ]
    },
    'alt_total': {
        'type': 'total',
        'scope': 'team',
        'aliases': [
            'alternate total', 'alt total', 'alternate game total',
            'alternate runs total', 'alternate goals total',
            'alternate points total'
        ]
    },

    # Halves Standard & Alternative Markets
    'moneyline_h1': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['1st half moneyline', 'first half moneyline']
    },
    'spread_h1': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['1st half spread', 'first half spread']
    },
    'total_h1': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['1st half total', 'first half total']
    },
    'alt_spread_h1': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 1st half spread', 'alt 1st half spread', 'alt spread 1h']
    },
    'alt_total_h1': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 1st half total', 'alt 1st half total', 'alt total 1h']
    },
    'moneyline_h2': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['2nd half moneyline', 'second half moneyline']
    },
    'spread_h2': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['2nd half spread', 'second half spread']
    },
    'total_h2': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['2nd half total', 'second half total']
    },
    'alt_spread_h2': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 2nd half spread', 'alt 2nd half spread', 'alt spread 2h']
    },
    'alt_total_h2': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 2nd half total', 'alt 2nd half total', 'alt total 2h']
    },

    # Quarters Standard & Alternative Markets
    'moneyline_q1': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['1st quarter moneyline', 'first quarter moneyline']
    },
    'spread_q1': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['1st quarter spread', 'first quarter spread']
    },
    'total_q1': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['1st quarter total', 'first quarter total']
    },
    'alt_spread_q1': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 1st quarter spread', 'alt 1st quarter spread', 'alt spread q1']
    },
    'alt_total_q1': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 1st quarter total', 'alt 1st quarter total', 'alt total q1']
    },
    'moneyline_q2': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['2nd quarter moneyline', 'second quarter moneyline']
    },
    'spread_q2': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['2nd quarter spread', 'second quarter spread']
    },
    'total_q2': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['2nd quarter total', 'second quarter total']
    },
    'alt_spread_q2': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 2nd quarter spread', 'alt 2nd quarter spread', 'alt spread q2']
    },
    'alt_total_q2': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 2nd quarter total', 'alt 2nd quarter total', 'alt total q2']
    },
    'moneyline_q3': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['3rd quarter moneyline', 'third quarter moneyline']
    },
    'spread_q3': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['3rd quarter spread', 'third quarter spread']
    },
    'total_q3': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['3rd quarter total', 'third quarter total']
    },
    'alt_spread_q3': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 3rd quarter spread', 'alt 3rd quarter spread', 'alt spread q3']
    },
    'alt_total_q3': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 3rd quarter total', 'alt 3rd quarter total', 'alt total q3']
    },
    'moneyline_q4': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['4th quarter moneyline', 'fourth quarter moneyline']
    },
    'spread_q4': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['4th quarter spread', 'fourth quarter spread']
    },
    'total_q4': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['4th quarter total', 'fourth quarter total']
    },
    'alt_spread_q4': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 4th quarter spread', 'alt 4th quarter spread', 'alt spread q4']
    },
    'alt_total_q4': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 4th quarter total', 'alt 4th quarter total', 'alt total q4']
    },

    # Baseball - First 5 & First 7
    'moneyline_f5': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['first 5 innings moneyline', 'f5 moneyline']
    },
    'spread_f5': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['first 5 innings spread', 'f5 spread']
    },
    'total_f5': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['first 5 innings total', 'f5 total']
    },
    'alt_spread_f5': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate first 5 innings spread', 'alt f5 spread', 'alternate f5 line']
    },
    'alt_total_f5': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate first 5 innings total', 'alt f5 total']
    },
    'moneyline_f7': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['first 7 innings moneyline', 'f7 moneyline']
    },
    'spread_f7': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['first 7 innings spread', 'f7 spread']
    },
    'total_f7': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['first 7 innings total', 'f7 total']
    },
    'alt_spread_f7': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate first 7 innings spread', 'alt f7 spread']
    },
    'alt_total_f7': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate first 7 innings total', 'alt f7 total']
    },

    # Hockey - Period Markets
    'moneyline_p1': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['1st period moneyline', 'first period moneyline']
    },
    'spread_p1': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['1st period spread', 'first period spread']
    },
    'total_p1': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['1st period total', 'first period total']
    },
    'alt_spread_p1': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 1st period spread', 'alt period 1 spread', 'alt p1 spread']
    },
    'alt_total_p1': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 1st period total', 'alt p1 total']
    },
    'moneyline_p2': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['2nd period moneyline', 'second period moneyline']
    },
    'spread_p2': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['2nd period spread', 'second period spread']
    },
    'total_p2': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['2nd period total', 'second period total']
    },
    'alt_spread_p2': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 2nd period spread', 'alt p2 spread']
    },
    'alt_total_p2': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 2nd period total', 'alt p2 total']
    },
    'moneyline_p3': {
        'type': 'moneyline',
        'scope': 'team',
        'aliases': ['3rd period moneyline', 'third period moneyline']
    },
    'spread_p3': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['3rd period spread', 'third period spread']
    },
    'total_p3': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['3rd period total', 'third period total']
    },
    'alt_spread_p3': {
        'type': 'spread',
        'scope': 'team',
        'aliases': ['alternate 3rd period spread', 'alt p3 spread']
    },
    'alt_total_p3': {
        'type': 'total',
        'scope': 'team',
        'aliases': ['alternate 3rd period total', 'alt p3 total']
    },
}

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
        REVERSE_MARKET_LOOKUP[(league, standard)] = (standard, mapping['type'], mapping['scope'])
        for alias in mapping['aliases']:
            REVERSE_MARKET_LOOKUP[(league, clean_str(alias))] = (standard, mapping['type'], mapping['scope'])

MARKET_EXACT_RESULT_REGEX = r'''
    (?:to\s)? 
    (?:record|hit|score)?
    \s*
    (?P<line>a|an|\d+\+)
    \s+
    (?P<market>
        hits?|home\s+runs?|bases?|total\s+bases?|strikeouts?|
        stolen\s+bases?|rbis?|runs?|points?|rebounds?|made\s+threes?|
        double\s+double|triple\s+double
    )
'''
MARKET_EXACT_RESULT_PATTERN = re.compile(MARKET_EXACT_RESULT_REGEX, re.IGNORECASE | re.VERBOSE)

MARKET_OVER_UNDER_REGEX = r'''
    (?P<scope>
        player|pitcher|batter|total|team
    )?
    \s*
    (?P<market>
        hits?|home\s+runs?|bases?|total\s+bases?|strikeouts?(\s+thrown)?|
        stolen\s+bases?|rbis?|runs?|points?|rebounds?|made\s+threes?
    )
'''
MARKET_OVER_UNDER_PATTERN = re.compile(MARKET_OVER_UNDER_REGEX, re.IGNORECASE | re.VERBOSE)

MARKET_SCOPE_INCLUDED_PATTERN = re.compile(r'^(?P<scope>.+)\s-\s(?P<market>.+)$')

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