from abc import ABC, abstractmethod
from redis import Redis
from settings import REDIS_HOST, REDIS_PORT

class SportsbookClient(ABC):

    def __init__(self, league=None):
        self.league = league
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
    

    @abstractmethod
    def parse_schedule():
        pass


    @abstractmethod
    def parse_odds():
        pass
    