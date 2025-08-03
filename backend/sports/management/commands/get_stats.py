from django.core.management import BaseCommand
from sports.models import TeamStat, PlayerStat
from sports.queries import get_event_stats, get_season_stats_aggregate, get_season_stats

class Command(BaseCommand):
    help = 'Get stored team or players stats by season'

    def add_arguments(self, parser):
        parser.add_argument('-l', '--league', type=str, required=True)
        parser.add_argument('-s', '--season', type=int, required=True)
        parser.add_argument('-e', '--event', type=str)
        parser.add_argument('-a', '--aggregate', action='store_true')

        team_or_player = parser.add_mutually_exclusive_group(required=True)
        team_or_player.add_argument('-t', '--team', type=str)
        team_or_player.add_argument('-p', '--player', type=str)

    
    def handle(self, *args, **options):
        league = options['league']
        season = options['season']
        event = options['event']

        team = options['team']
        player = options['player']

        aggregate = options['aggregate']

        model, key_field, entity_key = (TeamStat, 'team_key', team) if team else (PlayerStat, 'player_key', player)
        params = [model, league, season, key_field, entity_key]

        if event:
            print(get_event_stats(*params, event))
        elif aggregate:
            print(get_season_stats_aggregate(*params))
        else:
            print(get_season_stats(*params))
