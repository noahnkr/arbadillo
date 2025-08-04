from datetime import datetime
from collections import defaultdict
from django.db.models import Model
from sports.models import Event, TeamStat, PlayerStat
from common.constants.aliases import REVERSE_STATS_LOOKUP, EFFICIENCY_ALIASES

def _get_stats(
        model: Model, 
        league: str, 
        season: int, 
        key_field: str, 
        entity_key: str, 
        event_keys: list = None):
    """Generic function to fetch stats for a team or player."""
    filters = { key_field: entity_key }

    if event_keys:
        filters['event_key__in'] = event_keys
    else:
        filters['event_key__in'] = get_events(league, season).values_list('event_key', flat=True)

    return model.objects.filter(**filters).values()


def _aggregate_stats(league: str, stats: list):
    stat_sums = defaultdict(float)
    stat_counts = defaultdict(int)

    for stat in stats:
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


def get_events(
        league: str, 
        season: int,
        team_key: str = None,
        before_date: datetime = None, 
        after_date: datetime = None):
    filters = { 'league': league, 'season': season }

    if before_date:
        filters['start_time__lt'] = before_date
    if after_date:
        filters['start_time__gte'] = after_date

    if team_key:
        events = Event.objects.filter(**filters, away_team=team_key) | Event.objects.filter(**filters, home_team=team_key)
    else:
        events = Event.objects.filter(**filters)

    return events


def get_team_event_stats(league: str, season: int, team_key: str, event_key: str):
    stats = _get_stats(
        model=TeamStat, 
        league=league,
        season=season, 
        key_field='team_key',
        entity_key=team_key,
        event_keys=[event_key]
    )
    return { s['stat_name']: s['value'] for s in stats }


def get_player_event_stats(league: str, season: int, player_key: str, event_key: str):
    stats = _get_stats(
        model=PlayerStat, 
        league=league,
        season=season, 
        key_field='player_key',
        entity_key=player_key,
        event_keys=[event_key]
    )
    return { s['stat_name']: s['value'] for s in stats }


def get_team_season_stats(
        league: str,
        season: int,
        team_key: str,
        before_date: datetime = None,
        after_date: datetime = None):

    if before_date or after_date:
        events = get_events(
            league, season, team_key, 
            before_date=before_date,
            after_date=after_date
        ).values_list('event_key', flat=True)
    else:
        events = None

    stats = _get_stats(
        model=TeamStat, 
        league=league,
        season=season, 
        key_field='team_key',
        entity_key=team_key,
        event_keys=events
    )
    return _aggregate_stats(league, stats)

 
def get_player_season_stats(
        league: str,
        season: int,
        player_key: str,
        before_date: datetime = None,
        after_date: datetime = None):

    if before_date or after_date:
        events = get_events(
            league, season, None,  # No need for team_key
            before_date=before_date,
            after_date=after_date
        ).values_list('event_key', flat=True)
    else:
        events = None

    stats = _get_stats(
        model=PlayerStat, 
        league=league,
        season=season, 
        key_field='player_key',
        entity_key=player_key,
        event_keys=events
    )
    return _aggregate_stats(league, stats)


def get_team_opponent_season_stats(
        league: str, 
        season: int, 
        team_key: str, 
        before_date: datetime = None,
        after_date: datetime = None):

    events = get_events(
        league, season, team_key, 
        before_date=before_date, 
        after_date=after_date
    )

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
            event_keys=[event_key]
        )
        opponent_stats.extend(stats)
    
    return _aggregate_stats(league, opponent_stats)