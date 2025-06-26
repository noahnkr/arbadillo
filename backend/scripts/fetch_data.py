import json
import argparse
import requests
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright
from ..common.constants.urls import ESPNBET_URLS, ESPNBET_AUTH_TOKEN

def fetch_data(url, headers=None, params=None, method='requests', context=None, page=None) -> dict:
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
        if not context:
            raise ValueError('Playwright context is required for method=`playwright_request`')
        response = context.request.get(url, headers=final_headers, params=params)
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
        raise ValueError(f'Unknown method `{method}`')

def fetch_espnbet_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        base_url = ESPNBET_URLS['base']
        event_id = '94593739-217b-4d1f-b656-394a252c5655'
        league_url = f'/sport/baseball/organization/united-states/competition/mlb'#/event/{event_id}/section/sgp'
        cookies = context.cookies()
        cookie_header = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
        headers = {
            'origin': 'https://thescore.bet',
            'referer': 'https://thescore.bet',
            'cookie': cookie_header,
            'x-anonymous-authorization': ESPNBET_AUTH_TOKEN,
        }
        variables = {
            'canonicalUrl': league_url,
            'oddsFormat': 'AMERICAN',
            'includeRichEvent': True,
            'includeRecommendedProps': True,
            'includeSectionDefaultField': True,
            'includeTableMarketCard': True,
            'pageType': 'PAGE',
        }
        params = {
            'operationName': 'Marketplace',
            'variables': json.dumps(variables),
        }

        data = fetch_data(base_url, headers=headers, params=params, method='page_evaluate_fetch', page=page)

        with open('espnbet-schedule-data.json', 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == '__main__':
    fetch_espnbet_data()