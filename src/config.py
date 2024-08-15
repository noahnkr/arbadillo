from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import os

load_dotenv()

class Config:
    # WebDriver Configuration
    BROWSER = os.environ.get('BROWSER') or 'chrome'
    HEADLESS = os.environ.get('HEADLESS', 'False').lower() in ['true', '1', 't']
    WEBDRIVER_PATH = os.environ.get('WEBDRIVER_PATH')
    WEBDRIVER_WAIT_TIME = int(os.environ.get('WEBDRIVER_WAIT_TIME') or 10)

    @staticmethod
    def get_driver():
        if Config.BROWSER == 'chrome':
            options = ChromeOptions()

            # Apply headless mode based on the environment variable
            if Config.HEADLESS:
                options.add_argument('--headless')

            # Suppress logging
            options.add_argument('--disable-logging')
            options.add_argument('--log-level=3')
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('window-size=1920,1080')
            options.add_argument('--disable-gpu')

            if Config.WEBDRIVER_PATH:
                service = ChromeService(Config.WEBDRIVER_PATH)
            else:
                service = ChromeService(ChromeDriverManager().install())

            return webdriver.Chrome(options, service)

        else:
            raise ValueError(f'Browser {Config.BROWSER} is not supported.')

    # Scraper Configuration
    SCRAPING_INTERVAL = int(os.environ.get('SCRAPING_INTERVAL') or 60)
    RETRY_ATTEMPTS = int(os.environ.get('RETRY_ATTEMPTS') or 3)
    LEAGUES = os.environ.get('LEAGUES').split(',')
    BOOKS =  os.environ.get('BOOKS').split(',')

    # Database Configuration