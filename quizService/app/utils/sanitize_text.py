import bleach


def sanitize_text(value: str) -> str:
    """Strip all HTML tags and trim surrounding whitespace from user-supplied text."""
    return bleach.clean(str(value), tags=[], attributes={}, strip=True).strip()
