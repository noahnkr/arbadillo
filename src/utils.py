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
	# General Game Lines
	'moneyline', 'spread', 'total',

	# Alternate Game Lines
	'alt_spread', 'alt_total', 'team_total',

	# Game Period Markets (Applicable to multiple sports)
	'first_half_moneyline', 'first_half_spread', 'first_half_total',
	'second_half_moneyline', 'second_half_spread', 'second_half_total',
	'first_quarter_moneyline', 'first_quarter_spread', 'first_quarter_total',
	'second_quarter_moneyline', 'second_quarter_spread', 'second_quarter_total',
	'third_quarter_moneyline', 'third_quarter_spread', 'third_quarter_total',
	'fourth_quarter_moneyline', 'fourth_quarter_spread', 'fourth_quarter_total',
	'first_period_moneyline', 'first_period_spread', 'first_period_total',
	'second_period_moneyline', 'second_period_spread', 'second_period_total',
	'third_period_moneyline', 'third_period_spread', 'third_period_total',

	# MLB Markets
	# Batting Props
	'batter_hits', 'batter_rbis', 'batter_total_bases', 'batter_runs', 
	'batter_singles', 'batter_doubles', 'batter_triples', 'batter_home_runs', 
	'batter_walks', 'batter_stolen_bases', 'batter_hits_runs_rbis',

	# Pitching Props
	'pitcher_outs', 'pitcher_strikeouts', 'pitcher_earned_runs', 'pitcher_walks',
	'pitcher_hits_allowed', 'pitcher_home_runs_allowed', 'pitcher_first_inning_runs_allowed',
	'pitcher_wins', 'pitcher_losses', 'pitcher_saves', 'pitcher_complete_games',

	# Team Props
	'team_hits', 'team_home_runs', 'team_total_runs', 'team_errors',
	'team_total_hits', 'team_total_bases', 'team_total_strikeouts', 'team_total_walks',
	'team_total_left_on_base',

	# Innings Markets
	'first_inning_moneyline', 'first_inning_total_runs', 'first_inning_3way', 
	'first_five_innings_moneyline', 'first_five_innings_spread', 'first_five_innings_total',

	# NFL/NCAAF Markets
	# Player Props
	'player_passing_yards', 'player_rushing_yards', 'player_receiving_yards', 
	'player_touchdowns', 'player_receptions', 'player_completions',
	'player_interceptions', 'player_sacks', 'player_tackles', 'player_assists',
	'player_rushing_attempts', 'player_passing_attempts', 'player_passing_completions',
	'player_fumbles', 'player_field_goals_made', 'player_extra_points_made',

	# Team Props
	'team_total_points', 'team_first_half_points', 'team_second_half_points',
	'team_total_touchdowns', 'team_field_goals', 'team_safeties',
	'team_total_first_downs', 'team_total_rushing_yards', 'team_total_passing_yards',
	'team_total_turnovers', 'team_total_sacks', 'team_total_interceptions',

	# Drive Markets
	'first_team_to_score', 'first_touchdown_scorer', 'last_touchdown_scorer',
	'anytime_touchdown_scorer', 'first_scoring_play',

	# NBA/NCAAB Markets
	# Player Props
	'player_points', 'player_rebounds', 'player_assists', 'player_steals', 
	'player_blocks', 'player_turnovers', 'player_three_pointers',
	'player_double_double', 'player_triple_double', 'player_free_throws_made',

	# Team Props
	'team_total_points', 'team_first_half_points', 'team_second_half_points',
	'team_total_rebounds', 'team_three_pointers_made', 'team_turnovers',
	'team_total_fouls', 'team_total_free_throws', 'team_total_field_goals',
	'team_total_blocks', 'team_total_steals', 'team_total_assists',
	'team_total_three_pointers',

	# NHL Markets
	# Player Props
	'player_goals', 'player_assists', 'player_points', 'player_shots', 
	'player_hits', 'player_blocks', 'player_penalty_minutes',

	# Team Props
	'team_total_goals', 'team_first_period_goals', 'team_second_period_goals', 
	'team_total_shots', 'team_total_hits', 'team_power_play_goals',
	'team_total_penalty_minutes', 'team_total_faceoff_wins', 'team_total_saves',

	# Soccer Markets
	# Player Props
	'player_goals', 'player_assists', 'player_shots', 'player_shots_on_target',
	'player_passes', 'player_tackles', 'player_clearances', 'player_saves',
	'player_offsides', 'player_fouls', 'player_yellow_cards', 'player_red_cards',

	# Team Props
	'team_total_goals', 'team_first_half_goals', 'team_second_half_goals',
	'team_total_shots', 'team_total_corners', 'team_possession_percentage',
	'team_total_fouls', 'team_total_offsides', 'team_total_yellow_cards',
	'team_total_red_cards', 'team_total_free_kicks', 'team_total_goal_kicks',

	# Tennis Markets
	# Player Props
	'player_aces', 'player_double_faults', 'player_first_serve_percentage',
	'player_break_points_won', 'player_total_games_won', 'player_total_sets_won',

	# Golf Markets
	# Player Props
	'player_strokes', 'player_birdies', 'player_eagles', 'player_bogeys',
	'player_double_bogeys', 'player_pars', 'player_putts', 'player_driving_distance',
	'player_greens_in_regulation', 'player_fairways_hit',

	# Motorsports Markets (NASCAR, Formula 1, etc.)
	# Driver Props
	'driver_wins', 'driver_podiums', 'driver_top_10', 'driver_fastest_lap',
	'driver_pit_stop_time', 'driver_overtakes', 'driver_lap_led',

	# Race Markets
	'fastest_lap', 'most_lead_changes', 'most_overtakes', 'safety_car_appearance',
	'total_race_time', 'margin_of_victory',

	# Boxing/MMA Markets
	# Fighter Props
	'fighter_wins', 'fighter_by_ko_tko', 'fighter_by_submission', 'fighter_by_decision',
	'fighter_total_strikes', 'fighter_total_significant_strikes', 'fighter_total_takedowns',
	'fighter_total_knockdowns', 'fighter_total_clinch_time', 'fighter_total_control_time',

	# Round Markets
	'round_moneyline', 'round_total', 'round_to_go_distance', 'round_method_of_victory',

	# eSports Markets
	# Player Props
	'player_kills', 'player_assists', 'player_deaths', 'player_headshots',
	'player_damage', 'player_healing', 'player_first_blood', 'player_cs',
	'player_gold', 'player_towers_destroyed',

	# Team Props
	'team_total_kills', 'team_total_towers_destroyed', 'team_total_dragons',
	'team_total_barons', 'team_total_cs', 'team_total_gold', 'team_first_blood',
	'team_total_heralds',

	# Miscellaneous Markets
	# (Applicable for less common or custom markets)
	'specials', 'boosted_odds', 'custom_markets', 'exotic_bets',
	'prop_builder', 'parlays', 'teasers', 'futures',
}

MARKET_MAPPINGS = {
    # General Game Lines
    'moneyline': 'moneyline',
    'ml': 'moneyline',
    'money_line': 'moneyline',
    'money_line_bet': 'moneyline',
    'straight_up': 'moneyline',
    
    'spread': 'spread',
    'point_spread': 'spread',
    'handicap': 'spread',
    'against_the_spread': 'spread',

    'total': 'total',
    'over_under': 'total',
    'points_total': 'total',
    'totals': 'total',

    # Alternate Game Lines
    'alternate_spread': 'alt_spread',
    'alt_spread': 'alt_spread',
    'alternate_total': 'alt_total',
    'alt_total': 'alt_total',
    'team_total': 'team_total',

    # Game Period Markets (Applicable to multiple sports)
    'first_half_moneyline': 'first_half_moneyline',
    '1h_moneyline': 'first_half_moneyline',
    '1st_half_ml': 'first_half_moneyline',
    '1h_ml': 'first_half_moneyline',
    '1st_half_moneyline': 'first_half_moneyline',

    'first_half_spread': 'first_half_spread',
    '1h_spread': 'first_half_spread',
    '1st_half_spread': 'first_half_spread',

    'first_half_total': 'first_half_total',
    '1h_total': 'first_half_total',
    '1st_half_total': 'first_half_total',

    'second_half_moneyline': 'second_half_moneyline',
    '2h_moneyline': 'second_half_moneyline',
    '2nd_half_ml': 'second_half_moneyline',
    '2h_ml': 'second_half_moneyline',
    '2nd_half_moneyline': 'second_half_moneyline',

    'second_half_spread': 'second_half_spread',
    '2h_spread': 'second_half_spread',
    '2nd_half_spread': 'second_half_spread',

    'second_half_total': 'second_half_total',
    '2h_total': 'second_half_total',
    '2nd_half_total': 'second_half_total',

    'first_quarter_moneyline': 'first_quarter_moneyline',
    '1q_moneyline': 'first_quarter_moneyline',
    '1st_qtr_ml': 'first_quarter_moneyline',
    '1st_qtr_moneyline': 'first_quarter_moneyline',
    '1q_ml': 'first_quarter_moneyline',

    'first_quarter_spread': 'first_quarter_spread',
    '1q_spread': 'first_quarter_spread',
    '1st_qtr_spread': 'first_quarter_spread',

    'first_quarter_total': 'first_quarter_total',
    '1q_total': 'first_quarter_total',
    '1st_qtr_total': 'first_quarter_total',

    'second_quarter_moneyline': 'second_quarter_moneyline',
    '2q_moneyline': 'second_quarter_moneyline',
    '2nd_qtr_ml': 'second_quarter_moneyline',
    '2q_ml': 'second_quarter_moneyline',
    '2nd_qtr_moneyline': 'second_quarter_moneyline',

    'second_quarter_spread': 'second_quarter_spread',
    '2q_spread': 'second_quarter_spread',
    '2nd_qtr_spread': 'second_quarter_spread',

    'second_quarter_total': 'second_quarter_total',
    '2q_total': 'second_quarter_total',
    '2nd_qtr_total': 'second_quarter_total',

    'third_quarter_moneyline': 'third_quarter_moneyline',
    '3q_moneyline': 'third_quarter_moneyline',
    '3rd_qtr_ml': 'third_quarter_moneyline',
    '3q_ml': 'third_quarter_moneyline',
    '3rd_qtr_moneyline': 'third_quarter_moneyline',

    'third_quarter_spread': 'third_quarter_spread',
    '3q_spread': 'third_quarter_spread',
    '3rd_qtr_spread': 'third_quarter_spread',

    'third_quarter_total': 'third_quarter_total',
    '3q_total': 'third_quarter_total',
    '3rd_qtr_total': 'third_quarter_total',

    'fourth_quarter_moneyline': 'fourth_quarter_moneyline',
    '4q_moneyline': 'fourth_quarter_moneyline',
    '4th_qtr_ml': 'fourth_quarter_moneyline',
    '4q_ml': 'fourth_quarter_moneyline',
    '4th_qtr_moneyline': 'fourth_quarter_moneyline',

    'fourth_quarter_spread': 'fourth_quarter_spread',
    '4q_spread': 'fourth_quarter_spread',
    '4th_qtr_spread': 'fourth_quarter_spread',

    'fourth_quarter_total': 'fourth_quarter_total',
    '4q_total': 'fourth_quarter_total',
    '4th_qtr_total': 'fourth_quarter_total',

    'first_period_moneyline': 'first_period_moneyline',
    '1p_moneyline': 'first_period_moneyline',
    '1st_period_ml': 'first_period_moneyline',
    '1st_period_moneyline': 'first_period_moneyline',
    '1p_ml': 'first_period_moneyline',

    'first_period_spread': 'first_period_spread',
    '1p_spread': 'first_period_spread',
    '1st_period_spread': 'first_period_spread',

    'first_period_total': 'first_period_total',
    '1p_total': 'first_period_total',
    '1st_period_total': 'first_period_total',

    'second_period_moneyline': 'second_period_moneyline',
    '2p_moneyline': 'second_period_moneyline',
    '2nd_period_ml': 'second_period_moneyline',
    '2p_ml': 'second_period_moneyline',
    '2nd_period_moneyline': 'second_period_moneyline',

    'second_period_spread': 'second_period_spread',
    '2p_spread': 'second_period_spread',
    '2nd_period_spread': 'second_period_spread',

    'second_period_total': 'second_period_total',
    '2p_total': 'second_period_total',
    '2nd_period_total': 'second_period_total',

    'third_period_moneyline': 'third_period_moneyline',
    '3p_moneyline': 'third_period_moneyline',
    '3rd_period_ml': 'third_period_moneyline',
    '3p_ml': 'third_period_moneyline',
    '3rd_period_moneyline': 'third_period_moneyline',

    'third_period_spread': 'third_period_spread',
    '3p_spread': 'third_period_spread',
    '3rd_period_spread': 'third_period_spread',

    'third_period_total': 'third_period_total',
    '3p_total': 'third_period_total',
    '3rd_period_total': 'third_period_total',

    # MLB Markets
    # Batting Props
    'batter_hits': 'batter_hits',
    'total_hits': 'batter_hits',
    'player_hits': 'batter_hits',

    'batter_rbis': 'batter_rbis',
    'runs_batted_in': 'batter_rbis',
    'player_rbis': 'batter_rbis',

    'batter_total_bases': 'batter_total_bases',
    'total_bases': 'batter_total_bases',
    'player_total_bases': 'batter_total_bases',

    'batter_runs': 'batter_runs',
    'runs_scored': 'batter_runs',
    'player_runs': 'batter_runs',

    'batter_singles': 'batter_singles',
    'total_singles': 'batter_singles',
    'player_singles': 'batter_singles',

    'batter_doubles': 'batter_doubles',
    'total_doubles': 'batter_doubles',
    'player_doubles': 'batter_doubles',

    'batter_triples': 'batter_triples',
    'total_triples': 'batter_triples',
    'player_triples': 'batter_triples',

    'batter_home_runs': 'batter_home_runs',
    'total_home_runs': 'batter_home_runs',
    'player_home_runs': 'batter_home_runs',

    'batter_walks': 'batter_walks',
    'total_walks': 'batter_walks',
    'player_walks': 'batter_walks',

    'batter_stolen_bases': 'batter_stolen_bases',
    'total_stolen_bases': 'batter_stolen_bases',
    'player_stolen_bases': 'batter_stolen_bases',

    'batter_hits_runs_rbis': 'batter_hits_runs_rbis',
    'hits_runs_rbis': 'batter_hits_runs_rbis',
    'total_hits_runs_rbis': 'batter_hits_runs_rbis',
    'player_hits_runs_rbis': 'batter_hits_runs_rbis',
    'batter_h_r_rbis': 'batter_hits_runs_rbis',
    'h_r_rbis': 'batter_hits_runs_rbis',
    'total_h_r_rbis': 'batter_hits_runs_rbis',
    'player_h_r_rbis': 'batter_hits_runs_rbis',

    # Pitching Props
    'pitcher_outs': 'pitcher_outs',
    'outs_recorded': 'pitcher_outs',
    'player_outs_recorded': 'pitcher_outs',

    'pitcher_strikeouts': 'pitcher_strikeouts',
    'total_strikeouts': 'pitcher_strikeouts',
    'player_strikeouts': 'pitcher_strikeouts',

    'pitcher_earned_runs': 'pitcher_earned_runs',
    'total_earned_runs': 'pitcher_earned_runs',
    'player_earned_runs': 'pitcher_earned_runs',

    'pitcher_walks': 'pitcher_walks',
    'total_walks': 'pitcher_walks',
    'player_walks': 'pitcher_walks',

    'pitcher_hits_allowed': 'pitcher_hits_allowed',
    'total_hits_allowed': 'pitcher_hits_allowed',
    'player_hits_allowed': 'pitcher_hits_allowed',

    'pitcher_home_runs_allowed': 'pitcher_home_runs_allowed',
    'total_home_runs_allowed': 'pitcher_home_runs_allowed',
    'player_home_runs_allowed': 'pitcher_home_runs_allowed',

    'pitcher_first_inning_runs_allowed': 'pitcher_first_inning_runs_allowed',
    '1st_inning_runs_allowed': 'pitcher_first_inning_runs_allowed',
    'first_inning_runs_allowed': 'pitcher_first_inning_runs_allowed',
    'player_first_inning_runs_allowed': 'pitcher_first_inning_runs_allowed',

    'pitcher_wins': 'pitcher_wins',
    'total_wins': 'pitcher_wins',
    'player_wins': 'pitcher_wins',

    'pitcher_losses': 'pitcher_losses',
    'total_losses': 'pitcher_losses',
    'player_losses': 'pitcher_losses',

    'pitcher_saves': 'pitcher_saves',
    'total_saves': 'pitcher_saves',
    'player_saves': 'pitcher_saves',

    'pitcher_complete_games': 'pitcher_complete_games',
    'total_complete_games': 'pitcher_complete_games',
    'player_complete_games': 'pitcher_complete_games',

    # Team Props
    'team_hits': 'team_hits',
    'total_team_hits': 'team_hits',

    'team_home_runs': 'team_home_runs',
    'total_team_home_runs': 'team_home_runs',

    'team_total_runs': 'team_total_runs',
    'total_team_runs': 'team_total_runs',

    'team_errors': 'team_errors',
    'total_team_errors': 'team_errors',

    'team_total_hits': 'team_total_hits',
    'total_team_total_hits': 'team_total_hits',

    'team_total_bases': 'team_total_bases',
    'total_team_total_bases': 'team_total_bases',

    'team_total_strikeouts': 'team_total_strikeouts',
    'total_team_total_strikeouts': 'team_total_strikeouts',

    'team_total_walks': 'team_total_walks',
    'total_team_total_walks': 'team_total_walks',

    'team_total_left_on_base': 'team_total_left_on_base',
    'total_team_total_left_on_base': 'team_total_left_on_base',

    # Innings Markets
    'first_inning_moneyline': 'first_inning_moneyline',
    '1st_inning_moneyline': 'first_inning_moneyline',
    'first_inning_ml': 'first_inning_moneyline',
    '1st_inning_ml': 'first_inning_moneyline',

    'first_inning_total_runs': 'first_inning_total_runs',
    '1st_inning_total_runs': 'first_inning_total_runs',
    'first_inning_total': 'first_inning_total_runs',
    '1st_inning_total': 'first_inning_total_runs',

    'first_inning_3way': 'first_inning_3way',
    '1st_inning_3way': 'first_inning_3way',
    'first_inning_3_way': 'first_inning_3way',
    '1st_inning_3_way': 'first_inning_3way',

    'first_five_innings_moneyline': 'first_five_innings_moneyline',
    '1st_5_innings_moneyline': 'first_five_innings_moneyline',
    '1st_5_ml': 'first_five_innings_moneyline',
    'first_5_innings_ml': 'first_five_innings_moneyline',

    'first_five_innings_spread': 'first_five_innings_spread',
    '1st_5_innings_spread': 'first_five_innings_spread',
    '1st_5_spread': 'first_five_innings_spread',
    'first_5_innings_spread': 'first_five_innings_spread',

    'first_five_innings_total': 'first_five_innings_total',
    '1st_5_innings_total': 'first_five_innings_total',
    '1st_5_total': 'first_five_innings_total',
    'first_5_innings_total': 'first_five_innings_total',

    # NFL/NCAAF Markets
    # Player Props
    'player_passing_yards': 'player_passing_yards',
    'passing_yards': 'player_passing_yards',
    'pass_yards': 'player_passing_yards',
    'yards_passing': 'player_passing_yards',

    'player_rushing_yards': 'player_rushing_yards',
    'rushing_yards': 'player_rushing_yards',
    'rush_yards': 'player_rushing_yards',
    'yards_rushing': 'player_rushing_yards',

    'player_receiving_yards': 'player_receiving_yards',
    'receiving_yards': 'player_receiving_yards',
    'receive_yards': 'player_receiving_yards',
    'yards_receiving': 'player_receiving_yards',

    'player_touchdowns': 'player_touchdowns',
    'touchdowns': 'player_touchdowns',
    'tds': 'player_touchdowns',
    'td': 'player_touchdowns',

    'player_receptions': 'player_receptions',
    'receptions': 'player_receptions',
    'rec': 'player_receptions',
    'catches': 'player_receptions',

    'player_completions': 'player_completions',
    'completions': 'player_completions',
    'comp': 'player_completions',

    'player_interceptions': 'player_interceptions',
    'interceptions': 'player_interceptions',
    'ints': 'player_interceptions',

    'player_sacks': 'player_sacks',
    'sacks': 'player_sacks',

    'player_tackles': 'player_tackles',
    'tackles': 'player_tackles',

    'player_assists': 'player_assists',
    'assists': 'player_assists',

    'player_rushing_attempts': 'player_rushing_attempts',
    'rushing_attempts': 'player_rushing_attempts',
    'rush_attempts': 'player_rushing_attempts',
    'attempts_rushing': 'player_rushing_attempts',

    'player_passing_attempts': 'player_passing_attempts',
    'passing_attempts': 'player_passing_attempts',
    'pass_attempts': 'player_passing_attempts',
    'attempts_passing': 'player_passing_attempts',

    'player_passing_completions': 'player_passing_completions',
    'passing_completions': 'player_passing_completions',
    'pass_completions': 'player_passing_completions',
    'completions_passing': 'player_passing_completions',

    'player_fumbles': 'player_fumbles',
    'fumbles': 'player_fumbles',

    'player_field_goals_made': 'player_field_goals_made',
    'field_goals_made': 'player_field_goals_made',
    'fg_made': 'player_field_goals_made',
    'fgs_made': 'player_field_goals_made',

    'player_extra_points_made': 'player_extra_points_made',
    'extra_points_made': 'player_extra_points_made',
    'xp_made': 'player_extra_points_made',

    # Team Props
    'team_total_points': 'team_total_points',
    'total_team_points': 'team_total_points',

    'team_first_half_points': 'team_first_half_points',
    'total_team_1h_points': 'team_first_half_points',
    '1h_team_points': 'team_first_half_points',

    'team_second_half_points': 'team_second_half_points',
    'total_team_2h_points': 'team_second_half_points',
    '2h_team_points': 'team_second_half_points',

    'team_total_touchdowns': 'team_total_touchdowns',
    'total_team_touchdowns': 'team_total_touchdowns',

    'team_field_goals': 'team_field_goals',
    'total_team_field_goals': 'team_field_goals',
    'team_fgs': 'team_field_goals',

    'team_safeties': 'team_safeties',
    'total_team_safeties': 'team_safeties',

    'team_total_first_downs': 'team_total_first_downs',
    'total_team_first_downs': 'team_total_first_downs',
    'team_first_downs': 'team_total_first_downs',

    'team_total_rushing_yards': 'team_total_rushing_yards',
    'total_team_rushing_yards': 'team_total_rushing_yards',

    'team_total_passing_yards': 'team_total_passing_yards',
    'total_team_passing_yards': 'team_total_passing_yards',

    'team_total_turnovers': 'team_total_turnovers',
    'total_team_turnovers': 'team_total_turnovers',

    'team_total_sacks': 'team_total_sacks',
    'total_team_sacks': 'team_total_sacks',

    'team_total_interceptions': 'team_total_interceptions',
    'total_team_interceptions': 'team_total_interceptions',

    # Drive Markets
    'first_team_to_score': 'first_team_to_score',
    'first_score_team': 'first_team_to_score',

    'first_touchdown_scorer': 'first_touchdown_scorer',
    'first_td_scorer': 'first_touchdown_scorer',
    'first_td': 'first_touchdown_scorer',

    'last_touchdown_scorer': 'last_touchdown_scorer',
    'last_td_scorer': 'last_touchdown_scorer',
    'last_td': 'last_touchdown_scorer',

    'anytime_touchdown_scorer': 'anytime_touchdown_scorer',
    'anytime_td_scorer': 'anytime_touchdown_scorer',
    'anytime_td': 'anytime_touchdown_scorer',

    'first_scoring_play': 'first_scoring_play',
    'first_score': 'first_scoring_play',

    # NBA/NCAAB Markets
    # Player Props
    'player_points': 'player_points',
    'points': 'player_points',
    'pts': 'player_points',

    'player_rebounds': 'player_rebounds',
    'rebounds': 'player_rebounds',
    'rebs': 'player_rebounds',

    'player_assists': 'player_assists',
    'assists': 'player_assists',
    'asts': 'player_assists',

    'player_steals': 'player_steals',
    'steals': 'player_steals',
    'stls': 'player_steals',

    'player_blocks': 'player_blocks',
    'blocks': 'player_blocks',
    'blks': 'player_blocks',

    'player_turnovers': 'player_turnovers',
    'turnovers': 'player_turnovers',
    'tos': 'player_turnovers',

    'player_three_pointers': 'player_three_pointers',
    'three_pointers': 'player_three_pointers',
    '3p': 'player_three_pointers',
    '3pts': 'player_three_pointers',

    'player_double_double': 'player_double_double',
    'double_double': 'player_double_double',

    'player_triple_double': 'player_triple_double',
    'triple_double': 'player_triple_double',

    'player_free_throws_made': 'player_free_throws_made',
    'free_throws_made': 'player_free_throws_made',
    'ft_made': 'player_free_throws_made',

    # Team Props
    'team_total_points': 'team_total_points',
    'total_team_points': 'team_total_points',

    'team_first_half_points': 'team_first_half_points',
    'total_team_1h_points': 'team_first_half_points',
    '1h_team_points': 'team_first_half_points',

    'team_second_half_points': 'team_second_half_points',
    'total_team_2h_points': 'team_second_half_points',
    '2h_team_points': 'team_second_half_points',

    'team_total_rebounds': 'team_total_rebounds',
    'total_team_rebounds': 'team_total_rebounds',

    'team_three_pointers_made': 'team_three_pointers_made',
    'total_team_three_pointers_made': 'team_three_pointers_made',
    'team_3pts_made': 'team_three_pointers_made',

    'team_turnovers': 'team_turnovers',
    'total_team_turnovers': 'team_turnovers',

    'team_total_fouls': 'team_total_fouls',
    'total_team_fouls': 'team_total_fouls',

    'team_total_free_throws': 'team_total_free_throws',
    'total_team_free_throws': 'team_total_free_throws',

    'team_total_field_goals': 'team_total_field_goals',
    'total_team_field_goals': 'team_total_field_goals',

    'team_total_blocks': 'team_total_blocks',
    'total_team_blocks': 'team_total_blocks',

    'team_total_steals': 'team_total_steals',
    'total_team_steals': 'team_total_steals',

    'team_total_assists': 'team_total_assists',
    'total_team_assists': 'team_total_assists',

    'team_total_three_pointers': 'team_total_three_pointers',
    'total_team_3pts': 'team_total_three_pointers',

    # NHL Markets
    # Player Props
    'player_goals': 'player_goals',
    'goals': 'player_goals',
    'g': 'player_goals',

    'player_assists': 'player_assists',
    'assists': 'player_assists',
    'a': 'player_assists',

    'player_points': 'player_points',
    'points': 'player_points',
    'pts': 'player_points',

    'player_shots': 'player_shots',
    'shots': 'player_shots',
    'sog': 'player_shots',

    'player_hits': 'player_hits',
    'hits': 'player_hits',
    'h': 'player_hits',

    'player_blocks': 'player_blocks',
    'blocks': 'player_blocks',
    'blk': 'player_blocks',

    'player_penalty_minutes': 'player_penalty_minutes',
    'penalty_minutes': 'player_penalty_minutes',
    'pim': 'player_penalty_minutes',

    # Team Props
    'team_total_goals': 'team_total_goals',
    'total_team_goals': 'team_total_goals',

    'team_first_period_goals': 'team_first_period_goals',
    'total_team_1p_goals': 'team_first_period_goals',

    'team_second_period_goals': 'team_second_period_goals',
    'total_team_2p_goals': 'team_second_period_goals',

    'team_total_shots': 'team_total_shots',
    'total_team_shots': 'team_total_shots',

    'team_total_hits': 'team_total_hits',
    'total_team_hits': 'team_total_hits',

    'team_power_play_goals': 'team_power_play_goals',
    'total_team_pp_goals': 'team_power_play_goals',

    'team_total_penalty_minutes': 'team_total_penalty_minutes',
    'total_team_penalty_minutes': 'team_total_penalty_minutes',
    'team_pim': 'team_total_penalty_minutes',

    'team_total_faceoff_wins': 'team_total_faceoff_wins',
    'total_team_faceoff_wins': 'team_total_faceoff_wins',

    'team_total_saves': 'team_total_saves',
    'total_team_saves': 'team_total_saves',

    # Soccer Markets
    # Player Props
    'player_goals': 'player_goals',
    'goals_scored': 'player_goals',
    'goal': 'player_goals',

    'player_assists': 'player_assists',
    'assists': 'player_assists',

    'player_shots': 'player_shots',
    'shots': 'player_shots',

    'player_shots_on_target': 'player_shots_on_target',
    'shots_on_target': 'player_shots_on_target',
    'sog': 'player_shots_on_target',

    'player_passes': 'player_passes',
    'passes': 'player_passes',

    'player_tackles': 'player_tackles',
    'tackles': 'player_tackles',

    'player_clearances': 'player_clearances',
    'clearances': 'player_clearances',

    'player_saves': 'player_saves',
    'saves': 'player_saves',

    'player_offsides': 'player_offsides',
    'offsides': 'player_offsides',

    'player_fouls': 'player_fouls',
    'fouls': 'player_fouls',

    'player_yellow_cards': 'player_yellow_cards',
    'yellow_cards': 'player_yellow_cards',
    'ycs': 'player_yellow_cards',

    'player_red_cards': 'player_red_cards',
    'red_cards': 'player_red_cards',
    'rcs': 'player_red_cards',

    # Team Props
    'team_total_goals': 'team_total_goals',
    'total_team_goals': 'team_total_goals',

    'team_first_half_goals': 'team_first_half_goals',
    'total_team_1h_goals': 'team_first_half_goals',

    'team_second_half_goals': 'team_second_half_goals',
    'total_team_2h_goals': 'team_second_half_goals',

    'team_total_shots': 'team_total_shots',
    'total_team_shots': 'team_total_shots',

    'team_total_corners': 'team_total_corners',
    'total_team_corners': 'team_total_corners',

    'team_possession_percentage': 'team_possession_percentage',
    'possession_percentage': 'team_possession_percentage',
    'team_possession': 'team_possession_percentage',

    'team_total_fouls': 'team_total_fouls',
    'total_team_fouls': 'team_total_fouls',

    'team_total_offsides': 'team_total_offsides',
    'total_team_offsides': 'team_total_offsides',

    'team_total_yellow_cards': 'team_total_yellow_cards',
    'total_team_yellow_cards': 'team_total_yellow_cards',
    'team_yellow_cards': 'team_total_yellow_cards',

    'team_total_red_cards': 'team_total_red_cards',
    'total_team_red_cards': 'team_total_red_cards',
    'team_red_cards': 'team_total_red_cards',

    'team_total_free_kicks': 'team_total_free_kicks',
    'total_team_free_kicks': 'team_total_free_kicks',

    'team_total_goal_kicks': 'team_total_goal_kicks',
    'total_team_goal_kicks': 'team_total_goal_kicks',

    # Tennis Markets
    # Player Props
    'player_aces': 'player_aces',
    'aces': 'player_aces',

    'player_double_faults': 'player_double_faults',
    'double_faults': 'player_double_faults',

    'player_first_serve_percentage': 'player_first_serve_percentage',
    'first_serve_percentage': 'player_first_serve_percentage',

    'player_break_points_won': 'player_break_points_won',
    'break_points_won': 'player_break_points_won',

    'player_total_games_won': 'player_total_games_won',
    'total_games_won': 'player_total_games_won',
    'games_won': 'player_total_games_won',

    'player_total_sets_won': 'player_total_sets_won',
    'total_sets_won': 'player_total_sets_won',
    'sets_won': 'player_total_sets_won',

    # Golf Markets
    # Player Props
    'player_strokes': 'player_strokes',
    'strokes': 'player_strokes',

    'player_birdies': 'player_birdies',
    'birdies': 'player_birdies',

    'player_eagles': 'player_eagles',
    'eagles': 'player_eagles',

    'player_bogeys': 'player_bogeys',
    'bogeys': 'player_bogeys',

    'player_double_bogeys': 'player_double_bogeys',
    'double_bogeys': 'player_double_bogeys',

    'player_pars': 'player_pars',
    'pars': 'player_pars',

    'player_putts': 'player_putts',
    'putts': 'player_putts',

    'player_driving_distance': 'player_driving_distance',
    'driving_distance': 'player_driving_distance',

    'player_greens_in_regulation': 'player_greens_in_regulation',
    'greens_in_regulation': 'player_greens_in_regulation',
    'gir': 'player_greens_in_regulation',

    'player_fairways_hit': 'player_fairways_hit',
    'fairways_hit': 'player_fairways_hit',

    # Motorsports Markets (NASCAR, Formula 1, etc.)
    # Driver Props
    'driver_wins': 'driver_wins',
    'race_winner': 'driver_wins',

    'driver_podiums': 'driver_podiums',
    'podiums': 'driver_podiums',

    'driver_top_10': 'driver_top_10',
    'top_10': 'driver_top_10',

    'driver_fastest_lap': 'driver_fastest_lap',
    'fastest_lap': 'driver_fastest_lap',

    'driver_pit_stop_time': 'driver_pit_stop_time',
    'pit_stop_time': 'driver_pit_stop_time',

    'driver_overtakes': 'driver_overtakes',
    'overtakes': 'driver_overtakes',

    'driver_lap_led': 'driver_lap_led',
    'lap_led': 'driver_lap_led',

    # Race Markets
    'fastest_lap': 'fastest_lap',
    'most_lead_changes': 'most_lead_changes',
    'most_overtakes': 'most_overtakes',
    'safety_car_appearance': 'safety_car_appearance',
    'total_race_time': 'total_race_time',
    'margin_of_victory': 'margin_of_victory',

    # Boxing/MMA Markets
    # Fighter Props
    'fighter_wins': 'fighter_wins',
    'fight_winner': 'fighter_wins',
    'match_winner': 'fighter_wins',

    'fighter_by_ko_tko': 'fighter_by_ko_tko',
    'ko_tko': 'fighter_by_ko_tko',

    'fighter_by_submission': 'fighter_by_submission',
    'submission': 'fighter_by_submission',

    'fighter_by_decision': 'fighter_by_decision',
    'decision': 'fighter_by_decision',

    'fighter_total_strikes': 'fighter_total_strikes',
    'total_strikes': 'fighter_total_strikes',

    'fighter_total_significant_strikes': 'fighter_total_significant_strikes',
    'significant_strikes': 'fighter_total_significant_strikes',

    'fighter_total_takedowns': 'fighter_total_takedowns',
    'total_takedowns': 'fighter_total_takedowns',

    'fighter_total_knockdowns': 'fighter_total_knockdowns',
    'total_knockdowns': 'fighter_total_knockdowns',

    'fighter_total_clinch_time': 'fighter_total_clinch_time',
    'total_clinch_time': 'fighter_total_clinch_time',

    'fighter_total_control_time': 'fighter_total_control_time',
    'total_control_time': 'fighter_total_control_time',

    # Round Markets
    'round_moneyline': 'round_moneyline',
    'round_ml': 'round_moneyline',

    'round_total': 'round_total',
    'total_rounds': 'round_total',

    'round_to_go_distance': 'round_to_go_distance',
    'to_go_the_distance': 'round_to_go_distance',

    'round_method_of_victory': 'round_method_of_victory',
    'method_of_victory': 'round_method_of_victory',

    # eSports Markets
    # Player Props
    'player_kills': 'player_kills',
    'kills': 'player_kills',

    'player_assists': 'player_assists',
    'assists': 'player_assists',

    'player_deaths': 'player_deaths',
    'deaths': 'player_deaths',

    'player_headshots': 'player_headshots',
    'headshots': 'player_headshots',

    'player_damage': 'player_damage',
    'damage': 'player_damage',

    'player_healing': 'player_healing',
    'healing': 'player_healing',

    'player_first_blood': 'player_first_blood',
    'first_blood': 'player_first_blood',

    'player_cs': 'player_cs',
    'cs': 'player_cs',

    'player_gold': 'player_gold',
    'gold': 'player_gold',

    'player_towers_destroyed': 'player_towers_destroyed',
    'towers_destroyed': 'player_towers_destroyed',

    # Team Props
    'team_total_kills': 'team_total_kills',
    'total_team_kills': 'team_total_kills',

    'team_total_towers_destroyed': 'team_total_towers_destroyed',
    'total_team_towers_destroyed': 'team_total_towers_destroyed',

    'team_total_dragons': 'team_total_dragons',
    'total_team_dragons': 'team_total_dragons',

    'team_total_barons': 'team_total_barons',
    'total_team_barons': 'team_total_barons',

    'team_total_cs': 'team_total_cs',
    'total_team_cs': 'team_total_cs',

    'team_total_gold': 'team_total_gold',
    'total_team_gold': 'team_total_gold',

    'team_first_blood': 'team_first_blood',
    'first_team_blood': 'team_first_blood',

    'team_total_heralds': 'team_total_heralds',
    'total_team_heralds': 'team_total_heralds',

    # Miscellaneous Markets
    'specials': 'specials',
    'boosted_odds': 'boosted_odds',
    'custom_markets': 'custom_markets',
    'exotic_bets': 'exotic_bets',
    'prop_builder': 'prop_builder',
    'parlays': 'parlays',
    'teasers': 'teasers',
    'futures': 'futures',
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
    'LOS ANGELES CLIPPERS': 'LAC', 'LA CLIPPERS': 'LAC', 'CLIPPERS': 'LAC', 'LAC': 'LAC',
    'LOS ANGELES LAKERS': 'LAL', 'LAKERS': 'LAL', 'LA LAKERS': 'LAL', 'LOS ANGELES L': 'LAL', 'LAL': 'LAL',
    'MEMPHIS GRIZZLIES': 'MEM', 'MEMPHIS': 'MEM', 'GRIZZLIES': 'MEM', 'MEM': 'MEM',
    'MIAMI HEAT': 'MIA', 'MIAMI': 'MIA', 'HEAT': 'MIA', 'MIA': 'MIA',
    'MILWAUKEE BUCKS': 'MIL', 'MILWAUKEE': 'MIL', 'BUCKS': 'MIL', 'MIL': 'MIL',
    'MINNESOTA TIMBERWOLVES': 'MIN', 'MINNESOTA': 'MIN', 'TIMBERWOLVES': 'MIN', 'MIN': 'MIN',
    'NEW ORLEANS PELICANS': 'NOP', 'NEW ORLEANS': 'NOP', 'PELICANS': 'NOP', 'NOP': 'NOP',
    'NEW YORK KNICKS': 'NYK', 'NEW YORK K': 'NYK', 'NEW YORK KN': 'NYK', 'KNICKS': 'NYK', 'NYK': 'NYK',
    'OKLAHOMA CITY THUNDER': 'OKC', 'OKLAHOMA CITY': 'OKC', 'THUNDER': 'OKC', 'OKC': 'OKC',
    'ORLANDO MAGIC': 'ORL', 'ORLANDO': 'ORL', 'MAGIC': 'ORL', 'ORL': 'ORL',
    'PHILADELPHIA 76ERS': 'PHI', 'PHILADELPHIA': 'PHI', '76ERS': 'PHI', 'SIXERS': 'PHI', 'PHI': 'PHI',
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
    'LOS ANGELES CHARGERS': 'LAC', 'LA CHARGERS': 'LAC', 'CHARGERS': 'LAC', 'LAC': 'LAC',
    'LOS ANGELES RAMS': 'LAR', 'LA RAMS': 'LAR', 'RAMS': 'LAR', 'LAR': 'LAR',
    'MIAMI DOLPHINS': 'MIA', 'MIAMI': 'MIA', 'DOLPHINS': 'MIA', 'MIA': 'MIA',
    'MINNESOTA VIKINGS': 'MIN', 'MINNESOTA': 'MIN', 'VIKINGS': 'MIN', 'MIN': 'MIN',
    'NEW ENGLAND PATRIOTS': 'NE', 'NEW ENGLAND': 'NE', 'PATRIOTS': 'NE', 'NE': 'NE',
    'NEW ORLEANS SAINTS': 'NO', 'NEW ORLEANS': 'NO', 'SAINTS': 'NO', 'NO': 'NO',
    'NEW YORK GIANTS': 'NYG', 'NEW YORK G': 'NYG', 'GIANTS': 'NYG', 'NYG': 'NYG',
    'NEW YORK JETS': 'NYJ', 'NEW YORK J': 'NYJ', 'JETS': 'NYJ', 'NYJ': 'NYJ',
    'LAS VEGAS RAIDERS': 'LV', 'LAS VEGAS': 'LV', 'RAIDERS': 'LV', 'LV': 'LV',
    'PHILADELPHIA EAGLES': 'PHI', 'PHILADELPHIA': 'PHI', 'EAGLES': 'PHI', 'PHI': 'PHI',
    'PITTSBURGH STEELERS': 'PIT', 'PITTSBURGH': 'PIT', 'STEELERS': 'PIT', 'PIT': 'PIT',
    'SAN FRANCISCO 49ERS': 'SF', 'SAN FRANCISCO': 'SF', '49ERS': 'SF', 'NINERS': 'SF', 'SF': 'SF',
    'SEATTLE SEAHAWKS': 'SEA', 'SEATTLE': 'SEA', 'SEAHAWKS': 'SEA', 'SEA': 'SEA',
    'TAMPA BAY BUCCANEERS': 'TB', 'TAMPA BAY': 'TB', 'BUCCANEERS': 'TB', 'BUCS': 'TB', 'TB': 'TB',
    'TENNESSEE TITANS': 'TEN', 'TENNESSEE': 'TEN', 'TITANS': 'TEN', 'TEN': 'TEN',
    'WASHINGTON FOOTBALL TEAM': 'WAS', 'WASHINGTON': 'WAS', 'WFT': 'WAS', 'WAS': 'WAS',

    # MLB
    'ARIZONA DIAMONDBACKS': 'ARI', 'ARIZONA': 'ARI', 'DIAMONDBACKS': 'ARI', 'DBACKS': 'ARI', 'ARI': 'ARI',
    'ATLANTA BRAVES': 'ATL', 'ATLANTA': 'ATL', 'BRAVES': 'ATL', 'ATL': 'ATL',
    'BALTIMORE ORIOLES': 'BAL', 'BALTIMORE': 'BAL', 'ORIOLES': 'BAL', 'O\'S': 'BAL', 'BAL': 'BAL',
    'BOSTON RED SOX': 'BOS', 'BOSTON': 'BOS', 'RED SOX': 'BOS', 'SOX': 'BOS', 'BOS': 'BOS',
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
    'OAKLAND ATHLETICS': 'OAK', 'OAKLAND': 'OAK', 'ATHLETICS': 'OAK', 'A\'S': 'OAK', 'OAK': 'OAK',
    'PHILADELPHIA PHILLIES': 'PHI', 'PHILADELPHIA': 'PHI', 'PHILLIES': 'PHI', 'PHI': 'PHI',
    'PITTSBURGH PIRATES': 'PIT', 'PITTSBURGH': 'PIT', 'PIRATES': 'PIT', 'BUCS': 'PIT', 'PIT': 'PIT',
    'SAN DIEGO PADRES': 'SD', 'SAN DIEGO': 'SD', 'PADRES': 'SD', 'SD': 'SD',
    'SAN FRANCISCO GIANTS': 'SF', 'SAN FRANCISCO': 'SF', 'GIANTS': 'SF', 'SF': 'SF',
    'SEATTLE MARINERS': 'SEA', 'SEATTLE': 'SEA', 'MARINERS': 'SEA', 'SEA': 'SEA',
    'ST. LOUIS CARDINALS': 'STL', 'ST LOUIS CARDINALS': 'STL', 'ST LOUIS': 'STL', 'ST. LOUIS': 'STL', 'CARDINALS': 'STL', 'STL': 'STL',
    'TAMPA BAY RAYS': 'TB', 'TAMPA BAY': 'TB', 'RAYS': 'TB', 'TB': 'TB',
    'TEXAS RANGERS': 'TEX', 'TEXAS': 'TEX', 'RANGERS': 'TEX', 'TEX': 'TEX',
    'TORONTO BLUE JAYS': 'TOR', 'TORONTO': 'TOR', 'BLUE JAYS': 'TOR', 'TOR': 'TOR',
    'WASHINGTON NATIONALS': 'WAS', 'WASHINGTON': 'WAS', 'NATIONALS': 'WAS', 'WAS': 'WAS',

    # NHL
    'ANAHEIM DUCKS': 'ANA', 'ANAHEIM': 'ANA', 'DUCKS': 'ANA', 'ANA': 'ANA',
    'ARIZONA COYOTES': 'ARI', 'ARIZONA': 'ARI', 'COYOTES': 'ARI', 'YOTES': 'ARI', 'ARI': 'ARI',
    'BOSTON BRUINS': 'BOS', 'BOSTON': 'BOS', 'BRUINS': 'BOS', 'BOS': 'BOS',
    'BUFFALO SABRES': 'BUF', 'BUFFALO': 'BUF', 'SABRES': 'BUF', 'BUF': 'BUF',
    'CALGARY FLAMES': 'CGY', 'CALGARY': 'CGY', 'FLAMES': 'CGY', 'CGY': 'CGY',
    'CAROLINA HURRICANES': 'CAR', 'CAROLINA': 'CAR', 'HURRICANES': 'CAR', 'CANES': 'CAR', 'CAR': 'CAR',
    'CHICAGO BLACKHAWKS': 'CHI', 'CHICAGO': 'CHI', 'BLACKHAWKS': 'CHI', 'HAWKS': 'CHI', 'CHI': 'CHI',
    'COLORADO AVALANCHE': 'COL', 'COLORADO': 'COL', 'AVALANCHE': 'COL', 'AVS': 'COL', 'COL': 'COL',
    'COLUMBUS BLUE JACKETS': 'CBJ', 'COLUMBUS': 'CBJ', 'BLUE JACKETS': 'CBJ', 'CBJ': 'CBJ',
    'DALLAS STARS': 'DAL', 'DALLAS': 'DAL', 'STARS': 'DAL', 'DAL': 'DAL',
    'DETROIT RED WINGS': 'DET', 'DETROIT': 'DET', 'RED WINGS': 'DET', 'WINGS': 'DET', 'DET': 'DET',
    'EDMONTON OILERS': 'EDM', 'EDMONTON': 'EDM', 'OILERS': 'EDM', 'EDM': 'EDM',
    'FLORIDA PANTHERS': 'FLA', 'FLORIDA': 'FLA', 'PANTHERS': 'FLA', 'FLA': 'FLA',
    'LOS ANGELES KINGS': 'LAK', 'LOS ANGELES K': 'LAK', 'LA KINGS': 'LAK', 'KINGS': 'LAK', 'LAK': 'LAK',
    'MINNESOTA WILD': 'MIN', 'MINNESOTA': 'MIN', 'WILD': 'MIN', 'MIN': 'MIN',
    'MONTREAL CANADIENS': 'MTL', 'MONTREAL': 'MTL', 'CANADIENS': 'MTL', 'HABS': 'MTL', 'MTL': 'MTL',
    'NASHVILLE PREDATORS': 'NSH', 'NASHVILLE': 'NSH', 'PREDATORS': 'NSH', 'PREDS': 'NSH', 'NSH': 'NSH',
    'NEW JERSEY DEVILS': 'NJD', 'NEW JERSEY': 'NJD', 'DEVILS': 'NJD', 'NJD': 'NJD',
    'NEW YORK ISLANDERS': 'NYI', 'NEW YORK I': 'NYI', 'ISLANDERS': 'NYI', 'NYI': 'NYI',
    'NEW YORK RANGERS': 'NYR', 'NEW YORK R': 'NYR', 'RANGERS': 'NYR', 'NYR': 'NYR',
    'OTTAWA SENATORS': 'OTT', 'OTTAWA': 'OTT', 'SENATORS': 'OTT', 'SENS': 'OTT', 'OTT': 'OTT',
    'PHILADELPHIA FLYERS': 'PHI', 'PHILADELPHIA': 'PHI', 'FLYERS': 'PHI', 'PHI': 'PHI',
    'PITTSBURGH PENGUINS': 'PIT', 'PITTSBURGH': 'PIT', 'PENGUINS': 'PIT', 'PENS': 'PIT', 'PIT': 'PIT',
    'SAN JOSE SHARKS': 'SJS', 'SAN JOSE': 'SJS', 'SHARKS': 'SJS', 'SJS': 'SJS',
    'SEATTLE KRAKEN': 'SEA', 'SEATTLE': 'SEA', 'KRAKEN': 'SEA', 'SEA': 'SEA',
    'ST. LOUIS BLUES': 'STL', 'ST LOUIS': 'STL', 'ST. LOUIS': 'STL', 'BLUES': 'STL', 'STL': 'STL',
    'TAMPA BAY LIGHTNING': 'TB', 'TAMPA BAY': 'TB', 'LIGHTNING': 'TB', 'BOLTS': 'TB', 'TB': 'TB',
    'TORONTO MAPLE LEAFS': 'TOR', 'TORONTO': 'TOR', 'MAPLE LEAFS': 'TOR', 'LEAFS': 'TOR', 'TOR': 'TOR',
    'VANCOUVER CANUCKS': 'VAN', 'VANCOUVER': 'VAN', 'CANUCKS': 'VAN', 'VAN': 'VAN',
    'VEGAS GOLDEN KNIGHTS': 'VGK', 'VEGAS': 'VGK', 'GOLDEN KNIGHTS': 'VGK', 'KNIGHTS': 'VGK', 'VGK': 'VGK',
    'WASHINGTON CAPITALS': 'WAS', 'WASHINGTON': 'WAS', 'CAPITALS': 'WAS', 'CAPS': 'WAS', 'WAS': 'WAS',
    'WINNIPEG JETS': 'WPG', 'WINNIPEG': 'WPG', 'JETS': 'WPG', 'WPG': 'WPG',

    # MLS
    'ATLANTA UNITED': 'ATL', 'ATLANTA': 'ATL', 'UNITED': 'ATL', 'ATL UTD': 'ATL', 'ATL': 'ATL',
    'AUSTIN FC': 'ATX', 'AUSTIN': 'ATX', 'AFC': 'ATX', 'ATX': 'ATX',
    'CF MONTREAL': 'MTL', 'MONTREAL': 'MTL', 'CFM': 'MTL', 'IMPACT': 'MTL', 'MTL': 'MTL',
    'CHARLOTTE FC': 'CLT', 'CHARLOTTE': 'CLT', 'CFC': 'CLT', 'CLT': 'CLT',
    'CHICAGO FIRE': 'CHI', 'CHICAGO': 'CHI', 'FIRE': 'CHI', 'CF97': 'CHI', 'CHI': 'CHI',
    'FC CINCINNATI': 'CIN', 'CINCINNATI': 'CIN', 'FCC': 'CIN', 'CIN': 'CIN',
    'COLORADO RAPIDS': 'COL', 'COLORADO': 'COL', 'RAPIDS': 'COL', 'COL': 'COL',
    'COLUMBUS CREW': 'CLB', 'COLUMBUS': 'CLB', 'CREW': 'CLB', 'CLB': 'CLB',
    'DC UNITED': 'DC', 'DCU': 'DC', 'DC UNITED': 'DC', 'DC': 'DC',
    'FC DALLAS': 'DAL', 'DALLAS': 'DAL', 'FCD': 'DAL', 'DAL': 'DAL',
    'HOUSTON DYNAMO': 'HOU', 'HOUSTON': 'HOU', 'DYNAMO': 'HOU', 'HOU': 'HOU',
    'SPORTING KANSAS CITY': 'SKC', 'KANSAS CITY': 'SKC', 'SKC': 'SKC', 'SPORTING KC': 'SKC', 'SKC': 'SKC',
    'LA GALAXY': 'LAG', 'LA GALAXY': 'LAG', 'GALAXY': 'LAG', 'LAG': 'LAG',
    'LOS ANGELES FC': 'LAFC', 'LAFC': 'LAFC', 'LOS ANGELES F': 'LAFC', 'LA FC': 'LAFC', 'LAFC': 'LAFC',
    'INTER MIAMI': 'MIA', 'MIAMI': 'MIA', 'IMCF': 'MIA', 'MIA': 'MIA',
    'MINNESOTA UNITED': 'MIN', 'MINNESOTA': 'MIN', 'UNITED': 'MIN', 'MNUFC': 'MIN', 'MIN': 'MIN',
    'NASHVILLE SC': 'NSH', 'NASHVILLE': 'NSH', 'NSC': 'NSH', 'NSH': 'NSH',
    'NEW ENGLAND REVOLUTION': 'NE', 'NEW ENGLAND': 'NE', 'REVOLUTION': 'NE', 'REVS': 'NE', 'NE': 'NE',
    'NEW YORK CITY FC': 'NYC', 'NEW YORK C': 'NYC', 'NYCFC': 'NYC', 'NYC': 'NYC',
    'NEW YORK RED BULLS': 'NYRB', 'NEW YORK R': 'NYRB', 'RED BULLS': 'NYRB', 'NYRB': 'NYRB',
    'ORLANDO CITY SC': 'ORL', 'ORLANDO CITY': 'ORL', 'ORLANDO': 'ORL', 'LIONS': 'ORL', 'ORL': 'ORL',
    'PHILADELPHIA UNION': 'PHI', 'PHILADELPHIA': 'PHI', 'UNION': 'PHI', 'PHI': 'PHI',
    'PORTLAND TIMBERS': 'POR', 'PORTLAND': 'POR', 'TIMBERS': 'POR', 'POR': 'POR',
    'REAL SALT LAKE': 'RSL', 'SALT LAKE': 'RSL', 'REAL SL': 'RSL', 'RSL': 'RSL',
    'SAN JOSE EARTHQUAKES': 'SJ', 'SAN JOSE': 'SJ', 'EARTHQUAKES': 'SJ', 'QUAKES': 'SJ', 'SJ': 'SJ',
    'SEATTLE SOUNDERS': 'SEA', 'SEATTLE': 'SEA', 'SOUNDERS': 'SEA', 'SEA': 'SEA',
    'ST. LOUIS CITY SC': 'STL', 'ST. LOUIS': 'STL', 'ST LOUIS': 'STL', 'CITY SC': 'STL', 'STL': 'STL',
    'TORONTO FC': 'TOR', 'TORONTO': 'TOR', 'TFC': 'TOR', 'TOR': 'TOR',
    'VANCOUVER WHITECAPS': 'VAN', 'VANCOUVER': 'VAN', 'WHITECAPS': 'VAN', 'VAN': 'VAN',
}
