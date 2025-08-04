from collections import defaultdict
from django.db.models import Model
from sports.models import Event, TeamStat, PlayerStat
from common.constants.aliases import REVERSE_STATS_LOOKUP, EFFICIENCY_ALIASES

def _get_stats(model: Model, league: str, season: int, key_field: str, entity_key: str, event_key: str = None):
    """Generic function to fetch stats for a team or player."""
    filters = { key_field: entity_key }

    if event_key:
        filters['event_key'] = event_key
    else:
        filters['event_key__in'] = _get_events(league, season).values_list('event_key', flat=True)

    return model.objects.filter(**filters).values()


def _get_events(league: str, season: int, team_key: str = None):
    filters = { 'league': league, 'season': season }
    if team_key:
        events = Event.objects.filter(**filters, away_team=team_key) | Event.objects.filter(**filters, home_team=team_key)
    else:
        events = Event.objects.filter(**filters)

    return events


def _aggregate_season_stats(league: str, season_stats: list):
    stat_sums = defaultdict(float)
    stat_counts = defaultdict(int)

    for stat in season_stats:
        stat_sums[stat['stat_name']] += stat['value']
        stat_counts[stat['stat_name']] += 1

    aggregate = {}

    # Compute rate for efficiency stats
    for conv, att in EFFICIENCY_ALIASES.values():
        if conv in stat_sums and att in stat_sums:
            conv_sum = stat_sums.get(conv, 0)
            att_sum = stat_sums.get(att, 1)
            eff_stat_name, _ = REVERSE_STATS_LOOKUP[(league, (conv, att))]
            aggregate[eff_stat_name] = round(conv_sum / att_sum, 3)

    # Compute per-game average for other stats
    excluded = {v for pair in EFFICIENCY_ALIASES.values() for v in pair}
    for stat, stat_sum in stat_sums.items():
        if stat not in excluded:
            aggregate[stat] = round(stat_sum / stat_counts[stat], 3)
    
    return aggregate


def get_team_event_stats(league: str, season: str, team_key: str, event_key: str):
    stats = _get_stats(
        model=TeamStat, 
        league=league,
        season=season, 
        key_field='team_key',
        entity_key=team_key,
        event_key=event_key
    )
    return { s['stat_name']: s['value'] for s in stats }


def get_player_event_stats(league: str, season: str, player_key: str, event_key: str):
    stats = _get_stats(
        model=PlayerStat, 
        league=league,
        season=season, 
        key_field='player_key',
        entity_key=player_key,
        event_key=event_key
    )
    return { s['stat_name']: s['value'] for s in stats }


def get_team_season_stats(league: str, season: str, team_key: str):
    stats = _get_stats(
        model=TeamStat, 
        league=league,
        season=season, 
        key_field='team_key',
        entity_key=team_key,
    )
    return _aggregate_season_stats(league, stats)

 
def get_player_season_stats(league: str, season: str, player_key: str):
    stats = _get_stats(
        model=TeamStat, 
        league=league,
        season=season, 
        key_field='player_key',
        entity_key=player_key,
    )
    return _aggregate_season_stats(league, stats)


def get_team_opponent_season_stats(league: str, season: str, team_key: str):
    events = _get_events(league, season, team_key)
    event_opponents = {}

    for event in events:
        if event.away_team == team_key:
            event_opponents[event.event_key] = event.home_team
        else:
            event_opponents[event.event_key] = event.away_team

    opponent_stats = []
    for event_key, opponent in event_opponents.items():
        stats = _get_stats(
            model=TeamStat,
            league=league,
            season=season,
            key_field='team_key',
            entity_key=opponent,
            event_key=event_key
        )
        opponent_stats.extend(stats)
    
    return _aggregate_season_stats(league, opponent_stats)