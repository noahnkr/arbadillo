from common.constants.aliases import MARKET_TO_STATS
from sports.queries import (
    get_team_season_stats, get_player_season_stats,
    get_team_opponent_season_stats
)

def build_features_for_market(
        market, 
        league, 
        season, 
        team_key=None, 
        opponent_key=None, 
        player_key=None,
        before_date=None,
        after_date=None):

    config = MARKET_TO_STATS[league][market]
    required_stats = config['stats']
    context = config['context']

    feature_vector = {}

    if context == 'team':
        self_stats = get_team_season_stats(league, season, team_key, before_date, after_date)
        opp_stats = get_team_season_stats(league, season, opponent_key, before_date, after_date)
        self_opp_stats = get_team_opponent_season_stats(league, season, team_key, before_date, after_date)
        opp_opp_stats = get_team_opponent_season_stats(league, season, opponent_key, before_date, after_date)

        for stat in required_stats:
            x = self_stats[stat]
            y = opp_stats[stat]
            x_opp_allowed = opp_opp_stats[stat]
            y_opp_allowed = self_opp_stats[stat]

            feature_vector[f'{stat}_self'] = x
            feature_vector[f'{stat}_opp'] = y
            feature_vector[f'{stat}_diff'] = x - y
            feature_vector[f'{stat}_vs_opp_allowed'] = x - x_opp_allowed
            feature_vector[f'{stat}_vs_self_allowed'] = y - y_opp_allowed
    else:
        pass

    return feature_vector
