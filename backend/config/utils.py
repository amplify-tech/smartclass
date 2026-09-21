"""Small shared helpers used across apps."""


def dedupe_preserve_order(items):
    """Return unique items in first-seen order."""
    return list(dict.fromkeys(items))


def parse_positive_int(value):
    """Return a positive int, or None if missing/invalid."""
    if value is None or value == '':
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 1 else None
