import csv
import os
from typing import List, Tuple

from src.song import Song
from src.user_profile import UserProfile
from src.guardrails import validate_song, deduplicate_songs
from src.logger import setup_logger

logger = setup_logger()

# Resolve songs.csv relative to the project root (one level above src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_PATH = os.path.join(_PROJECT_ROOT, "data", "songs.csv")


def load_songs(filepath: str = DEFAULT_DATA_PATH) -> List[Song]:
    """
    Load, validate, and deduplicate songs from a CSV file.
    Skips rows that fail validation with a warning rather than crashing.
    """
    songs: List[Song] = []
    skipped = 0

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                is_valid, error = validate_song(row)
                if not is_valid:
                    logger.warning(f"Skipping invalid row — {error} | {dict(row)}")
                    skipped += 1
                    continue

                song = Song(
                    id=int(row["id"]),
                    title=row["title"].strip(),
                    artist=row["artist"].strip(),
                    genre=row["genre"].strip(),
                    mood=row["mood"].strip(),
                    energy=float(row["energy"]),
                    popularity=int(row["popularity"]),
                    decade=row["decade"].strip(),
                )
                songs.append(song)

    except FileNotFoundError:
        logger.error(f"Songs file not found: {filepath}")
        return []

    songs = deduplicate_songs(songs)
    logger.info(f"Loaded {len(songs)} songs ({skipped} skipped).")
    return songs


def retrieve_candidates(
    profile: UserProfile, songs: List[Song]
) -> Tuple[List[Song], str]:
    """
    RAG-style retrieval: filter the catalog to relevant candidates before scoring.

    Retrieval modes (returned as the second element of the tuple):
      "exact"   — both genre AND mood match (tight filter, high precision)
      "partial" — at least one of genre, mood, or decade matches (broader)
      "fallback"— no filters applied; returns the full catalog for diverse results

    The mode name is passed through to the agent's self-check and output so the
    user can see which retrieval path was taken.
    """
    if not songs:
        logger.warning("Catalog is empty — nothing to retrieve.")
        return [], "fallback"

    # Vague requests skip filtering and go straight to full-catalog fallback
    if profile.is_vague:
        logger.info("Vague request — using full-catalog fallback retrieval.")
        return list(songs), "fallback"

    # --- Exact retrieval: genre AND mood both specified and both match ---
    if profile.preferred_genre and profile.preferred_mood:
        exact = [
            s for s in songs
            if s.genre == profile.preferred_genre and s.mood == profile.preferred_mood
        ]
        if len(exact) >= 2:
            logger.info(
                f"Exact retrieval: {len(exact)} songs match "
                f"genre='{profile.preferred_genre}' + mood='{profile.preferred_mood}'."
            )
            return exact, "exact"

    # --- Partial retrieval: at least one dimension matches ---
    partial = []
    for song in songs:
        genre_hit = profile.preferred_genre and song.genre == profile.preferred_genre
        mood_hit = profile.preferred_mood and song.mood == profile.preferred_mood
        decade_hit = profile.preferred_decade and song.decade == profile.preferred_decade
        if genre_hit or mood_hit or decade_hit:
            partial.append(song)

    if partial:
        logger.info(f"Partial retrieval: {len(partial)} songs matched at least one preference.")
        return partial, "partial"

    # --- Fallback: nothing matched, return full catalog ---
    logger.info("No partial matches — using full-catalog fallback.")
    return list(songs), "fallback"
