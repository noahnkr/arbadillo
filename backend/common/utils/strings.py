import re

def extract_float(raw: str) -> float | None:
    """Extracts the first numeric value from a string and returns it as a float."""
    match = re.search(r'\d+(?:\.\d+)?', raw)
    return float(match.group()) if match else None


def extract_text(raw: str) -> str | None:
    """Extracts the first alpha values from a string."""
    match = re.search(r'[a-z\s]*', raw)
    return float(match.group().strip()) if match else None


def clean_str(raw: str) -> str:
    """Trim and normalize input string extracted from web and JSON"""
    raw = re.sub(r"[-_e/\\]", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip().lower()