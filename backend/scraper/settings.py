import os

BOT_NAME = 'scraper'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

ROBOTSTXT_OBEY = False

LOG_LEVEL = 'CRITICAL'

TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
