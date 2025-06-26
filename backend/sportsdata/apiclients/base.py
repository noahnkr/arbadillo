from abc import ABC, abstractmethod
from django.conf import settings
from redis import Redis

import logging

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