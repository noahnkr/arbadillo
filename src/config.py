from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os

load_dotenv()

class Config:
	# WebDriver Configuration
	BROWSER = os.getenv('BROWSER', 'chrome') 
	HEADLESS = os.getenv('HEADLESS', 'False').lower() in ['true', '1', 't']
	WEBDRIVER_PATH = os.getenv('WEBDRIVER_PATH')
	WEBDRIVER_WAIT_TIME = int(os.getenv('WEBDRIVER_WAIT_TIME') or 10)
	WEBDRIVER_THREADS = int(os.getenv('WEBDRIVER_THREADS') or 3)

	@staticmethod
	def get_driver() -> WebDriver:
		match Config.BROWSER:
			case 'chrome':
				options = ChromeOptions()

				# Apply headless mode based on the environment variable
				if Config.HEADLESS:
					options.add_argument('--headless')

				options.add_argument('--disable-logging')
				options.add_argument('--log-level=3')
				options.add_argument('--disable-extensions')
				options.add_argument('--disable-gpu')
				options.add_argument('--disable-infobars')
				options.add_argument('--no-sandbox')
				user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
				options.add_argument(f'user-agent={user_agent}')
				options.add_experimental_option('excludeSwitches', ['enable-automation'])
				options.add_experimental_option('useAutomationExtension', False)
				options.add_argument('--disable-dev-shm-usage')
				options.add_argument('window-size=1920,1080')

				if Config.WEBDRIVER_PATH:
					service = ChromeService(Config.WEBDRIVER_PATH)
				else:
					service = ChromeService(ChromeDriverManager().install())

				return webdriver.Chrome(options, service)
			case 'firefox':
				options = FirefoxOptions()

				# Apply headless mode based on the environment variable
				if Config.HEADLESS:
					options.add_argument('-headless')

				if Config.WEBDRIVER_PATH:
					service = FirefoxService(Config.WEBDRIVER_PATH)
				else:
					service = FirefoxService(GeckoDriverManager().install())

				return webdriver.Firefox(options, service)
			
			case _:
				raise ValueError(f'Browser {Config.BROWSER} is not supported.')

	# Scraper Configuration
	SCRAPING_INTERVAL = int(os.getenv('SCRAPING_INTERVAL') or 60)
	LEAGUES = os.getenv('LEAGUES', '').split(',')
	BOOKS =  os.getenv('BOOKS', '').split(',')

	# Database Configuration

	# Debug
	LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()