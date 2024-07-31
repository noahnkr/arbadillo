from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from src.scraper.sportsbook import BetMGMScraper
import json
import os

def get_chrome_options():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    
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
    scraper = BetMGMScraper(driver)
    data = scraper.scrape(['MLB'])

    PATH = './data'
    if not os.path.exists(PATH):
        os.makedirs(PATH)

    with open('data/export.json', 'w') as file:
        json.dump(data, file, indent=4)


if __name__ == '__main__':
    main()
