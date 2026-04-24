"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def print_recommendations(
    profile_name: str,
    recommendations: list,
    mode: str,
    diversity_mode: bool,
) -> None:
    """Print a formatted visual summary table for one user profile's recommendations."""
    COL_RANK    = 4
    COL_TITLE   = 25
    COL_ARTIST  = 21
    COL_GENRE   = 20
    COL_SCORE   = 7
    TABLE_WIDTH = 81

    print("=" * TABLE_WIDTH)
    print(f"Profile : {profile_name}")
    diversity_label = "ON" if diversity_mode else "OFF"
    print(f"Mode    : {mode}  |  Diversity: {diversity_label}")
    print("=" * TABLE_WIDTH)
    print()

    print(
        " #  ".ljust(COL_RANK)
        + "Title".ljust(COL_TITLE)
        + "Artist".ljust(COL_ARTIST)
        + "Genre/Mood".ljust(COL_GENRE)
        + "Score".rjust(COL_SCORE)
    )
    print("-" * TABLE_WIDTH)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        if len(song["title"]) > 24:
            title_cell = (song["title"][:23] + "…").ljust(COL_TITLE)
        else:
            title_cell = song["title"].ljust(COL_TITLE)

        if len(song["artist"]) > 20:
            artist_cell = (song["artist"][:19] + "…").ljust(COL_ARTIST)
        else:
            artist_cell = song["artist"].ljust(COL_ARTIST)

        gm_raw = f"{song['genre']} / {song['mood']}"
        if len(gm_raw) > 19:
            gm_raw = gm_raw[:19] + "…"
        gm_cell = gm_raw.ljust(COL_GENRE)

        score_cell = f"{score:.3f}".rjust(COL_SCORE)

        print(str(rank).rjust(3) + " " + title_cell + artist_cell + gm_cell + score_cell)

        if isinstance(explanation, list):
            explanation = "; ".join(explanation)
        print(f"     Why: {explanation}")
        print()


def main() -> None:
    # Switch scoring mode here — one line change.
    # Available: BALANCED | GENRE_FIRST | MOOD_FIRST | ENERGY_FOCUSED | DISCOVERY
    SCORING_MODE = "BALANCED"

    # Toggle diversity/fairness mode here — one line change.
    # When True, a greedy selection loop applies ARTIST_PENALTY (0.80x) and
    # GENRE_PENALTY (0.92x) to prevent a single artist or genre from
    # dominating the top-k results.
    DIVERSITY_MODE: bool = True

    songs = load_songs("data/songs.csv")

    profiles = {
        # Profile 1: Late-night focused hip-hop worker.
        # Wants vocal-heavy tracks (not instrumental), some spoken word (rap),
        # moderate-to-high tempo, and high danceability.
        "Late-Night Hip-Hop Worker": {
            "genre": "hip-hop",
            "mood": "focused",
            "target_energy": 0.78,
            "likes_acoustic": False,
            "target_tempo": 0.37,        # ~95 BPM normalized: (95-58)/(158-58) = 0.37
            "target_danceability": 0.80,
            "wants_popular": True,
            "wants_instrumental": False,
            "target_speechiness": 0.20,  # expects some rap/spoken word
        },
        # Profile 2: Coffeehouse jazz listener.
        # Prefers acoustic, relaxed, slow-tempo, mostly instrumental with light vocals.
        "Coffeehouse Jazz Listener": {
            "genre": "jazz",
            "mood": "relaxed",
            "target_energy": 0.37,
            "likes_acoustic": True,
            "target_tempo": 0.32,        # ~90 BPM normalized: (90-58)/(158-58) = 0.32
            "target_danceability": 0.50,
            "wants_popular": False,
            "wants_instrumental": False,  # jazz vocals are appreciated
            "target_speechiness": 0.07,
        },
        # Profile 3: Gym workout listener.
        # Wants high energy, high danceability, fast tempo, popular tracks, minimal acoustics.
        "Gym Workout Listener": {
            "genre": "pop",
            "mood": "intense",
            "target_energy": 0.93,
            "likes_acoustic": False,
            "target_tempo": 0.74,        # ~132 BPM normalized: (132-58)/(158-58) = 0.74
            "target_danceability": 0.88,
            "wants_popular": True,
            "wants_instrumental": False,
            "target_speechiness": 0.06,
        },
        # Adversarial 1: genre and mood exist in the catalog but no song satisfies BOTH.
        # Tests whether the 0.35 genre weight always overrides the 0.25 mood weight
        # when the two signals conflict, and whether the formula handles partial matches gracefully.
        "Moody Electronic User (Adversarial)": {
            "genre": "electronic",
            "mood": "moody",
            "target_energy": 0.75,
            "likes_acoustic": False,
            "target_tempo": 0.82,        # ~140 BPM normalized: (140-58)/(158-58) = 0.82
            "target_danceability": 0.90,
            "wants_popular": False,
            "wants_instrumental": True,  # electronic/IDM skew
            "target_speechiness": 0.04,
        },
        # Adversarial 2: cold-start user with no genre or mood declared.
        # Tests the degraded-mode floor: with 60% of scoring weight unavailable (0.35 + 0.25),
        # the formula can only differentiate by energy (0.15), acousticness (0.08),
        # tempo (0.07), danceability (0.04), and the 3 new features (0.06 combined),
        # producing a technically valid but practically limited ranked list.
        "Cold Start User (Adversarial)": {
            "genre": "",
            "mood": "",
            "target_energy": 0.50,
            "likes_acoustic": False,
            "target_tempo": 0.50,
            "target_danceability": 0.50,
            "wants_popular": True,
            "wants_instrumental": False,
            "target_speechiness": 0.05,
        },
    }

    if DIVERSITY_MODE:
        print("[Diversity mode ON — artist/genre penalties active]")

    for profile_name, user_prefs in profiles.items():
        recommendations = recommend_songs(
            user_prefs, songs, k=5, mode=SCORING_MODE, diversity=DIVERSITY_MODE
        )
        print_recommendations(profile_name, recommendations, SCORING_MODE, DIVERSITY_MODE)


if __name__ == "__main__":
    main()
