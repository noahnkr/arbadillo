
def american_to_decimal(american_odds):
    return american_odds / 100 + 1 if american_odds > 0 else \
           100 / american_odds + 1

def decimal_to_ip(decimal_odds):
    return (1 / decimal_odds) * 100
