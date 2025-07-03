import argparse
import json
import requests
from urllib.parse import urlencode
from common.utils.sportsbook_helpers import get_sport_from_league
from common.utils.client import get_browser
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


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
        return response

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


def fetch_fanduel_data(output, league=None, event_id=None):
    browser = get_browser()
    context = browser.new_context()

    url = 'https://sbapi.il.sportsbook.fanduel.com/api'
    if league:
        url += '/content-managed-page'
        params = {
            'page': 'CUSTOM',
            'customPageId': league
        }
    else:
        url += '/event-page'
        params = { 'eventId': event_id }


    headers = {
        'origin': 'https://sportsbook.fanduel.com',
        'referer': 'https://sportsbook.fanduel.com',
    }
    final_params = {
        '_ak': 'FhMFpcPWXMeyZxOx',
        'timezone': 'America%2FChicago',
        **params
    }
    data = fetch_data(url, headers=headers, params=final_params, method='playwright_request', context=context)

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_espnbet_data(output, league=None, event_id=None):
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

    with open('data/espnbet_data.json', 'w') as f:
        json.dump(data, f, indent=2)

def fetch_draftkings_data(output, league=None, event_id=None):
    browser = get_browser()
    context = browser.new_context()
    event_id = 32479983
    url = f'https://sportsbook-nash.draftkings.com/api/sportscontent/dkusil/v1/events/{event_id}/categories'
    headers = {
        'origin': 'https://sportsbook.draftkings.com',
        'referer': 'https://sportsbook.draftkings.com',
    }
    data = fetch_data(url, headers=headers, method='playwright_request', context=context)

    with open('data/draftkings_data.json', 'w') as f:
        json.dump(data, f, indent=2)


def fetch_betrivers_data(output, league=None, event_id=None):
    event_id = 1022036311
    url = 'https://il.betrivers.com/api/service/sportsbook/offering/listview/details'
    headers = {
        'origin': 'https://betrivers.com',
        'referer': 'https://betrivers.com'
    }
    params = {
        'eventId': event_id,
        'cageCode': 847,
    }
    data = fetch_data(url, headers=headers, params=params)

    with open('data/betrivers_data.json', 'w') as f:
        json.dump(data, f, indent=2)


def fetch_betmgm_data(output, league, event_id):
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        url = 'https://www.ia.betmgm.com/en/sports/events/chicago-white-sox-at-los-angeles-dodgers-17734647?tab=score'
        page.goto(url)
        page.wait_for_selector('div.six-pack-container')

        with open('data/betmgm_data.html', 'w', encoding='utf-8') as f:
            f.write(page.content())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sportsbook', help='Name of the sportsbook to be fetched from')
    parser.add_argument('-o', '--output', type=str, help='The file where the output data will be written')

    league_or_event = parser.add_mutually_exclusive_group(required=True)
    league_or_event.add_argument('-e', '--event', type=int, help='The id of the event whose data will be fetched')
    league_or_event.add_argument('-l', '--league', type=str, help='The league whose schedule data will be fetched')

    args = parser.parse_args()

    if not args.output:
        if args.event:
            args.output = f'{args.sportsbook}_{args.event.replace(":", '_')}_data'
        elif args.league:
            args.output = f'{args.sportsbook}_{args.league}_data'

    match args.sportsbook:
        case 'fanduel': fetch_fanduel_data(args.output, league=args.league, event_id=args.event)
        case 'draftkings': fetch_draftkings_data(args.output, league=args.league, event_id=args.event)
        case 'espnbet': fetch_espnbet_data(args.output, league=args.league, event_id=args.event)
        case 'betrivers': fetch_betrivers_data(args.output, league=args.league, event_id=args.event)
        case 'betmgm': fetch_betmgm_data(output=args.output, league=args.league, event_id=args.event)
        case _: print(f'Unknown sportsbook `{args.sportsbook}`')
