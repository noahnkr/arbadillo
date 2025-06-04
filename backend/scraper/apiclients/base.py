from abc import ABC, abstractmethod
from redis import Redis
import requests
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

class SportsbookClient(ABC):

    def __init__(self, league=None):
        self.league = league
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


    @abstractmethod
    def fetch_data(self, url):
        pass


    @abstractmethod
    def parse_schedule(self):
        pass


    @abstractmethod
    def parse_odds(self):
        pass
    