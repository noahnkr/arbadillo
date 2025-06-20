import logging
import requests

from abc import ABC, abstractmethod
from django.conf import settings
from urllib.parse import urlencode
from redis import Redis

class SportsbookClient(ABC):

    def __init__(self, name, league):
        self.name = name
        self.league = league
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.logger = logging.getLogger(f'scraper.apiclients.{self.name}')


    def fetch_data(self, url, headers=None, params=None, method='requests', session=None, page=None):
        default_headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
		}
        final_headers = { **default_headers, **(headers or {}) }

        if method == 'requests':
            response = requests.get(url, headers=final_headers, params=params)
            response.raise_for_status()
            return response.json()
        elif method == 'playwright_request':
            if not session:
                raise ValueError('Playwright session is required for method=`playwright_request`')
            response = session.context.request.get(url, headers=final_headers, params=params)
            return response.json()
        elif method == 'page_evaluate_fetch':
            if not page:
                raise ValueError('Playwright page is required for method=`page_evaluate_fetch`')

            query_str = '?' + urlencode(params or {}, doseq=True)
            js  = f"""
                async () => {{
                    const res = await fetch("{url}{query_str}", {{
                        method: 'GET',
                        headers: {final_headers}
                    }});
                    return await res.json();
                }}
            """
            return page.evaluate(js)
        
        else:
            raise ValueError(f'Unknown method: {method}')


    @abstractmethod
    def parse_schedule(self):
        pass


    @abstractmethod
    def parse_primary_odds(self, status):
        pass


    @abstractmethod
    def parse_props(self, status):
        pass