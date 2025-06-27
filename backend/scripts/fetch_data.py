import json
import argparse
import requests
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

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
        url = 'https://sbapi.il.sportsbook.fanduel.com/api/content-managed-page?page=CUSTOM&customPageId=mlb'
        headers = {
            'origin': 'https://sportsbook.fanduel.com',
            'referer': 'https://sportsbook.fanduel.com',
        }
        params = {
            '_ak': 'FhMFpcPWXMeyZxOx',
            'timezone': 'America%2FChicago',
        }
        data = fetch_data(url, headers=headers, params=params, method='playwright_request', context=context)

        with open('fanduel-schedule-data.json', 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == '__main__':
    fetch_espnbet_data()