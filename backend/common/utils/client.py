import importlib

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from common.constants.sportsbook_definitions import CLIENT_MAP

_browser = None
_playwright = None

def init_browser():
    global _browser, _playwright
    if _browser is None:
        ctx = Stealth().use_sync(sync_playwright())
        _playwright = ctx.__enter__()
        _browser = _playwright.chromium.launch(headless=True)
    return _browser


def shutdown_browser():
    global _browser, _playwright
    if _browser:
        _browser.close()
        _playwright.stop()
        _browser = None
        _playwright = None


def get_class_from_path(path: str):
    module_path, class_name = path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_client(sportsbook: str, sport: str, league: str):
    class_path = CLIENT_MAP.get(sportsbook.lower())
    if not class_path:
        raise ValueError(f'No client found for sportsbook `{sportsbook}`')
    ClientClass = get_class_from_path(class_path)
    return ClientClass(sport, league)