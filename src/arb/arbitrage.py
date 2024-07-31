def american_to_decimal(american_odds):
    return american_odds / 100 + 1 if american_odds > 0 else \
           100 / american_odds + 1


def is_arbitrage_opportunity(odds1, odds2):
    odds1 = american_to_decimal(odds1)
    odds2 = american_to_decimal(odds2)
    
    # Calculate the implied probabilities.
    ip1 = 1 / odds1
    ip2 = 1 / odds2

    return ip1 + ip2 < 1


def calculate_arbitrage(odds1, odds2, investment):
    odds1 = american_to_decimal(odds1)
    odds2 = american_to_decimal(odds2)

    ip1 = 1 / odds1
    ip2 = 1 / odds2

    stake1 = investment * ip1
    stake2 = investment * ip2

    profit = (stake1 * odds1) + (stake2 * odds2) - investment
    roi = profit / investment * 100

    return { "stake1": stake1, "stake2": stake2, "profit": profit, "roi": roi }
 