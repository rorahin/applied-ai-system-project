from dataclasses import dataclass


@dataclass
class Song:
    """Represents a single song with its key audio and metadata features."""

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float       # 0.0 (calm) to 1.0 (intense)
    popularity: int     # 0 to 100
    decade: str         # e.g. "2010s"

    def __post_init__(self):
        # Normalize string fields to lowercase for consistent comparison
        self.genre = self.genre.lower().strip()
        self.mood = self.mood.lower().strip()
        self.decade = self.decade.lower().strip()
