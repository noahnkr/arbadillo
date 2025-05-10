import os

BOT_NAME = 'scraper'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

ROBOTSTXT_OBEY = False

TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
