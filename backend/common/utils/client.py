import importlib

from common.constants.sportsbook_definitions import CLIENT_MAP


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