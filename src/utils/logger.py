import logging
from config import Config

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='[%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("some_other_library").setLevel(logging.CRITICAL)