from dataclasses import dataclass
from typing import List, Tuple

from src.song import Song
from src.user_profile import UserProfile
from src.logger import setup_logger

logger = setup_logger()

# Scoring weights — must sum to 1.0
WEIGHTS = {
    "genre":      0.30,
    "mood":       0.30,
    "energy":     0.20,
    "popularity": 0.10,
    "decade":     0.10,
}

# Minimum score for a "medium" confidence recommendation
CONFIDENCE_THRESHOLD = 0.50


@dataclass
class Recommendation:
    """A scored, explained recommendation for a single song."""
    song: Song
    score: float
    confidence: str   # "high", "medium", or "low"
    explanation: str  # human-readable breakdown of the score


def score_song(song: Song, profile: UserProfile) -> Tuple[float, str]:
    """
    Compute a weighted score for a song against a user profile.

    When a preference dimension is unspecified (None), we award a neutral
    0.5 contribution for that dimension so unspecified dimensions don't
    unfairly penalise any song.

    Returns (score, explanation_string).
    """
    parts: List[str] = []
    score = 0.0

    # --- Genre (30%) ---
    if profile.preferred_genre:
        if song.genre == profile.preferred_genre:
            score += WEIGHTS["genre"]
            parts.append(f"genre match ({song.genre})")
        else:
            parts.append(f"genre mismatch ({song.genre} ≠ {profile.preferred_genre})")
    else:
        score += WEIGHTS["genre"] * 0.5  # neutral

    # --- Mood (30%) ---
    if profile.preferred_mood:
        if song.mood == profile.preferred_mood:
            score += WEIGHTS["mood"]
            parts.append(f"mood match ({song.mood})")
        else:
            parts.append(f"mood mismatch ({song.mood} ≠ {profile.preferred_mood})")
    else:
        score += WEIGHTS["mood"] * 0.5  # neutral

    # --- Energy (20%) — closeness to target ---
    if profile.target_energy is not None:
        closeness = 1.0 - abs(song.energy - profile.target_energy)
        score += WEIGHTS["energy"] * closeness
        parts.append(f"energy {song.energy:.2f} (target {profile.target_energy:.2f})")
    else:
        score += WEIGHTS["energy"] * 0.5  # neutral

    # --- Popularity (10%) ---
    pop_score = song.popularity / 100.0
    score += WEIGHTS["popularity"] * pop_score
    parts.append(f"popularity {song.popularity}")

    # --- Decade (10%) ---
    if profile.preferred_decade:
        if song.decade == profile.preferred_decade:
            score += WEIGHTS["decade"]
            parts.append(f"decade match ({song.decade})")
        else:
            parts.append(f"decade mismatch ({song.decade} ≠ {profile.preferred_decade})")
    else:
        score += WEIGHTS["decade"] * 0.5  # neutral

    return round(score, 4), " | ".join(parts)


def get_confidence(score: float) -> str:
    """Map a numeric score to a human-readable confidence label."""
    if score >= 0.75:
        return "high"
    if score >= CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def rank_songs(
    songs: List[Song], profile: UserProfile, top_k: int = 5
) -> List[Recommendation]:
    """
    Score every candidate song and return the top_k recommendations,
    sorted by score descending with ties broken by ascending song id.
    """
    scored: List[Recommendation] = []
    for song in songs:
        score, explanation = score_song(song, profile)
        scored.append(
            Recommendation(
                song=song,
                score=score,
                confidence=get_confidence(score),
                explanation=explanation,
            )
        )

    scored.sort(key=lambda r: (-r.score, r.song.id))
    top = scored[:top_k]
    logger.info(f"Ranked {len(songs)} songs → returning top {len(top)}.")
    return top
