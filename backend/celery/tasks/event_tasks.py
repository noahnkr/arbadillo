from ..celery import app

@app.task
def scrape_schedule():
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = CrawlerProcess(get_project_settings())
    process.crawl('schedule')
    process.start()


@app.task
def find_event_url(sportsbook, event_key):
    pass