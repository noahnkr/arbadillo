import logging

from abc import ABC, abstractmethod
from django.conf import settings
from redis import Redis

from sportsdata.tasks import batch_upsert_events


class SportsClient(ABC):
    
    def __init__(self, name):
        self.name = name
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.logger = logging.getLogger(f'sportsdata.apiclients.{self.name}')
    

    def upsert_events(self, event_data):
        if not event_data:
            self.logger.info(f'no new events to upsert ({self.league})')
        else:
            self.logger.info(f'upserting {len(event_data)} events ({self.league})')
            batch_upsert_events.delay(event_data)
