from datetime import datetime
from dateutil import tz

def current_timestamp() -> str:
    """Return current UTC timestamp as ISO string."""
    central = tz.gettz('America/Chicago')
    return datetime.now(tz=central).isoformat()


def utc_to_cst(time: str) -> str:
    """Converts a time string in UTC to CST."""
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Chicago')

    # Handle different datetime formats
    try:
        utc = datetime.strptime(time, '%Y-%m-%dT%H:%MZ')
    except Exception:
        # Remove ms if present
        if '.' in time:
            time = time.split('.')[0] + 'Z'
        utc = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return datetime.strftime(central, '%Y-%m-%dT%H:%MZ')


def time_diff_minutes(t1: str, t2: str) -> float:
    """Return time diff in minutes between two ISO timestamps."""
    dt1 = datetime.fromisoformat(t1)
    dt2 = datetime.fromisoformat(t2)
    return abs((dt1 - dt2).total_seconds()) / 60.0