import json
import requests
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright
from common.utils.client import get_browser

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


def fetch_fanduel_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
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

        with open('data/fanduel-schedule-data.json', 'w') as f:
            json.dump(data, f, indent=2)


def fetch_espnbet_data():
    browser = get_browser()
    context = browser.new_context()
    page = context.new_page()

    url = 'https://sportsbook-tsb.ca-default.thescore.bet/graphql/persisted_queries/a10930c7eba26a588efb729298364a07aa4cdcd40d456dd061dee1355bfb8e86'
    path = '/sport/baseball/organization/united-states/competition/mlb/event/50c5f852-cb18-4139-a38b-32ccd8278a43'

    headers = {
        'origin': 'https://thescore.bet',
        'referer': 'https://thescore.bet',
        'x-anonymous-authorization': 'Bearer eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYifQ.I90O69ULGH1ehEsPEpXv88G-0YYSnvlTKb2NL-38EvZU66NSOWsxWZXkOg4QpbAuyooucKAhMYmSwQmIJ2iEJ0U-NZP7upAyI1-riFZM26h5i5i58cXGDFqTYqU3sg6imTgsh0CFo_LsSwMAzcUAubpeCXH_TaPtHneme2jjPoYvo-fwt_OanVcMVqQnVwbd7rQktGDM-NBYQO2DQdegCA_n9lyQKeJHgoYgXnN426od2-MCVpc--E7fwz1-0fQo4eeaI0BEi3Oxaykxc3aPD4dtJA4CpGL9VKxe-DCa_A-e3TYGrzKRbtUgjlyHNAXtjP8XF6PBR3Dk2FG_VKyBZuZwQdSwtNT5cbi6OjSa-n32ArCXueqMygz_51Fc-kP34sU2mxC_XoN9bvSOXIu3iyLXZfVdGZOpRNwAMxH0yhmRx0KB89Vr9nSwbTAyqX693bnkIeNoaASK_iuptNXcVsg6HyE93xceTrT7ALmQrZW5Z0V2brTWNnhdgypRYy9fMxYb6Y0T3nbeuNvMSHtQUj5H9ZERJuhDk4oe7Eu6s-U2bfjSO9R2yxUs6i-VS58cqUPnK0HxSzSFiwVUYRu7x6ZLEW7ZXL5vgYe4A13uTc-CTyoJiIHi_xuHcPfUX2pHfXsVa-kcXBls_Bljr4NBNdhEzC3OS28K2H7sD4gv3T8.DAZz4Z6i1ZeSoknKSeNayA.3dlCcWPnwYjTpjirq3ml7b_3Ry_9Y9lev7sDh6yS-Ty_clXkn9ULinDnxVUQQYzIW69HFf7CKO6UmHO1tGgVPNjhCN9_nQbbRrv4GbcnhfHQ7-r6VdsscX7ikwKyGTfYPzHDWzUg6z8uZBd_llb747myH55kt_fpzUNEwd3y530-6NZ1MhZHymIG8htWzf-JvbcmU_ff7V15p6iMHByeSR11aJQ0nAhURlw0fTuvg9N4SSmMWh3I-Wg5YvvrmFq0kmsO71vxuSJABKnp7yG7FQ.LAZPf8A0B73LnIZIn40Fmw'
    }
    variables = {
        'canonicalUrl': path,
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
    data = fetch_data(url, headers=headers, params=params, method='page_evaluate_fetch', page=page)

    with open('data/espnbet-data.json', 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == '__main__':
    fetch_espnbet_data()