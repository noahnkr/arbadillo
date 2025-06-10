from playwright.sync_api import sync_playwright

class PlaywrightSessionManager:
    _instance = None

    def __init__(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=True)
        self.context = self.browser.new_context()


    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PlaywrightSessionManager()
        return cls._instance


    @classmethod
    def shutdown(cls):
        if cls._instance:
            cls._instance.browser.close()
            cls._instance.p.stop()
            cls._instance = None
    