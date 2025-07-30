import time
import random

from django.core.management import BaseCommand
from django.utils.timezone import is_naive, make_aware
from datetime import timezone
from sports.clients.espn import ESPNClient
from sports.models import (
    Event, EventResult, TeamStat, PlayerStat
)
from common.utils.sportsbook_helpers import get_sport_from_league

class Command(BaseCommand):
    help = 'Fetch historical or weekly ESPN stats'

    def add_arguments(self, parser):
        parser.add_argument('--league', type=str, required=True)
        parser.add_argument('--season', type=int, default=2024)
        parser.add_argument('--teams', action='store_true')
        parser.add_argument('--players', action='store_true')
    
    def handle(self, *args, **options):
        league = options['league']
        season = options['season']
        get_teams = options['teams']
        get_players = options['players']

        sport = get_sport_from_league(league)
        client = ESPNClient(sport, league)

        if get_teams:
            events = set()
            event_results = set()
            team_stats = set()

            teams, _ = client.get_teams()
            for team in teams:
                team_events = client.get_events(team.team_key, season)
                for event in team_events:
                    events.add(event)
                    result, away_stats, home_stats = client.get_event_stats(event.event_key)
                    event_results.add(result)
                    for stat in away_stats + home_stats:
                        team_stats.add(stat)
            
            Event.objects.bulk_create(
                [
                    Event(
                        start_time=make_aware(e.start_time, timezone.utc) if is_naive(e.start_time) else e.start_time,
                        **{k: v for k,v in e.to_dict().items() if k != 'start_time'}
                    )
                    for e in events
                ],
                ignore_conflicts=True
            )
            EventResult.objects.bulk_create(
                [
                    EventResult(**r.to_dict())
                    for r in event_results
                ],
                ignore_conflicts=True
            )
            TeamStat.objects.bulk_create(
                [
                    TeamStat(**t.to_dict())
                    for t in team_stats
                ],
                ignore_conflicts=True
            )
        
        if get_players:
            player_stats = set()

            teams, _ = client.get_teams()
            for team in teams:
                players, _ = client.get_players(team.team_key)
                for player in players:
                    for stat in client.get_player_stats(player.player_key, season):
                        player_stats.add(stat)
            
            PlayerStat.objects.bulk_create(
                [
                    PlayerStat(**p.to_dict())
                    for p in player_stats
                ],
                ignore_conflicts=True
            )