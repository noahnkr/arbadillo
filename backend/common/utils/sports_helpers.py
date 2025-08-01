from common.constants.aliases import EVENT_SEASON_TYPE_ALIASES
from common.utils.strings import clean_str
from common.exceptions import NormalizationError

def normalize_season_type(season_type: str) -> str:
    for standard, season_types in EVENT_SEASON_TYPE_ALIASES:
        if clean_str(season_type) in map(clean_str, season_types):
            return standard
    raise NormalizationError(f'Unknown season type: {season_type}')
