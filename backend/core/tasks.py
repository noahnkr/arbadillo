import logging

from celery import shared_task, group, chord
from sportsdata.tasks import sync_teams, sync_players, sync_schedule
from oddsdata.tasks import scrape_events_for_league, sync_odds
from common.constants.sportsbook_definitions import SPORTSBOOK_CLIENTS, CLIENT_LEAGUES
from common.utils.sportsbook_helpers import get_sport_from_league

logger = logging.getLogger(__name__)

@shared_task(queue='scraping')
def bootstrap_initial_data():
    logger.info('Bootstrapping initial data...')
    chord(
        group(
            sync_teams.s(sport=get_sport_from_league(league), league=league)
            for league in CLIENT_LEAGUES
        ),
        bootstrap_roster_and_schedule.s()
    ).apply_async()

@shared_task(queue='scraping')
def bootstrap_roster_and_schedule(teams_by_league):
    logger.info('Teams synced. Bootstrapping rosters and schedules...')
    roster_tasks = []
    schedule_tasks = []
    
    for teams in teams_by_league:
        if not teams:
            continue
            
        league = teams[0]['league']

        for team in teams:
            roster_tasks.append(
                sync_players.s(
                    sport=get_sport_from_league(league), 
                    league=league,
                    team_id=team['espn_id']
                )
            )
        
        schedule_tasks.append(
            sync_schedule.s(
                sport=get_sport_from_league(league), 
                league=league,
            )
        )

    chord(
        group(roster_tasks + schedule_tasks),
        bootstrap_sportsbook_schedule.si()
    ).apply_async()


@shared_task(queue='scraping')
def bootstrap_sportsbook_schedule():
    # Phase 3: Sync sportsbook schedule to find event ids
    logger.info('ESPN roster and schedule synced. Bootstrapping sportsbook schedule...')
    chord(
        group(
            scrape_events_for_league.s(sportsbook=sportsbook, league=league)
            for sportsbook in SPORTSBOOK_CLIENTS
            for league in CLIENT_LEAGUES
        ),
        bootstrap_sportsbook_odds.si()
    ).apply_async()

@shared_task(queue='scraping')
def bootstrap_sportsbook_odds():
    # Phase 4: Sync upcoming and active sportsbook odds
    logger.info('Sportsbook schedule synced. Bootstrapping sportsbook odds...')
    group(
        sync_odds.s(status='upcoming'),
        sync_odds.s(status='active')
    ).apply_async()