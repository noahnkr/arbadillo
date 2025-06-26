import importlib

from playwright.sync_api import sync_playwright

from common.constants.sportsbook import CLIENT_MAP

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


class PlaywrightSessionManager:
    _instance = None

    def __init__(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()


    @classmethod
    def get_instance(cls, force_new=False):
        if cls._instance is None or force_new:
            if cls._instance:
                cls.shutdown()
            cls._instance = PlaywrightSessionManager()
        return cls._instance


    @classmethod
    def new_page(cls, force_context=False):
        if force_context:
            cls.get_instance(force_new=True)
        elif cls._instance is None:
            cls.get_instance()
        return cls._instance.context.new_page()


    @classmethod
    def get_cookies(cls, force_new=False):
        if cls._instance is None or force_new:
            cls.get_instance(force_new=True)
            cls._instance.page.wait_for_timeout(3000)

        cookies = cls._instance.context.cookies()
        return '; '.join(f"{c['name']}={c['value']}" for c in cookies)


    @classmethod
    def shutdown(cls):
        if cls._instance:
            cls._instance.browser.close()
            cls._instance.p.stop()
            cls._instance = None
