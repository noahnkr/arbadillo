from abc import ABC, abstractmethod
from django.conf import settings
from redis import Redis
import requests

class SportsbookClient(ABC):

    def __init__(self, league):
        self.league = league
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )


    def fetch_data(self, url, headers=None, params=None, session=None):
        default_headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		}
        final_headers = { **default_headers, **(headers or {}) }

        if session:
            response = session.context.request.get(url, headers=final_headers, params=params)
            return response.json()
        else:
            response = requests.get(url, headers=final_headers, params=params)
            response.raise_for_status()
            return response.json()


    @abstractmethod
    def parse_schedule(self):
        pass


    @abstractmethod
    def parse_odds(self):
        pass
    