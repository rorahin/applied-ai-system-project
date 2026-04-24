from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    """Represents a parsed user preference profile derived from a natural language request."""

    preferred_genre: Optional[str] = None
    preferred_mood: Optional[str] = None
    target_energy: Optional[float] = None      # 0.0 to 1.0
    preferred_decade: Optional[str] = None     # e.g. "2010s"
    popularity_preference: Optional[str] = None  # "popular", "niche", or None
    raw_request: str = ""
    is_vague: bool = False   # True when no preferences could be parsed
