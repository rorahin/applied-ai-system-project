from typing import List, Optional, Tuple

from src.logger import setup_logger

logger = setup_logger()

# All genres and moods present in songs.csv
SUPPORTED_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "hip-hop", "country", "electronic", "classical",
    "indie folk", "r&b", "metal",
}

SUPPORTED_MOODS = {
    "happy", "chill", "intense", "relaxed", "focused",
    "moody", "melancholy", "sad", "nostalgic", "aggressive",
    "calm", "energetic",
}

SUPPORTED_DECADES = {"1990s", "2000s", "2010s", "2020s"}


def validate_request(raw_request: str) -> Tuple[bool, str]:
    """Return (is_valid, error_message). Catches empty and trivially short requests."""
    if not raw_request or not raw_request.strip():
        return False, "Empty request. Please describe the music you want."
    if len(raw_request.strip()) < 3:
        return False, "Request too short. Please provide more details."
    return True, ""


def validate_song(song_dict: dict) -> Tuple[bool, str]:
    """Validate a raw CSV row dict. Returns (is_valid, error_message)."""
    required = ["title", "artist", "genre", "mood", "energy", "popularity", "decade"]
    for field in required:
        value = song_dict.get(field)
        if value is None or str(value).strip() == "":
            return False, f"Missing required field: '{field}'"

    try:
        energy = float(song_dict["energy"])
        if not 0.0 <= energy <= 1.0:
            return False, f"Energy out of range [0,1]: {energy}"
    except (ValueError, TypeError):
        return False, f"Energy must be numeric, got: {song_dict['energy']}"

    try:
        popularity = int(song_dict["popularity"])
        if not 0 <= popularity <= 100:
            return False, f"Popularity out of range [0,100]: {popularity}"
    except (ValueError, TypeError):
        return False, f"Popularity must be an integer, got: {song_dict['popularity']}"

    return True, ""


def deduplicate_songs(songs: list) -> list:
    """Remove songs with identical (title, artist) pairs. Preserves first occurrence."""
    seen: set = set()
    unique = []
    for song in songs:
        key = (song.title.lower(), song.artist.lower())
        if key not in seen:
            seen.add(key)
            unique.append(song)
        else:
            logger.warning(f"Duplicate removed: '{song.title}' by {song.artist}")
    return unique


def check_genre_support(genre: Optional[str]) -> Optional[str]:
    """Return normalized genre if it exists in the catalog, else None."""
    if genre and genre.lower() in SUPPORTED_GENRES:
        return genre.lower()
    return None


def check_mood_support(mood: Optional[str]) -> Optional[str]:
    """Return normalized mood if it exists in SUPPORTED_MOODS, else None."""
    if mood and mood.lower() in SUPPORTED_MOODS:
        return mood.lower()
    return None
