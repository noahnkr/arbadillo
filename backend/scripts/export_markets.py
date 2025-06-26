import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from oddsdata.tasks import collect_espn_schedule, collect_sportsbook_schedule, export_all_client_markets

collect_espn_schedule.delay()
collect_sportsbook_schedule.delay()
export_all_client_markets.delay({
    'mlb': [
        'mlb:2025-06-23:texas-rangers@baltimore-orioles',
    ]
})
