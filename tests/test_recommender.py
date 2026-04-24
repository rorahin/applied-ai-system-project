"""
Comprehensive test suite for the Music Recommender Simulation.

Covers: load_songs, SCORING_WEIGHTS, score_song, recommend_songs,
        OOP Recommender class, integration tests with real catalog,
        and diversity/fairness logic.

Run with:
    python3 -m pytest tests/ -v
"""

import os
import pytest

from src.recommender import (
    load_songs,
    score_song,
    recommend_songs,
    SCORING_WEIGHTS,
    ARTIST_PENALTY,
    GENRE_PENALTY,
    Song,
    UserProfile,
    Recommender,
    TEMPO_BPM_MIN,
    TEMPO_BPM_MAX,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "songs.csv")

# ---------------------------------------------------------------------------
# Required CSV keys
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "id", "title", "artist", "genre", "mood",
    "energy", "tempo_bpm", "valence", "danceability",
    "acousticness", "popularity", "instrumentalness", "speechiness",
}


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def songs():
    """Load the real 20-song catalog once for the entire test module."""
    return load_songs(CSV_PATH)


@pytest.fixture
def hip_hop_profile():
    """Late-Night Hip-Hop Worker profile (copied from main.py)."""
    return {
        "genre": "hip-hop",
        "mood": "focused",
        "target_energy": 0.78,
        "likes_acoustic": False,
        "target_tempo": 0.37,
        "target_danceability": 0.80,
        "wants_popular": True,
        "wants_instrumental": False,
        "target_speechiness": 0.20,
    }


@pytest.fixture
def jazz_profile():
    """Coffeehouse Jazz Listener profile (copied from main.py)."""
    return {
        "genre": "jazz",
        "mood": "relaxed",
        "target_energy": 0.37,
        "likes_acoustic": True,
        "target_tempo": 0.32,
        "target_danceability": 0.50,
        "wants_popular": False,
        "wants_instrumental": False,
        "target_speechiness": 0.07,
    }


@pytest.fixture
def gym_profile():
    """Gym Workout Listener profile (copied from main.py)."""
    return {
        "genre": "pop",
        "mood": "intense",
        "target_energy": 0.93,
        "likes_acoustic": False,
        "target_tempo": 0.74,
        "target_danceability": 0.88,
        "wants_popular": True,
        "wants_instrumental": False,
        "target_speechiness": 0.06,
    }


@pytest.fixture
def electronic_profile():
    """Moody Electronic User (Adversarial) profile (copied from main.py)."""
    return {
        "genre": "electronic",
        "mood": "moody",
        "target_energy": 0.75,
        "likes_acoustic": False,
        "target_tempo": 0.82,
        "target_danceability": 0.90,
        "wants_popular": False,
        "wants_instrumental": True,
        "target_speechiness": 0.04,
    }


@pytest.fixture
def cold_start_profile():
    """Cold Start User (Adversarial) profile (copied from main.py)."""
    return {
        "genre": "",
        "mood": "",
        "target_energy": 0.50,
        "likes_acoustic": False,
        "target_tempo": 0.50,
        "target_danceability": 0.50,
        "wants_popular": True,
        "wants_instrumental": False,
        "target_speechiness": 0.05,
    }


@pytest.fixture
def pop_song_dict():
    """A minimal pop/happy song dict for unit tests."""
    return {
        "id": 1,
        "title": "Test Pop Track",
        "artist": "Artist A",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.80,
        "tempo_bpm": 120.0,
        "valence": 0.85,
        "danceability": 0.75,
        "acousticness": 0.15,
        "popularity": 75,
        "instrumentalness": 0.03,
        "speechiness": 0.06,
    }


@pytest.fixture
def pop_user_dict():
    """A user profile that is a perfect genre/mood match for pop_song_dict."""
    return {
        "genre": "pop",
        "mood": "happy",
        "target_energy": 0.80,
        "likes_acoustic": False,
        "target_tempo": 0.62,    # (120 - 58) / 100 = 0.62
        "target_danceability": 0.75,
        "wants_popular": True,
        "wants_instrumental": False,
        "target_speechiness": 0.06,
    }


@pytest.fixture
def jazz_song_dict():
    """A minimal jazz/relaxed song dict for unit tests."""
    return {
        "id": 2,
        "title": "Test Jazz Track",
        "artist": "Artist B",
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.37,
        "tempo_bpm": 90.0,
        "valence": 0.70,
        "danceability": 0.54,
        "acousticness": 0.89,
        "popularity": 61,
        "instrumentalness": 0.10,
        "speechiness": 0.08,
    }


# ===========================================================================
# 1.  load_songs()
# ===========================================================================

class TestLoadSongs:

    def test_returns_list(self, songs):
        """load_songs must return a plain Python list."""
        assert isinstance(songs, list)

    def test_loads_exactly_20_songs(self, songs):
        """The real CSV contains exactly 20 songs."""
        assert len(songs) == 20

    def test_every_song_has_all_required_keys(self, songs):
        """Every song dict must expose all 13 required keys."""
        for song in songs:
            assert REQUIRED_KEYS.issubset(song.keys()), (
                f"Song id={song.get('id')} is missing keys: "
                f"{REQUIRED_KEYS - song.keys()}"
            )

    def test_id_is_int(self, songs):
        """The id field must be cast to int, not left as a string."""
        for song in songs:
            assert isinstance(song["id"], int), f"id={song['id']} is not int"

    def test_energy_is_float(self, songs):
        """energy must be a float after loading."""
        for song in songs:
            assert isinstance(song["energy"], float)

    def test_acousticness_is_float(self, songs):
        """acousticness must be a float after loading."""
        for song in songs:
            assert isinstance(song["acousticness"], float)

    def test_danceability_is_float(self, songs):
        """danceability must be a float after loading."""
        for song in songs:
            assert isinstance(song["danceability"], float)

    def test_instrumentalness_is_float(self, songs):
        """instrumentalness must be a float after loading."""
        for song in songs:
            assert isinstance(song["instrumentalness"], float)

    def test_speechiness_is_float(self, songs):
        """speechiness must be a float after loading."""
        for song in songs:
            assert isinstance(song["speechiness"], float)

    def test_valence_is_float(self, songs):
        """valence must be a float after loading."""
        for song in songs:
            assert isinstance(song["valence"], float)

    def test_tempo_bpm_is_float(self, songs):
        """tempo_bpm must be a float after loading."""
        for song in songs:
            assert isinstance(song["tempo_bpm"], float)

    def test_popularity_is_int(self, songs):
        """popularity must be cast to int, not left as string or float."""
        for song in songs:
            assert isinstance(song["popularity"], int)

    def test_energy_values_in_range(self, songs):
        """All energy values must be in the valid [0.0, 1.0] range."""
        for song in songs:
            assert 0.0 <= song["energy"] <= 1.0, (
                f"energy out of range for id={song['id']}: {song['energy']}"
            )

    def test_acousticness_values_in_range(self, songs):
        """All acousticness values must be in [0.0, 1.0]."""
        for song in songs:
            assert 0.0 <= song["acousticness"] <= 1.0

    def test_danceability_values_in_range(self, songs):
        """All danceability values must be in [0.0, 1.0]."""
        for song in songs:
            assert 0.0 <= song["danceability"] <= 1.0

    def test_instrumentalness_values_in_range(self, songs):
        """All instrumentalness values must be in [0.0, 1.0]."""
        for song in songs:
            assert 0.0 <= song["instrumentalness"] <= 1.0

    def test_speechiness_values_in_range(self, songs):
        """All speechiness values must be in [0.0, 1.0]."""
        for song in songs:
            assert 0.0 <= song["speechiness"] <= 1.0

    def test_popularity_values_in_range(self, songs):
        """All popularity values must be in the integer range [0, 100]."""
        for song in songs:
            assert 0 <= song["popularity"] <= 100

    def test_tempo_bpm_values_in_catalog_range(self, songs):
        """All tempo_bpm values must be within [58, 158] per catalog design."""
        for song in songs:
            assert TEMPO_BPM_MIN <= song["tempo_bpm"] <= TEMPO_BPM_MAX, (
                f"tempo_bpm out of range for id={song['id']}: {song['tempo_bpm']}"
            )

    def test_no_duplicate_song_ids(self, songs):
        """Each song must have a unique id."""
        ids = [song["id"] for song in songs]
        assert len(ids) == len(set(ids))

    def test_no_duplicate_titles(self, songs):
        """Each song must have a unique title."""
        titles = [song["title"] for song in songs]
        assert len(titles) == len(set(titles))


# ===========================================================================
# 2.  SCORING_WEIGHTS
# ===========================================================================

class TestScoringWeights:

    def test_balanced_mode_exists(self):
        """SCORING_WEIGHTS must contain a BALANCED key."""
        assert "BALANCED" in SCORING_WEIGHTS

    def test_genre_first_mode_exists(self):
        """SCORING_WEIGHTS must contain a GENRE_FIRST key."""
        assert "GENRE_FIRST" in SCORING_WEIGHTS

    def test_mood_first_mode_exists(self):
        """SCORING_WEIGHTS must contain a MOOD_FIRST key."""
        assert "MOOD_FIRST" in SCORING_WEIGHTS

    def test_energy_focused_mode_exists(self):
        """SCORING_WEIGHTS must contain an ENERGY_FOCUSED key."""
        assert "ENERGY_FOCUSED" in SCORING_WEIGHTS

    def test_discovery_mode_exists(self):
        """SCORING_WEIGHTS must contain a DISCOVERY key."""
        assert "DISCOVERY" in SCORING_WEIGHTS

    def test_each_mode_has_9_keys(self):
        """Every scoring mode must define weights for all 9 features."""
        for mode, weights in SCORING_WEIGHTS.items():
            assert len(weights) == 9, (
                f"Mode {mode} has {len(weights)} keys, expected 9"
            )

    def test_balanced_weights_sum_to_1(self):
        """BALANCED mode weights must sum to exactly 1.0."""
        total = sum(SCORING_WEIGHTS["BALANCED"].values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_genre_first_weights_sum_to_1(self):
        """GENRE_FIRST mode weights must sum to exactly 1.0."""
        total = sum(SCORING_WEIGHTS["GENRE_FIRST"].values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_mood_first_weights_sum_to_1(self):
        """MOOD_FIRST mode weights must sum to exactly 1.0."""
        total = sum(SCORING_WEIGHTS["MOOD_FIRST"].values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_energy_focused_weights_sum_to_1(self):
        """ENERGY_FOCUSED mode weights must sum to exactly 1.0."""
        total = sum(SCORING_WEIGHTS["ENERGY_FOCUSED"].values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_discovery_weights_sum_to_1(self):
        """DISCOVERY mode weights must sum to exactly 1.0."""
        total = sum(SCORING_WEIGHTS["DISCOVERY"].values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_no_negative_weight_in_any_mode(self):
        """No individual weight may be negative in any mode."""
        for mode, weights in SCORING_WEIGHTS.items():
            for feature, w in weights.items():
                assert w >= 0.0, (
                    f"Mode {mode}, feature {feature} has negative weight {w}"
                )

    def test_no_weight_exceeds_1_in_any_mode(self):
        """No individual weight may exceed 1.0 in any mode."""
        for mode, weights in SCORING_WEIGHTS.items():
            for feature, w in weights.items():
                assert w <= 1.0, (
                    f"Mode {mode}, feature {feature} has weight {w} > 1.0"
                )


# ===========================================================================
# 3.  score_song()
# ===========================================================================

class TestScoreSong:

    def test_returns_tuple(self, pop_user_dict, pop_song_dict):
        """score_song must return a tuple."""
        result = score_song(pop_user_dict, pop_song_dict)
        assert isinstance(result, tuple)

    def test_tuple_has_two_elements(self, pop_user_dict, pop_song_dict):
        """The returned tuple must have exactly 2 elements: (float, list)."""
        result = score_song(pop_user_dict, pop_song_dict)
        assert len(result) == 2

    def test_score_is_float(self, pop_user_dict, pop_song_dict):
        """The first element of the tuple must be a float."""
        score, _ = score_song(pop_user_dict, pop_song_dict)
        assert isinstance(score, float)

    def test_reasons_is_list(self, pop_user_dict, pop_song_dict):
        """The second element of the tuple must be a list."""
        _, reasons = score_song(pop_user_dict, pop_song_dict)
        assert isinstance(reasons, list)

    def test_score_in_valid_range(self, pop_user_dict, pop_song_dict):
        """Final score must be within [0.0, 1.0]."""
        score, _ = score_song(pop_user_dict, pop_song_dict)
        assert 0.0 <= score <= 1.0

    def test_genre_match_produces_1_genre_contribution(self, pop_user_dict, pop_song_dict):
        """When genre matches, the genre sub-score must contribute its full weight."""
        # With BALANCED weights genre=0.35 and a perfect genre match,
        # the genre contribution must be exactly 0.35 of the total.
        # We verify indirectly: score with match > score with mismatch by ~0.35.
        score_match, _ = score_song(pop_user_dict, pop_song_dict)
        mismatch_user = dict(pop_user_dict, genre="jazz")
        score_mismatch, _ = score_song(mismatch_user, pop_song_dict)
        assert score_match - score_mismatch == pytest.approx(0.35, abs=1e-9)

    def test_genre_mismatch_contributes_zero(self, pop_song_dict):
        """When genre does not match, genre contribution must be 0.0."""
        user = {
            "genre": "jazz",
            "mood": "happy",
            "target_energy": 0.80,
            "likes_acoustic": False,
            "target_tempo": 0.62,
            "target_danceability": 0.75,
            "wants_popular": True,
            "wants_instrumental": False,
            "target_speechiness": 0.06,
        }
        score_mismatch, _ = score_song(user, pop_song_dict)
        # Full match minus genre weight gives mismatch; difference == genre weight
        full_match_user = dict(user, genre="pop")
        score_match, _ = score_song(full_match_user, pop_song_dict)
        assert score_match - score_mismatch == pytest.approx(0.35, abs=1e-9)

    def test_mood_match_produces_full_mood_contribution(self, pop_user_dict, pop_song_dict):
        """When mood matches, the mood sub-score must contribute its full weight (0.25)."""
        score_match, _ = score_song(pop_user_dict, pop_song_dict)
        mismatch_user = dict(pop_user_dict, mood="sad")
        score_mismatch, _ = score_song(mismatch_user, pop_song_dict)
        assert score_match - score_mismatch == pytest.approx(0.25, abs=1e-9)

    def test_mood_mismatch_contributes_zero(self, pop_song_dict):
        """A mood mismatch must contribute 0.0 to the final score."""
        user = {"genre": "pop", "mood": "sad", "target_energy": 0.5,
                "likes_acoustic": False, "target_tempo": 0.5,
                "target_danceability": 0.5, "wants_popular": True,
                "wants_instrumental": False, "target_speechiness": 0.05}
        _, reasons = score_song(user, pop_song_dict)
        # No mood match reason should appear
        mood_reasons = [r for r in reasons if "mood match" in r]
        assert len(mood_reasons) == 0

    def test_perfect_energy_match_gives_max_energy_score(self, pop_user_dict, pop_song_dict):
        """When target_energy == song energy, energy sub-score must be 1.0."""
        # Energy sub-score = 1 - |0.80 - 0.80| = 1.0
        # We verify that changing target_energy away reduces the total score.
        score_perfect, _ = score_song(pop_user_dict, pop_song_dict)  # target_energy=0.80
        off_user = dict(pop_user_dict, target_energy=0.50)
        score_off, _ = score_song(off_user, pop_song_dict)
        # Difference = 0.15 * (1.0 - (1.0 - 0.30)) = 0.15 * 0.30 = 0.045
        assert score_perfect > score_off

    def test_energy_score_decreases_with_distance(self, pop_song_dict):
        """Energy sub-score must decrease monotonically as target drifts from song energy."""
        base_user = {"genre": "pop", "mood": "happy", "target_energy": 0.80,
                     "likes_acoustic": False, "target_tempo": 0.5,
                     "target_danceability": 0.5, "wants_popular": True,
                     "wants_instrumental": False, "target_speechiness": 0.05}
        score_0, _ = score_song(base_user, pop_song_dict)               # diff=0.0
        score_1, _ = score_song(dict(base_user, target_energy=0.60), pop_song_dict)  # diff=0.2
        score_2, _ = score_song(dict(base_user, target_energy=0.40), pop_song_dict)  # diff=0.4
        assert score_0 > score_1 > score_2

    def test_reasons_list_is_non_empty(self, pop_user_dict, pop_song_dict):
        """reasons must always contain at least one entry."""
        _, reasons = score_song(pop_user_dict, pop_song_dict)
        assert len(reasons) >= 1

    def test_genre_match_string_in_reasons(self, pop_user_dict, pop_song_dict):
        """When genre matches, reasons must include a genre match string."""
        _, reasons = score_song(pop_user_dict, pop_song_dict)
        assert any("genre match" in r for r in reasons)

    def test_mood_match_string_in_reasons(self, pop_user_dict, pop_song_dict):
        """When mood matches, reasons must include a mood match string."""
        _, reasons = score_song(pop_user_dict, pop_song_dict)
        assert any("mood match" in r for r in reasons)

    def test_unknown_genre_does_not_crash(self, pop_song_dict):
        """A user genre that does not exist in the catalog must not raise an exception."""
        user = {"genre": "xyzzy-genre-that-does-not-exist", "mood": "happy",
                "target_energy": 0.5, "likes_acoustic": False, "target_tempo": 0.5,
                "target_danceability": 0.5, "wants_popular": True,
                "wants_instrumental": False, "target_speechiness": 0.05}
        score, reasons = score_song(user, pop_song_dict)
        assert isinstance(score, float)
        assert isinstance(reasons, list)

    def test_unknown_mood_does_not_crash(self, pop_song_dict):
        """A user mood that does not exist in the catalog must not raise an exception."""
        user = {"genre": "pop", "mood": "xyzzy-mood-that-does-not-exist",
                "target_energy": 0.5, "likes_acoustic": False, "target_tempo": 0.5,
                "target_danceability": 0.5, "wants_popular": True,
                "wants_instrumental": False, "target_speechiness": 0.05}
        score, reasons = score_song(user, pop_song_dict)
        assert isinstance(score, float)
        assert isinstance(reasons, list)

    def test_score_is_deterministic(self, pop_user_dict, pop_song_dict):
        """Calling score_song twice with the same inputs must return the same score."""
        score1, _ = score_song(pop_user_dict, pop_song_dict)
        score2, _ = score_song(pop_user_dict, pop_song_dict)
        assert score1 == score2

    def test_all_modes_run_without_crashing(self, pop_user_dict, pop_song_dict):
        """score_song must execute without exception for every defined scoring mode."""
        for mode in SCORING_WEIGHTS:
            score, reasons = score_song(pop_user_dict, pop_song_dict, mode=mode)
            assert isinstance(score, float)
            assert isinstance(reasons, list)

    def test_genre_first_score_higher_than_discovery_for_genre_match(
        self, pop_user_dict, pop_song_dict
    ):
        """
        GENRE_FIRST assigns 0.55 to genre vs 0.10 in DISCOVERY.
        A genre-matched song must score higher in GENRE_FIRST than DISCOVERY.
        """
        score_gf, _ = score_song(pop_user_dict, pop_song_dict, mode="GENRE_FIRST")
        score_dsc, _ = score_song(pop_user_dict, pop_song_dict, mode="DISCOVERY")
        assert score_gf > score_dsc


# ===========================================================================
# 4.  recommend_songs()
# ===========================================================================

class TestRecommendSongs:

    def test_returns_list(self, hip_hop_profile, songs):
        """recommend_songs must return a list."""
        result = recommend_songs(hip_hop_profile, songs)
        assert isinstance(result, list)

    def test_returns_5_results_by_default(self, hip_hop_profile, songs):
        """Default k=5 must return exactly 5 results from a 20-song catalog."""
        result = recommend_songs(hip_hop_profile, songs)
        assert len(result) == 5

    def test_returns_k_equals_1(self, hip_hop_profile, songs):
        """k=1 must return exactly 1 result."""
        result = recommend_songs(hip_hop_profile, songs, k=1)
        assert len(result) == 1

    def test_returns_all_songs_when_k_exceeds_catalog(self, hip_hop_profile, songs):
        """When k > catalog size, all available songs are returned."""
        result = recommend_songs(hip_hop_profile, songs, k=25)
        assert len(result) == 20

    def test_first_result_has_highest_score(self, hip_hop_profile, songs):
        """The first result must have the highest score in the returned list."""
        result = recommend_songs(hip_hop_profile, songs)
        scores = [r[1] for r in result]
        assert scores[0] == max(scores)

    def test_results_sorted_descending_by_score(self, hip_hop_profile, songs):
        """All results must be in descending score order."""
        result = recommend_songs(hip_hop_profile, songs)
        scores = [r[1] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_no_duplicate_song_ids_in_results(self, hip_hop_profile, songs):
        """Every recommended song must appear at most once (no duplicates)."""
        result = recommend_songs(hip_hop_profile, songs)
        ids = [r[0]["id"] for r in result]
        assert len(ids) == len(set(ids))

    def test_tie_breaking_by_lower_id(self, pop_user_dict):
        """When two songs have equal scores, the one with the lower id appears first."""
        # Construct two songs that are identical in every scored feature
        song_a = {
            "id": 10, "title": "Song A", "artist": "Artist X",
            "genre": "rock", "mood": "intense", "energy": 0.50,
            "tempo_bpm": 108.0, "valence": 0.50, "danceability": 0.50,
            "acousticness": 0.50, "popularity": 50,
            "instrumentalness": 0.50, "speechiness": 0.05,
        }
        song_b = {
            "id": 3, "title": "Song B", "artist": "Artist Y",
            "genre": "rock", "mood": "intense", "energy": 0.50,
            "tempo_bpm": 108.0, "valence": 0.50, "danceability": 0.50,
            "acousticness": 0.50, "popularity": 50,
            "instrumentalness": 0.50, "speechiness": 0.05,
        }
        tie_user = {
            "genre": "rock", "mood": "intense", "target_energy": 0.50,
            "likes_acoustic": True, "target_tempo": 0.50,
            "target_danceability": 0.50, "wants_popular": True,
            "wants_instrumental": False, "target_speechiness": 0.05,
        }
        result = recommend_songs(tie_user, [song_a, song_b], k=2)
        # song_b (id=3) must appear before song_a (id=10)
        assert result[0][0]["id"] == 3
        assert result[1][0]["id"] == 10

    def test_each_result_tuple_has_3_elements(self, hip_hop_profile, songs):
        """Every result tuple must have exactly 3 elements: (dict, float, str)."""
        result = recommend_songs(hip_hop_profile, songs)
        for item in result:
            assert len(item) == 3

    def test_result_tuple_first_element_is_dict(self, hip_hop_profile, songs):
        """The first element of each result tuple must be a song dict."""
        result = recommend_songs(hip_hop_profile, songs)
        for song, _, _ in result:
            assert isinstance(song, dict)

    def test_result_tuple_second_element_is_float(self, hip_hop_profile, songs):
        """The second element of each result tuple must be a float score."""
        result = recommend_songs(hip_hop_profile, songs)
        for _, score, _ in result:
            assert isinstance(score, float)

    def test_result_tuple_third_element_is_string(self, hip_hop_profile, songs):
        """The third element (explanation) of each result tuple must be a string."""
        result = recommend_songs(hip_hop_profile, songs)
        for _, _, explanation in result:
            assert isinstance(explanation, str)

    def test_reasons_preserved_in_result(self, pop_user_dict, songs):
        """The explanation string in results must be non-empty."""
        result = recommend_songs(pop_user_dict, songs, k=1)
        _, _, explanation = result[0]
        assert explanation.strip() != ""

    def test_works_with_balanced_mode(self, hip_hop_profile, songs):
        """recommend_songs must not raise an exception with mode=BALANCED."""
        result = recommend_songs(hip_hop_profile, songs, mode="BALANCED")
        assert len(result) == 5

    def test_works_with_genre_first_mode(self, hip_hop_profile, songs):
        """recommend_songs must not raise an exception with mode=GENRE_FIRST."""
        result = recommend_songs(hip_hop_profile, songs, mode="GENRE_FIRST")
        assert len(result) == 5

    def test_works_with_discovery_mode(self, hip_hop_profile, songs):
        """recommend_songs must not raise an exception with mode=DISCOVERY."""
        result = recommend_songs(hip_hop_profile, songs, mode="DISCOVERY")
        assert len(result) == 5

    def test_diversity_false_does_not_crash(self, hip_hop_profile, songs):
        """diversity=False (default) must return 5 results without error."""
        result = recommend_songs(hip_hop_profile, songs, diversity=False)
        assert len(result) == 5

    def test_diversity_true_does_not_crash(self, hip_hop_profile, songs):
        """diversity=True must return results without raising an exception."""
        result = recommend_songs(hip_hop_profile, songs, diversity=True)
        assert len(result) == 5

    def test_diversity_true_no_repeated_artists_in_top_5(self, hip_hop_profile, songs):
        """With diversity=True, no artist should appear more than once in the top-5."""
        result = recommend_songs(hip_hop_profile, songs, k=5, diversity=True)
        artists = [r[0]["artist"] for r in result]
        assert len(artists) == len(set(artists)), (
            f"Repeated artists found: {artists}"
        )

    def test_diversity_true_k1_returns_one_result(self, hip_hop_profile, songs):
        """diversity=True with k=1 must return exactly 1 result."""
        result = recommend_songs(hip_hop_profile, songs, k=1, diversity=True)
        assert len(result) == 1

    def test_diversity_penalty_reason_appears_when_artist_repeats(self, songs):
        """
        When diversity=True forces a penalty, the explanation string for the
        penalised song must contain the word 'penalty'.
        """
        # Create a catalog where all songs share the same artist to guarantee a penalty
        catalog = []
        for i in range(5):
            catalog.append({
                "id": i + 1,
                "title": f"Song {i}",
                "artist": "Same Artist",
                "genre": "pop" if i < 3 else "rock",
                "mood": "happy",
                "energy": 0.70,
                "tempo_bpm": 110.0,
                "valence": 0.70,
                "danceability": 0.70,
                "acousticness": 0.20,
                "popularity": 60,
                "instrumentalness": 0.05,
                "speechiness": 0.05,
            })
        user = {"genre": "pop", "mood": "happy", "target_energy": 0.70,
                "likes_acoustic": False, "target_tempo": 0.52,
                "target_danceability": 0.70, "wants_popular": True,
                "wants_instrumental": False, "target_speechiness": 0.05}
        result = recommend_songs(user, catalog, k=5, diversity=True)
        explanations = [r[2] for r in result]
        penalty_present = any("penalty" in e.lower() for e in explanations[1:])
        assert penalty_present, (
            "Expected at least one penalty reason after first pick with a same-artist catalog"
        )

    def test_empty_catalog_returns_empty_list(self, hip_hop_profile):
        """recommend_songs on an empty catalog must return an empty list, not raise."""
        result = recommend_songs(hip_hop_profile, [])
        assert result == []

    def test_cold_start_profile_returns_5_results(self, cold_start_profile, songs):
        """Cold-start user (no genre, no mood) must still receive 5 valid results."""
        result = recommend_songs(cold_start_profile, songs)
        assert len(result) == 5

    def test_cold_start_all_scores_are_valid_floats(self, cold_start_profile, songs):
        """All scores returned for the cold-start profile must be floats in [0.0, 1.0]."""
        result = recommend_songs(cold_start_profile, songs)
        for _, score, _ in result:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0


# ===========================================================================
# 5.  Integration tests — real catalog + real profiles
# ===========================================================================

class TestIntegration:

    def test_hip_hop_worker_rank1_is_bassline_therapy(self, hip_hop_profile, songs):
        """
        Late-Night Hip-Hop Worker must get 'Bassline Therapy' (id=11) as rank-1.
        It is the only hip-hop/focused song — both genre (0.35) and mood (0.25)
        weights align, giving it a decisive score advantage over all other songs.
        """
        result = recommend_songs(hip_hop_profile, songs, mode="BALANCED")
        assert result[0][0]["id"] == 11
        assert result[0][0]["title"] == "Bassline Therapy"

    def test_jazz_listener_rank1_is_coffee_shop_stories(self, jazz_profile, songs):
        """
        Coffeehouse Jazz Listener must get 'Coffee Shop Stories' (id=7) as rank-1.
        Only jazz/relaxed song in the catalog — genre+mood match guarantees top score.
        """
        result = recommend_songs(jazz_profile, songs, mode="BALANCED")
        assert result[0][0]["id"] == 7
        assert result[0][0]["title"] == "Coffee Shop Stories"

    def test_gym_listener_rank1_is_gym_hero(self, gym_profile, songs):
        """
        Gym Workout Listener must get 'Gym Hero' (id=5) as rank-1.
        Only pop/intense song in the catalog — full genre+mood match dominates.
        """
        result = recommend_songs(gym_profile, songs, mode="BALANCED")
        assert result[0][0]["id"] == 5
        assert result[0][0]["title"] == "Gym Hero"

    def test_electronic_user_rank1_is_pulse_sequence(self, electronic_profile, songs):
        """
        Moody Electronic User must get 'Pulse Sequence' (id=13) as rank-1.
        No song is both electronic AND moody, but id=13 is the only electronic
        song (genre weight 0.35 > mood weight 0.25), so it outscores any moody
        non-electronic song.
        """
        result = recommend_songs(electronic_profile, songs, mode="BALANCED")
        assert result[0][0]["id"] == 13
        assert result[0][0]["title"] == "Pulse Sequence"

    def test_cold_start_returns_5_results(self, cold_start_profile, songs):
        """Cold Start User must receive exactly 5 results without crashing."""
        result = recommend_songs(cold_start_profile, songs)
        assert len(result) == 5

    def test_cold_start_all_scores_valid(self, cold_start_profile, songs):
        """All scores for the Cold Start User must be floats in [0.0, 1.0]."""
        result = recommend_songs(cold_start_profile, songs)
        for _, score, _ in result:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_hip_hop_diversity_no_repeated_artists(self, hip_hop_profile, songs):
        """With diversity=True, Hip-Hop Worker top-5 must have no repeated artists."""
        result = recommend_songs(hip_hop_profile, songs, k=5, diversity=True)
        artists = [r[0]["artist"] for r in result]
        assert len(artists) == len(set(artists))

    def test_diversity_penalised_score_lower_than_base(self, hip_hop_profile, songs):
        """
        A song that receives a diversity penalty must have a lower effective
        score than its raw base score.
        """
        result_no_div = recommend_songs(hip_hop_profile, songs, k=5, diversity=False)
        result_div    = recommend_songs(hip_hop_profile, songs, k=5, diversity=True)

        base_scores_by_id = {r[0]["id"]: r[1] for r in result_no_div}
        div_scores_by_id  = {r[0]["id"]: r[1] for r in result_div}

        penalised_found = False
        for song_id, div_score in div_scores_by_id.items():
            if song_id in base_scores_by_id:
                base = base_scores_by_id[song_id]
                if div_score < base - 1e-9:
                    penalised_found = True
                    break

        assert penalised_found, (
            "Expected at least one song to receive a lower effective score "
            "under diversity=True vs diversity=False"
        )


# ===========================================================================
# 6.  Diversity constants
# ===========================================================================

class TestDiversityConstants:

    def test_artist_penalty_equals_0_80(self):
        """ARTIST_PENALTY must be exactly 0.80."""
        assert ARTIST_PENALTY == pytest.approx(0.80)

    def test_genre_penalty_equals_0_92(self):
        """GENRE_PENALTY must be exactly 0.92."""
        assert GENRE_PENALTY == pytest.approx(0.92)


# ===========================================================================
# 7.  OOP Recommender class (backward-compatibility layer)
# ===========================================================================

class TestOOPRecommender:

    def _make_recommender(self) -> Recommender:
        """Build a minimal two-song Recommender for unit tests."""
        songs = [
            Song(id=1, title="Pop Track", artist="Artist A",
                 genre="pop", mood="happy", energy=0.80, tempo_bpm=120.0,
                 valence=0.85, danceability=0.75, acousticness=0.15,
                 popularity=75, instrumentalness=0.03, speechiness=0.06),
            Song(id=2, title="Chill Lofi", artist="Artist B",
                 genre="lofi", mood="chill", energy=0.40, tempo_bpm=80.0,
                 valence=0.60, danceability=0.55, acousticness=0.80,
                 popularity=50, instrumentalness=0.45, speechiness=0.04),
        ]
        return Recommender(songs)

    def _pop_user(self) -> UserProfile:
        return UserProfile(
            favorite_genre="pop", favorite_mood="happy",
            target_energy=0.80, likes_acoustic=False,
        )

    def test_recommend_returns_list(self):
        """Recommender.recommend must return a list."""
        rec = self._make_recommender()
        result = rec.recommend(self._pop_user(), k=2)
        assert isinstance(result, list)

    def test_recommend_returns_correct_count(self):
        """Recommender.recommend must return exactly k Song objects."""
        rec = self._make_recommender()
        result = rec.recommend(self._pop_user(), k=2)
        assert len(result) == 2

    def test_recommend_top_song_matches_genre_and_mood(self):
        """Pop/happy user's top recommendation must be the pop/happy song."""
        rec = self._make_recommender()
        result = rec.recommend(self._pop_user(), k=2)
        assert result[0].genre == "pop"
        assert result[0].mood == "happy"

    def test_explain_recommendation_returns_string(self):
        """explain_recommendation must return a non-empty string."""
        rec = self._make_recommender()
        explanation = rec.explain_recommendation(self._pop_user(), rec.songs[0])
        assert isinstance(explanation, str)
        assert explanation.strip() != ""

    def test_explain_recommendation_mentions_genre(self):
        """explain_recommendation must mention the genre when it matches."""
        rec = self._make_recommender()
        explanation = rec.explain_recommendation(self._pop_user(), rec.songs[0])
        assert "genre" in explanation.lower()

    def test_explain_recommendation_mentions_mood(self):
        """explain_recommendation must mention the mood when it matches."""
        rec = self._make_recommender()
        explanation = rec.explain_recommendation(self._pop_user(), rec.songs[0])
        assert "mood" in explanation.lower()

    def test_recommender_songs_attribute_accessible(self):
        """Recommender.songs must be accessible and contain Song objects."""
        rec = self._make_recommender()
        assert len(rec.songs) == 2
        assert isinstance(rec.songs[0], Song)

    def test_song_dataclass_optional_fields_have_defaults(self):
        """Song fields added in Challenge 1 must have defaults for backward compatibility."""
        song = Song(id=99, title="Minimal", artist="X", genre="pop",
                    mood="happy", energy=0.5, tempo_bpm=100.0,
                    valence=0.5, danceability=0.5, acousticness=0.5)
        assert isinstance(song.popularity, int)
        assert isinstance(song.instrumentalness, float)
        assert isinstance(song.speechiness, float)

    def test_user_profile_optional_fields_have_defaults(self):
        """UserProfile fields added in Challenge 1 must have defaults."""
        user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                           target_energy=0.8, likes_acoustic=False)
        assert isinstance(user.target_tempo, float)
        assert isinstance(user.target_danceability, float)
        assert isinstance(user.wants_popular, bool)
        assert isinstance(user.wants_instrumental, bool)
        assert isinstance(user.target_speechiness, float)
