import re
import unicodedata


def generate_slug_from_name(name: str) -> str:
    """Convert a business name to a URL-safe slug."""
    # Normalize unicode (handle Arabic/accented chars)
    normalized = unicodedata.normalize("NFKD", name)
    # Keep only ASCII characters
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    # Lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_str.lower()).strip("-")
    # Fallback if name is entirely non-ASCII (e.g., pure Arabic)
    if not slug:
        slug = "business"
    return slug[:50]  # max 50 chars
