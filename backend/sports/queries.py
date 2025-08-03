from collections import defaultdict
from django.db.models import Model
from sports.models import Event
from common.constants.aliases import REVERSE_STATS_LOOKUP, EFFICIENCY_ALIASES

def _get_stats(model: Model, league: str, season: int, key_field: str, entity_key: str, event_key: str = None):
    """Generic function to fetch stats for a team or player."""
    filters = { key_field: entity_key }

    if event_key:
        filters['event_key'] = event_key
    else:
        filters['event_key__in'] = Event.objects.filter(
            league=league,
            season=season
        ).values_list('event_key', flat=True)

    return model.objects.filter(**filters).values()


def get_event_stats(model: Model, league: str, season: str, key_field: str, entity_key: str, event_key: str):
    stats = _get_stats(model, league, season, key_field, entity_key, event_key).values('stat_name', 'value')
    return { s['stat_name']: s['value'] for s in stats }


def get_season_stats(model: Model, league: str, season: str, key_field: str, entity_key: str):
    stats = _get_stats(model, league, season, key_field, entity_key)

    stat_sums = defaultdict(float)
    stat_counts = defaultdict(int)

    for stat in stats:
        stat_sums[stat['stat_name']] += stat['value']
        stat_counts[stat['stat_name']] += 1

    season_stats = {}

    # Compute rate for efficiency stats
    for conv, att in EFFICIENCY_ALIASES.values():
        if conv in stat_sums and att in stat_sums:
            conv_sum = stat_sums.get(conv, 0)
            att_sum = stat_sums.get(att, 1)
            eff_stat_name, _ = REVERSE_STATS_LOOKUP[(league, (conv, att))]
            season_stats[eff_stat_name] = round(conv_sum / att_sum, 3)

    # Compute season-level net or average for each respective stat type
    excluded = {v for pair in EFFICIENCY_ALIASES.values() for v in pair}
    for stat, stat_sum in stat_sums.items():
        _, stat_type = REVERSE_STATS_LOOKUP[(league, stat)]
        if stat not in excluded:
            if stat_type == 'volume':
                season_stats[f'net_{stat}'] = stat_sum
            elif stat_type in {'rate', 'time'}:
                season_stats[f'avg_{stat}'] = round(stat_sum / stat_counts[stat], 3)

    return season_stats


def get_season_stats_aggregate(model: Model, league: str, season: str, key_field: str, entity_key: str):
    stats = _get_stats(model, league, season, key_field, entity_key)

    stat_sums = defaultdict(float)
    stat_counts = defaultdict(int)

    for stat in stats:
        stat_sums[stat['stat_name']] += stat['value']
        stat_counts[stat['stat_name']] += 1

    season_aggregate = {}

    # Compute rate for efficiency stats
    for conv, att in EFFICIENCY_ALIASES.values():
        if conv in stat_sums and att in stat_sums:
            conv_sum = stat_sums.get(conv, 0)
            att_sum = stat_sums.get(att, 1)
            eff_stat_name, _ = REVERSE_STATS_LOOKUP[(league, (conv, att))]
            season_aggregate[eff_stat_name] = round(conv_sum / att_sum, 3)

    # Compute per-game average for other stats
    excluded = {v for pair in EFFICIENCY_ALIASES.values() for v in pair}
    for stat, stat_sum in stat_sums.items():
        if stat not in excluded:
            season_aggregate[f'avg_{stat}'] = round(stat_sum / stat_counts[stat], 3)
    
    return season_aggregate
