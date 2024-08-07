from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scraper import *
from datetime import datetime

def get_chrome_options():
    chrome_options = Options()

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    
    # Set a user-agent string
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Disable extensions
    chrome_options.add_argument("--disable-extensions")

    # Disable infobars
    chrome_options.add_argument("--disable-infobars")

    # Disable sandboxing
    chrome_options.add_argument("--no-sandbox")

    # Disable dev-shm-usage (helps with running in Docker)
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Window size
    chrome_options.add_argument("window-size=1920,1080")

    # Disable GPU acceleration
    chrome_options.add_argument("--disable-gpu")

    return chrome_options

def main():
    chrome_options = get_chrome_options()
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

    # Take an input of the requested leagues (Which will be all of them)
    leagues = ['mlb', 'nba', 'nfl', 'premier_league']

    # Instantiate implementations of BaseScraper
    betmgm_scraper = BetMGMScraper(driver)
    #fanduel_scraper = FanDuelScraper(driver)
    #ceasars_scraper = CeasarsScraper(driver)
    book_scrapers = [betmgm_scraper]

    all_events = []

    for league in leagues:
        # Get a list of the events for the league from ESPN
        events = BaseScraper.scrape_league_events(league)
        for book in book_scrapers:
            # Append this books picks to the list of events.
            book.scrape_odds(league, events)
        
        # Once every book's picks has been added to the league's events, add these picks
        # to the final list and continue to the next league.
        all_events.extend(events)

    driver.quit()
if __name__ == '__main__':
    main()
