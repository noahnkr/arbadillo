import scrapy

class EventItem(scrapy.Item):
    event_key = scrapy.Field()
    league = scrapy.Field()
    start_time = scrapy.Field()
    away_team = scrapy.Field()
    home_team = scrapy.Field()
    status = scrapy.Field()
    collected_at =  scrapy.Field()

class OddsItem(scrapy.Item):
    event_key = scrapy.Field()
    sportsbook = scrapy.Field()
    market = scrapy.Field()
    outcome = scrapy.Field()
    line = scrapy.Field()
    value = scrapy.Field()
    player = scrapy.Field()
    prop = scrapy.Field()
    collected_at = scrapy.Field()
