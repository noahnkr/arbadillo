from selenium import webdriver
from config import Config
from scraper import *

def main():
    driver = webdriver.Chrome(Config.get_options, Config.get_service)
    scraper = BetMGMScraper(driver)
    leagues = ['mlb']
    data = scraper.scrape(leagues)
    print(data)

if __name__ == '__main__':
    main()
