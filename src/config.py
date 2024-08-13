from dotenv import load_dotenv
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import os

load_dotenv()

class Config:
    # WebDriver Configuration
    BROWSER = os.environ.get('BROWSER') or 'chrome'
    HEADLESS = os.environ.get('HEADLESS', 'False').lower() in ['true', '1', 't']
    WEBDRIVER_PATH = os.environ.get('WEBDRIVER_PATH') or ChromeDriverManager.install()
    WEBDRIVER_WAIT_TIME = int(os.environ.get('WEBDRIVER_WAIT_TIME') or 10)

    @staticmethod
    def get_service():
        if Config.BROWSER == 'chrome':
            return ChromeService(Config.WEBDRIVER_PATH)
        else:
            raise ValueError(f'Browser {Config.BROWSER} is not supported.')

    @staticmethod
    def get_options():
        if Config.BROWSER == 'chrome':
            options = ChromeOptions()

            # Apply headless mode based on the environment variable
            if Config.HEADLESS:
                options.add_argument('--headless')

            options.add_argument('--disable-logging')
            options.add_argument('--log-level=3')

            # Set a user-agent string
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')

            # Disable automation flags
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            # Disable extensions
            options.add_argument('--disable-extensions')

            # Disable infobars
            options.add_argument('--disable-infobars')

            # Disable sandboxing
            options.add_argument('--no-sandbox')

            # Disable dev-shm-usage (helps with running in Docker)
            options.add_argument('--disable-dev-shm-usage')

            # Window size
            options.add_argument('window-size=1920,1080')

            # Disable GPU acceleration
            options.add_argument('--disable-gpu')
        else:
            raise ValueError(f'Browser {Config.BROWSER} is not supported.')

        return options

    # Scraper Configuration
    SCRAPING_INTERVAL = int(os.environ.get('SCRAPING_INTERVAL') or 60)
    RETRY_ATTEMPTS = int(os.environ.get('RETRY_ATTEMPTS') or 3)

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

