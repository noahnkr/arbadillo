from django.core.management import BaseCommand
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
        parser.add_argument('-e', '--event', type=str)
        parser.add_argument('-o', '--opponent', action='store_true')

        team_or_player = parser.add_mutually_exclusive_group(required=True)
        team_or_player.add_argument('-t', '--team', type=str)
        team_or_player.add_argument('-p', '--player', type=str)

    
    def handle(self, *args, **options):
        league = options['league']
        season = options['season']
        event = options['event']
        opponent = options['opponent']

        team = options['team']
        player = options['player']

        if event:
            stats = get_team_event_stats(
                league, season, team, event
            ) if team else get_player_event_stats(
                league, season, player, event
            )
        elif opponent:
            stats = get_team_opponent_season_stats(
                league, season, team
            ) if team else {}
        else:
            stats = get_team_season_stats(
                league, season, team
            ) if team else get_player_season_stats(
                league, season, player
            )
        
        print(stats)