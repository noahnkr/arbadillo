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


    def fetch_data(self, url, headers=None, params=None):
        _headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		} or headers
        _params = {} or params
        response = requests.get(url, headers=_headers, params=_params)
        response.raise_for_status()
        data = response.json()
        return data


    @abstractmethod
    def parse_schedule(self):
        pass


    @abstractmethod
    def parse_odds(self):
        pass
    