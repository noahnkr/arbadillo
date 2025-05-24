from .constants import LEAGUE_ALIASES
from .exceptions import NormalizationError
from datetime import datetime
from multiprocessing import Process
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import hashlib
import importlib
import json
import re

# ---------- String Helpers -----------

def clean_team_name(name: str) -> str:
    """Trim and normalize team names."""
    return re.sub(r"\s+", " ", name).strip().lower()


def normalize_team_name(name: str, league: str) -> str:
    """Normalizes a team name to a slugified standard."""
    team_aliases = LEAGUE_ALIASES[league]
    for standard, aliases in team_aliases.items():
        if clean_team_name(name) in map(str.lower, aliases):
            return standard
    raise NormalizationError(f'Unkown team name `{name}` for league `{league}`')

# ---------- Event & Odds Helpers -----------

def create_event_key(league:str, away:str, home:str, date: datetime) -> str:
    """Generate event key (primary ID) for database and Redis."""
    date_str = date.strftime('%Y-%m-%d')
    return f'{league}_{away}@{home}_{date_str}'


def generate_odds_hash(odds_data: dict) -> str:
    """Create a hash to uniquely identify a specific odds line."""
    relevant = {k: odds_data[k] for k in sorted(odds_data) if k in {'event_key', 'market', 'outcome', 'value', 'line', 'player', 'prop'}}
    raw = json.dumps(relevant, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# ---------- Time Helpers -----------

def current_timestamp() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now().isoformat()


def iso_to_unix(iso_str: str) -> int:
    """Convert ISO time string to UNIX timestamp."""
    return int(datetime.fromisoformat(iso_str).timestamp())


def unix_to_iso(ts: int) -> str:
    """Convert UNIX timestamp to ISO format."""
    return datetime.fromtimestamp(ts).isoformat()


def time_diff_minutes(t1: str, t2: str) -> float:
    """Return time diff in minutes between two ISO timestamps."""
    dt1 = datetime.fromisoformat(t1)
    dt2 = datetime.fromisoformat(t2)
    return abs((dt1 - dt2).total_seconds()) / 60.0

# ---------- Scrapy Helpers ----------

def launch_spider(spider_name, args=None):
    """Dynamically launches a Scrapy spider in a seperate process."""
    def _crawl():
        spider_cls = get_spider_class(spider_name)
        settings = get_project_settings()
        process = CrawlerProcess(settings)
        process.crawl(spider_cls, **(args or {}))
        process.start()

    p = Process(target=_crawl)
    p.start()
    p.join()


def get_spider_class(spider_name):
    """Dynamically imports a spider class based on spider_name."""
    module_path = f'scraper.spiders.{spider_name}'
    spider_module = importlib.import_module(module_path)
    return getattr(spider_module, 'Spider')