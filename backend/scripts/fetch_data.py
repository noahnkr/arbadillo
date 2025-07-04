import argparse
import json

from urllib.parse import urlencode

from common.utils.sportsbook_helpers import get_sport_from_league
from common.utils.client import init_browser

def fetch_data(url, context, headers=None, params=None, method='request', intercept_query=None):
    default_headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }
    final_headers = { **default_headers, **(headers or {}) }

    encoded_params =  urlencode((params or []), doseq=True)
    query_str = '?' + encoded_params if encoded_params else ''

    final_url = url + query_str
    try:
        if method == 'request':
            response = context.request.get(final_url, headers=final_headers)
            return response.json()

        elif method == 'page_evaluate_fetch':
            page = context.new_page()
            query_str = '?' + urlencode(params or {}, doseq=True)
            js  = f"""
                async () => {{
                    const res = await fetch("{final_url}", {{
                        method: 'GET',
                        headers: {final_headers}
                    }});
                    return await res.json();
                }}
            """
            return page.evaluate(js)

        elif method == 'page_intercept':
            if not intercept_query:
                raise ValueError('Parameter intercept_query is required for method=`page_intercept`')

            page = context.new_page() 
            found = False
            data = None

            def handle_response(response):
                nonlocal found, data
                if intercept_query in response.url:
                    page.remove_listener('response', handle_response)
                    body = response.text()
                    parsed = json.loads(body)
                    data = parsed
                    found = True
            
            page.on('response', handle_response)
            try:
                page.goto(final_url)

                elapsed = 0
                while not found and elapsed < 15000:
                    page.wait_for_timeout(500)
                    elapsed += 500

                if not found:
                    raise RuntimeError(f'Timeout waiting for `{intercept_query}`')
                
            finally:
                page.close()

            return data

        else:
            raise ValueError(f'Unknown method `{method}`')

    except Exception as e:
        print(f'An exception occured: {e}')
        return {}


def fetch_fanduel_data(context, output, league, event_id=None):
    url = 'https://sbapi.il.sportsbook.fanduel.com/api'
    if event_id:
        url += '/event-page'
        params = [('eventId', event_id)]
    else:
        url += '/content-managed-page'
        params = [
            ('page', 'CUSTOM'),
            ('customPageId', league),
        ]

    headers = {
        'origin': 'https://sportsbook.fanduel.com',
        'referer': 'https://sportsbook.fanduel.com',
    }
    params.extend([
        ('_ak', 'FhMFpcPWXMeyZxOx'),
        ('timezone', 'America%2FChicago'),
    ])

    data = fetch_data(url, context, headers=headers, params=params)

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_espnbet_data(context, output, league, event_id=None):
    url = 'https://sportsbook-tsb.ca-default.thescore.bet/graphql/persisted_queries/a10930c7eba26a588efb729298364a07aa4cdcd40d456dd061dee1355bfb8e86'
    path = f'/sport/{get_sport_from_league(league)}/organization/united-states/competition/{league}'

    if event_id:
        path += f'/event/{event_id}'

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
    params = [
        ('operationName', 'Marketplace'),
        ('variables', json.dumps(variables)),
    ]

    data = fetch_data(url, context, headers=headers, params=params, method='page_evaluate_fetch')

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_draftkings_data(context, output, league, event_id=None):
    LEAGUE_ID_MAP = {
        'mlb': 84240,
    }
    url = 'https://sportsbook-nash.draftkings.com/api/sportscontent/dkusil/v1'
    if event_id:
        url += f'/leagues/{LEAGUE_ID_MAP[league]}'
    else:
        url = f'/events/{event_id}/categories'
    headers = {
        'origin': 'https://sportsbook.draftkings.com',
        'referer': 'https://sportsbook.draftkings.com',
    }

    data = fetch_data(url, context, headers=headers)

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_betrivers_data(context, output, league, event_id=None):
    CAGE_CODE = 847
    LEAGUE_ID_MAP = {
        'mlb': 1000093616,
    }
    url = 'https://il.betrivers.com/api/service/sportsbook/offering/listview'
    if event_id:
        url += '/details'
        params = [
            ('eventId', event_id),
            ('cageCode', CAGE_CODE),
        ]
    else:
        url += '/events'
        params = [
            ('type', 'live'),
            ('type', 'prematch'),
            ('cageCode', str(CAGE_CODE)),
            ('groupId', str(LEAGUE_ID_MAP[league])),
        ]

    headers = {
        'origin': 'https://betrivers.com',
        'referer': 'https://betrivers.com'
    }
    data = fetch_data(url, context, headers=headers, params=params)

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_betmgm_data(context, output, league, event_id=None):
    SPORT_ID_MAP = {
        'baseball': 23,
    }
    LEAGUE_ID_MAP = {
        'mlb': 75,
    }
    url = 'https://www.il.betmgm.com/en/sports'
    if event_id:
        url += f'/events/{event_id}'
        intercept_query = 'fixture-view'
    else:
        sport = get_sport_from_league(league)
        url += f'/{sport}-{SPORT_ID_MAP[sport]}/betting/usa-9/{league}-{LEAGUE_ID_MAP[league]}'
        intercept_query = 'fixtures'
    
    data = fetch_data(url, context, method='page_intercept', intercept_query=intercept_query)

    with open(output, 'w') as f:
        json.dump(data, f, indent=2)


def main(output, league, event_id):
    browser = init_browser()
    context = browser.new_context()

    match args.sportsbook:
        case 'fanduel': fetch_fanduel_data(context, output, league, event_id=event_id)
        case 'draftkings': fetch_draftkings_data(context, output, league, event_id=event_id)
        case 'espnbet': fetch_espnbet_data(context, output, league, event_id=event_id)
        case 'betrivers': fetch_betrivers_data(context, output, league, event_id=event_id)
        case 'betmgm': fetch_betmgm_data(context, output, league, event_id=event_id)
        case _: print(f'Unknown sportsbook `{args.sportsbook}`')
    
    context.close()
    browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sportsbook', help='Name of the sportsbook to be fetched from')
    parser.add_argument('league', help='Sports league')
    parser.add_argument('-e', '--event', type=str, help='The event whose data will be fetched from')
    parser.add_argument('-o', '--output', type=str, help='The file where the output data will be written')

    args = parser.parse_args()

    if not args.output:
        if args.event:
            args.output = f'data/{args.sportsbook}_{args.league}_{args.event.replace(":", '_')}_data.json'
        elif args.league:
            args.output = f'data/{args.sportsbook}_{args.league}_data.json'
    
    main(args.output, args.league, args.event)
