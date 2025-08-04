import pprint
from datetime import datetime
from datetime import timezone
from django.core.management import BaseCommand
from django.utils.timezone import make_aware
from sports.queries import (
    get_team_season_stats, get_player_season_stats,
    get_team_event_stats, get_player_event_stats,
    get_team_opponent_season_stats
)

class Command(BaseCommand):
    help = 'Get stored team or players stats by season'

    def add_arguments(self, parser):
        parser.add_argument('-l', '--league', type=str, required=True)
        parser.add_argument('-s', '--season', type=int, required=True)
        parser.add_argument('-t', '--team', type=str, required=True)

        parser.add_argument('-p', '--player', type=str)
        parser.add_argument('-o', '--opponent', action='store_true')

        parser.add_argument('-e', '--event', type=str)
        parser.add_argument('-b', '--before', type=str, help='Date in the format: YYYY-MM-DD')
        parser.add_argument('-a', '--after', type=str, help='Date in the format: YYYY-MM-DD')

    
    def handle(self, *args, **options):
        league = options['league']
        season = options['season']
        team = options['team']
        player = options['player']
        opponent = options['opponent']

        event = options['event']
        before = options['before']
        after = options['after']

        if event and (before or after):
            raise ValueError("You cannot provide both --event and --before/--after filters")

        if before:
            before = datetime.strptime(before, '%Y-%m-%d')
            before = make_aware(before, timezone.utc)

        if after:
            after = datetime.strptime(after, '%Y-%m-%d').replace()
            after = make_aware(after, timezone.utc)

        if event:
            stats = get_team_event_stats(
                league, season, team, event
            ) if team else get_player_event_stats(
                league, season, player, event
            )

        elif opponent:
            stats = get_team_opponent_season_stats(
                league, season, team, before, after
            ) if team else {}

        else:
            stats = get_team_season_stats(
                league, season, team, before, after
            ) if team else get_player_season_stats(
                league, season, team, player, before, after
            )
        
        pprint.pprint(stats)