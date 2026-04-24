from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import csv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Min/max tempo_bpm observed in the 20-song catalog.
# Used for min-max normalization of raw BPM to [0, 1].
TEMPO_BPM_MIN: float = 58.0
TEMPO_BPM_MAX: float = 158.0

# ---------------------------------------------------------------------------
# Scoring Modes — Challenge 2
# ---------------------------------------------------------------------------
# Each mode is a complete weight distribution over all 9 features.
# All weight sets sum to exactly 1.0.
# Add new modes here without touching score_song() or recommend_songs().
#
# BALANCED       — default; broad-purpose, genre+mood dominant
# GENRE_FIRST    — genre weight maximized; for single-genre listeners
# MOOD_FIRST     — mood weight maximized; for emotion/context-driven listening
# ENERGY_FOCUSED — energy+tempo maximized; for workout/activity listening
# DISCOVERY      — genre+mood minimized, danceability+popularity boosted;
#                  surfaces surprising cross-genre mainstream tracks
# ---------------------------------------------------------------------------

SCORING_WEIGHTS: Dict[str, Dict[str, float]] = {
    "BALANCED": {
        "genre": 0.35, "mood": 0.25, "energy": 0.15, "acousticness": 0.08,
        "tempo": 0.07, "danceability": 0.04, "popularity": 0.02,
        "instrumentalness": 0.02, "speechiness": 0.02,
    },
    "GENRE_FIRST": {
        "genre": 0.55, "mood": 0.15, "energy": 0.10, "acousticness": 0.07,
        "tempo": 0.05, "danceability": 0.03, "popularity": 0.02,
        "instrumentalness": 0.02, "speechiness": 0.01,
    },
    "MOOD_FIRST": {
        "genre": 0.15, "mood": 0.50, "energy": 0.10, "acousticness": 0.07,
        "tempo": 0.05, "danceability": 0.03, "popularity": 0.02,
        "instrumentalness": 0.06, "speechiness": 0.02,
    },
    "ENERGY_FOCUSED": {
        "genre": 0.10, "mood": 0.10, "energy": 0.35, "acousticness": 0.08,
        "tempo": 0.20, "danceability": 0.07, "popularity": 0.03,
        "instrumentalness": 0.05, "speechiness": 0.02,
    },
    "DISCOVERY": {
        "genre": 0.10, "mood": 0.10, "energy": 0.15, "acousticness": 0.10,
        "tempo": 0.10, "danceability": 0.20, "popularity": 0.15,
        "instrumentalness": 0.05, "speechiness": 0.05,
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """
    Represents a song and its audio attributes.

    Original fields (Phase 1/2):
        id, title, artist, genre, mood, energy, tempo_bpm,
        valence, danceability, acousticness

    Extended fields (Challenge 1):
        popularity       -- chart-level appeal, integer 0-100
        instrumentalness -- proportion of track that is instrumental, 0.0-1.0
        speechiness      -- proportion of spoken word content, 0.0-1.0

    New fields use defaults so existing test constructors that omit them
    continue to work without modification.

    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # --- Challenge 1 extended fields (defaults preserve backward compatibility) ---
    popularity: int = 50
    instrumentalness: float = 0.5
    speechiness: float = 0.05


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences used by the OOP Recommender.

    Original fields (Phase 1/2):
        favorite_genre, favorite_mood, target_energy, likes_acoustic

    Extended fields (Challenge 1):
        target_tempo        -- preferred normalized tempo, 0.0-1.0
        target_danceability -- preferred danceability level, 0.0-1.0
        wants_popular       -- True = prefer mainstream, False = prefer niche
        wants_instrumental  -- True = prefer instrumental, False = prefer vocal
        target_speechiness  -- preferred speechiness level, 0.0-1.0

    New fields use defaults so existing test constructors that omit them
    continue to work without modification.

    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # --- Challenge 1 extended fields (defaults preserve backward compatibility) ---
    target_tempo: float = 0.5
    target_danceability: float = 0.5
    wants_popular: bool = True
    wants_instrumental: bool = False
    target_speechiness: float = 0.1


# ---------------------------------------------------------------------------
# OOP Recommender (used by tests)
# ---------------------------------------------------------------------------

class Recommender:
    """
    OOP implementation of the recommendation logic.

    Scoring formula (weights sum to 1.0):
        final_score = (0.35 * genre_score)
                    + (0.25 * mood_score)
                    + (0.15 * energy_score)
                    + (0.08 * acousticness_score)
                    + (0.07 * tempo_score)
                    + (0.04 * dance_score)
                    + (0.02 * popularity_score)
                    + (0.02 * instrumentalness_score)
                    + (0.02 * speechiness_score)

    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> float:
        """Compute a weighted score for a song against a user profile."""
        genre_score = 1.0 if song.genre == user.favorite_genre else 0.0
        mood_score = 1.0 if song.mood == user.favorite_mood else 0.0
        energy_score = 1.0 - abs(song.energy - user.target_energy)

        if user.likes_acoustic:
            acousticness_score = song.acousticness
        else:
            acousticness_score = 1.0 - song.acousticness

        tempo_normalized = (song.tempo_bpm - TEMPO_BPM_MIN) / (TEMPO_BPM_MAX - TEMPO_BPM_MIN)
        tempo_score = 1.0 - abs(tempo_normalized - user.target_tempo)

        dance_score = 1.0 - abs(song.danceability - user.target_danceability)

        popularity_score = song.popularity / 100.0
        if not user.wants_popular:
            popularity_score = 1.0 - popularity_score

        if user.wants_instrumental:
            instrumentalness_score = song.instrumentalness
        else:
            instrumentalness_score = 1.0 - song.instrumentalness

        speechiness_score = 1.0 - abs(song.speechiness - user.target_speechiness)

        return (
            (0.35 * genre_score)
            + (0.25 * mood_score)
            + (0.15 * energy_score)
            + (0.08 * acousticness_score)
            + (0.07 * tempo_score)
            + (0.04 * dance_score)
            + (0.02 * popularity_score)
            + (0.02 * instrumentalness_score)
            + (0.02 * speechiness_score)
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by score, breaking ties by song id."""
        ranked = sorted(self.songs, key=lambda s: (-self._score(user, s), s.id))
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        reasons = []

        if song.genre == user.favorite_genre:
            reasons.append(f"genre matches your favorite ({song.genre})")
        if song.mood == user.favorite_mood:
            reasons.append(f"mood matches your preference ({song.mood})")

        energy_diff = abs(song.energy - user.target_energy)
        if energy_diff <= 0.15:
            reasons.append(f"energy level is close to your target ({song.energy:.2f})")

        if user.likes_acoustic and song.acousticness >= 0.7:
            reasons.append(f"highly acoustic ({song.acousticness:.2f})")
        elif not user.likes_acoustic and song.acousticness <= 0.3:
            reasons.append(f"low acousticness fits your style ({song.acousticness:.2f})")

        tempo_normalized = (song.tempo_bpm - TEMPO_BPM_MIN) / (TEMPO_BPM_MAX - TEMPO_BPM_MIN)
        if abs(tempo_normalized - user.target_tempo) <= 0.15:
            reasons.append(f"tempo close to your preferred pace (normalized: {tempo_normalized:.2f})")

        if abs(song.danceability - user.target_danceability) <= 0.15:
            reasons.append(f"danceability close to your preference ({song.danceability:.2f})")

        if user.wants_popular and song.popularity >= 70:
            reasons.append(f"popular track (popularity: {song.popularity})")
        elif not user.wants_popular and song.popularity <= 50:
            reasons.append(f"underground/niche track (popularity: {song.popularity})")

        if user.wants_instrumental and song.instrumentalness >= 0.7:
            reasons.append(f"highly instrumental ({song.instrumentalness:.2f})")
        elif not user.wants_instrumental and song.instrumentalness <= 0.1:
            reasons.append(f"vocal-forward track ({song.instrumentalness:.2f})")

        if abs(song.speechiness - user.target_speechiness) <= 0.10:
            reasons.append(f"speechiness close to your preference ({song.speechiness:.2f})")

        if not reasons:
            reasons.append("overall profile similarity")

        return "Recommended because: " + ", ".join(reasons) + "."


# ---------------------------------------------------------------------------
# Functional layer (used by main.py and future ML integrations)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """
    Load songs from a CSV file and return them as a list of typed dictionaries.

    All numeric fields are cast to their correct Python types:
        int  -- id, popularity
        float -- energy, tempo_bpm, valence, danceability, acousticness,
                 instrumentalness, speechiness
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":               int(row["id"]),
                "title":            row["title"],
                "artist":           row["artist"],
                "genre":            row["genre"],
                "mood":             row["mood"],
                "energy":           float(row["energy"]),
                "tempo_bpm":        float(row["tempo_bpm"]),
                "valence":          float(row["valence"]),
                "danceability":     float(row["danceability"]),
                "acousticness":     float(row["acousticness"]),
                "popularity":       int(row["popularity"]),
                "instrumentalness": float(row["instrumentalness"]),
                "speechiness":      float(row["speechiness"]),
            })
    return songs


def score_song(user_prefs: Dict, song: Dict, mode: str = "BALANCED") -> Tuple[float, List[str]]:
    """
    Score a single song against user preferences.

    Parameters
    ----------
    user_prefs : Dict
        User preference dictionary.
    song : Dict
        Song feature dictionary loaded from CSV.
    mode : str, optional
        Scoring mode key from SCORING_WEIGHTS. Defaults to "BALANCED".
        Available modes: BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED, DISCOVERY.
        Raises KeyError if an unknown mode is passed.

    Returns
    -------
    (float, List[str])
        A tuple of (final_score, reasons_list).
        final_score is in the range [0.0, 1.0].
        reasons_list is a non-empty list of human-readable strings explaining
        which features contributed positively.

    All weights are non-negative and sum to exactly 1.0.
    All individual feature scores are normalized to [0, 1] before weighting.
    """
    w = SCORING_WEIGHTS[mode]
    reasons = []

    # --- Genre (0.35) ---
    genre_score = 1.0 if song.get("genre") == user_prefs.get("genre") else 0.0
    if genre_score == 1.0:
        reasons.append(f"genre match ({song['genre']})")

    # --- Mood (0.25) ---
    mood_score = 1.0 if song.get("mood") == user_prefs.get("mood") else 0.0
    if mood_score == 1.0:
        reasons.append(f"mood match ({song['mood']})")

    # --- Energy (0.15) ---
    target_energy = user_prefs.get("target_energy", 0.5)
    song_energy = song.get("energy", 0.5)
    energy_score = 1.0 - abs(song_energy - target_energy)
    if abs(song_energy - target_energy) <= 0.15:
        reasons.append(f"energy close to target ({song_energy:.2f})")

    # --- Acousticness (0.08) ---
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    song_acousticness = song.get("acousticness", 0.5)
    if likes_acoustic:
        acousticness_score = song_acousticness
        if song_acousticness >= 0.7:
            reasons.append(f"highly acoustic ({song_acousticness:.2f})")
    else:
        acousticness_score = 1.0 - song_acousticness
        if song_acousticness <= 0.3:
            reasons.append(f"low acousticness ({song_acousticness:.2f})")

    # --- Tempo normalized (0.07) ---
    song_tempo_bpm = song.get("tempo_bpm", 100.0)
    tempo_normalized = (song_tempo_bpm - TEMPO_BPM_MIN) / (TEMPO_BPM_MAX - TEMPO_BPM_MIN)
    target_tempo = user_prefs.get("target_tempo", 0.5)
    tempo_score = 1.0 - abs(tempo_normalized - target_tempo)
    if abs(tempo_normalized - target_tempo) <= 0.15:
        reasons.append(f"tempo close to your preferred pace (normalized: {tempo_normalized:.2f})")

    # --- Danceability (0.04) ---
    song_dance = song.get("danceability", 0.5)
    target_dance = user_prefs.get("target_danceability", 0.5)
    dance_score = 1.0 - abs(song_dance - target_dance)
    if abs(song_dance - target_dance) <= 0.15:
        reasons.append(f"danceability close to your preference ({song_dance:.2f})")

    # --- Popularity (0.02) ---
    song_popularity = song.get("popularity", 50)
    wants_popular = user_prefs.get("wants_popular", True)
    raw_pop = song_popularity / 100.0
    if wants_popular:
        popularity_score = raw_pop
        if song_popularity >= 70:
            reasons.append(f"popular track (popularity: {song_popularity})")
    else:
        popularity_score = 1.0 - raw_pop
        if song_popularity <= 50:
            reasons.append(f"underground/niche track (popularity: {song_popularity})")

    # --- Instrumentalness (0.02) ---
    song_inst = song.get("instrumentalness", 0.5)
    wants_instrumental = user_prefs.get("wants_instrumental", False)
    if wants_instrumental:
        instrumentalness_score = song_inst
        if song_inst >= 0.7:
            reasons.append(f"highly instrumental ({song_inst:.2f})")
    else:
        instrumentalness_score = 1.0 - song_inst
        if song_inst <= 0.1:
            reasons.append(f"vocal-forward track ({song_inst:.2f})")

    # --- Speechiness (0.02) ---
    song_speech = song.get("speechiness", 0.05)
    target_speech = user_prefs.get("target_speechiness", 0.1)
    speechiness_score = 1.0 - abs(song_speech - target_speech)
    if abs(song_speech - target_speech) <= 0.10:
        reasons.append(f"speechiness close to your preference ({song_speech:.2f})")

    if not reasons:
        reasons.append("overall profile similarity")

    score = (
        (w["genre"]           * genre_score)
        + (w["mood"]          * mood_score)
        + (w["energy"]        * energy_score)
        + (w["acousticness"]  * acousticness_score)
        + (w["tempo"]         * tempo_score)
        + (w["danceability"]  * dance_score)
        + (w["popularity"]    * popularity_score)
        + (w["instrumentalness"] * instrumentalness_score)
        + (w["speechiness"]   * speechiness_score)
    )

    return (score, reasons)


ARTIST_PENALTY: float = 0.80
GENRE_PENALTY: float = 0.92


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "BALANCED",
    diversity: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """
    Rank all songs by score against user preferences and return the top k.

    Parameters
    ----------
    user_prefs : Dict
        User preference dictionary.
    songs : List[Dict]
        Full song catalog loaded from CSV.
    k : int, optional
        Number of top recommendations to return. Defaults to 5.
    mode : str, optional
        Scoring mode key from SCORING_WEIGHTS. Defaults to "BALANCED".
    diversity : bool, optional
        When False (default), returns the top-k by raw score — existing
        behaviour, all existing tests continue to pass unchanged.
        When True, uses a greedy iterative selection loop that applies
        ARTIST_PENALTY (0.80x) and GENRE_PENALTY (0.92x) to penalise
        artists and genres already present in the selected list, promoting
        variety in the final recommendations.

    Returns
    -------
    List of (song_dict, score_float, explanation_string) tuples,
    sorted descending by score, with ties broken by ascending song id.
    When diversity=True, score_float reflects the effective (penalised)
    score, not the raw base score.
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, mode)
        scored.append((song, score, reasons))

    if not diversity:
        result = []
        scored.sort(key=lambda x: (-x[1], x[0]["id"]))
        for song, score, reasons in scored[:k]:
            result.append((song, score, ", ".join(reasons)))
        return result

    # ------------------------------------------------------------------
    # Greedy iterative selection with artist/genre diversity penalties.
    # Time complexity: O(k * n) where n = len(songs), k = top-k count.
    # In practice k <= 10 and n <= a few thousand, so this is acceptable.
    # ------------------------------------------------------------------
    selected = []
    remaining = list(scored)

    while len(selected) < k and remaining:
        selected_artists = {s[0]["artist"] for s in selected}
        selected_genres = {s[0]["genre"] for s in selected}

        best = None
        best_eff = -1.0
        best_id = float("inf")

        for song, base_score, reasons in remaining:
            eff = base_score
            penalty_reasons = []

            if song["artist"] in selected_artists:
                eff *= ARTIST_PENALTY
                penalty_reasons.append(
                    f"Diversity penalty (artist): {song['artist']} already recommended"
                    " — score adjusted 0.80x"
                )
            if song["genre"] in selected_genres:
                eff *= GENRE_PENALTY
                penalty_reasons.append(
                    f"Diversity penalty (genre): {song['genre']} already represented"
                    " — score adjusted 0.92x"
                )

            eff = max(eff, 0.0)

            if eff > best_eff or (eff == best_eff and song["id"] < best_id):
                best = (song, eff, reasons + penalty_reasons)
                best_eff = eff
                best_id = song["id"]

        selected.append(best)
        remaining = [
            (s, sc, r) for s, sc, r in remaining if s["id"] != best[0]["id"]
        ]

    return [(song, score, ", ".join(reasons)) for song, score, reasons in selected]
