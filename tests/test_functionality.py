"""
Functionality tests for the Applied AI Music Recommendation System.

All tests use a self-contained in-memory fixture (tmp CSV) so they are
isolated from the real songs.csv and pass deterministically.
"""

import pytest

from src.agent import AppliedMusicAgent
from src.guardrails import deduplicate_songs, validate_request, validate_song
from src.recommender_engine import get_confidence, rank_songs, score_song
from src.song import Song
from src.user_profile import UserProfile


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_songs():
    """Minimal five-song catalog covering several genres, moods, and decades."""
    return [
        Song(id=1, title="Rock Anthem",    artist="Band A",   genre="rock",       mood="intense",   energy=0.90, popularity=80, decade="2010s"),
        Song(id=2, title="Chill Vibes",    artist="Artist B", genre="lofi",       mood="chill",     energy=0.30, popularity=60, decade="2010s"),
        Song(id=3, title="Happy Days",     artist="Pop Star", genre="pop",        mood="happy",     energy=0.70, popularity=90, decade="2020s"),
        Song(id=4, title="Sad Song",       artist="Artist C", genre="indie folk", mood="melancholy",energy=0.40, popularity=55, decade="2000s"),
        Song(id=5, title="Nostalgic Rock", artist="Band B",   genre="rock",       mood="moody",     energy=0.75, popularity=85, decade="1990s"),
    ]


@pytest.fixture
def agent(tmp_path, sample_songs):
    """Return an AppliedMusicAgent backed by a temporary five-song CSV."""
    csv_path = tmp_path / "songs.csv"
    header = "id,title,artist,genre,mood,energy,popularity,decade"
    rows = [header]
    for s in sample_songs:
        rows.append(
            f"{s.id},{s.title},{s.artist},{s.genre},{s.mood},{s.energy},{s.popularity},{s.decade}"
        )
    csv_path.write_text("\n".join(rows))
    return AppliedMusicAgent(songs_path=str(csv_path))


# ---------------------------------------------------------------------------
# 1. Normal recommendation request
# ---------------------------------------------------------------------------


class TestNormalRequest:
    def test_returns_recommendation_block(self, agent):
        result = agent.run("I want rock music")
        assert "MUSIC RECOMMENDATIONS" in result

    def test_result_contains_score(self, agent):
        result = agent.run("I want chill music")
        assert "Score:" in result

    def test_result_contains_confidence(self, agent):
        result = agent.run("Give me happy pop music")
        assert "Confidence:" in result

    def test_result_contains_explanation(self, agent):
        result = agent.run("I want rock music")
        assert "Why:" in result

    def test_genre_match_appears_in_output(self, agent):
        result = agent.run("I want rock music")
        assert "genre match" in result.lower() or "rock" in result.lower()

    def test_returns_string_type(self, agent):
        result = agent.run("calm music from the 2010s")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# 2. Empty input handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    def test_empty_string_returns_error(self, agent):
        result = agent.run("")
        assert "Input Error" in result or "Error" in result.lower()

    def test_whitespace_only_returns_error(self, agent):
        result = agent.run("   ")
        assert "Error" in result

    def test_empty_does_not_raise(self, agent):
        try:
            agent.run("")
        except Exception as exc:
            pytest.fail(f"run('') raised an exception: {exc}")

    def test_validate_request_rejects_empty(self):
        valid, msg = validate_request("")
        assert valid is False
        assert len(msg) > 0

    def test_validate_request_rejects_whitespace(self):
        valid, _ = validate_request("   ")
        assert valid is False

    def test_validate_request_accepts_normal_input(self):
        valid, _ = validate_request("I want rock music")
        assert valid is True


# ---------------------------------------------------------------------------
# 3. Unknown / unsupported genre
# ---------------------------------------------------------------------------


class TestUnknownGenre:
    def test_unknown_genre_does_not_crash(self, agent):
        try:
            agent.run("I want dragoncore spaceship music")
        except Exception as exc:
            pytest.fail(f"Unknown genre raised an exception: {exc}")

    def test_unknown_genre_returns_string(self, agent):
        result = agent.run("I want dragoncore spaceship music")
        assert isinstance(result, str) and len(result) > 0

    def test_unknown_genre_uses_fallback(self, agent):
        result = agent.run("I want dragoncore spaceship music")
        assert "fallback" in result.lower() or "MUSIC RECOMMENDATIONS" in result

    def test_vague_request_still_returns_songs(self, agent):
        result = agent.run("I want dragoncore spaceship music")
        assert "Score:" in result


# ---------------------------------------------------------------------------
# 4. Duplicate song removal
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_exact_duplicates_are_removed(self):
        songs = [
            Song(id=1, title="Same Song", artist="Same Artist", genre="pop", mood="happy", energy=0.5, popularity=70, decade="2010s"),
            Song(id=2, title="Same Song", artist="Same Artist", genre="pop", mood="happy", energy=0.5, popularity=70, decade="2010s"),
            Song(id=3, title="Other Song", artist="Other Artist", genre="rock", mood="intense", energy=0.8, popularity=65, decade="2010s"),
        ]
        result = deduplicate_songs(songs)
        assert len(result) == 2

    def test_unique_songs_all_preserved(self):
        songs = [
            Song(id=1, title="Song A", artist="Artist A", genre="pop",  mood="happy",   energy=0.5, popularity=70, decade="2010s"),
            Song(id=2, title="Song B", artist="Artist B", genre="rock", mood="intense", energy=0.8, popularity=65, decade="2010s"),
        ]
        result = deduplicate_songs(songs)
        assert len(result) == 2

    def test_case_insensitive_dedup(self):
        songs = [
            Song(id=1, title="song one", artist="artist a", genre="pop", mood="happy", energy=0.5, popularity=70, decade="2010s"),
            Song(id=2, title="Song One", artist="Artist A", genre="pop", mood="happy", energy=0.5, popularity=70, decade="2010s"),
        ]
        result = deduplicate_songs(songs)
        assert len(result) == 1

    def test_dedup_preserves_first_occurrence(self):
        songs = [
            Song(id=1, title="Same", artist="Same", genre="pop", mood="happy", energy=0.5, popularity=70, decade="2010s"),
            Song(id=2, title="Same", artist="Same", genre="pop", mood="happy", energy=0.5, popularity=70, decade="2010s"),
        ]
        result = deduplicate_songs(songs)
        assert result[0].id == 1


# ---------------------------------------------------------------------------
# 5. Scoring returns ranked results
# ---------------------------------------------------------------------------


class TestScoring:
    def test_score_returns_tuple(self, sample_songs):
        profile = UserProfile(preferred_genre="rock")
        score, explanation = score_song(sample_songs[0], profile)
        assert isinstance(score, float)
        assert isinstance(explanation, str)

    def test_score_is_in_valid_range(self, sample_songs):
        profile = UserProfile(preferred_genre="rock", preferred_mood="intense", target_energy=0.9)
        for song in sample_songs:
            score, _ = score_song(song, profile)
            assert 0.0 <= score <= 1.0, f"Score {score} out of [0,1] for {song.title}"

    def test_genre_match_beats_genre_mismatch(self, sample_songs):
        profile = UserProfile(preferred_genre="rock")
        rock_song = sample_songs[0]        # genre="rock"
        lofi_song = sample_songs[1]        # genre="lofi"
        rock_score, _ = score_song(rock_song, profile)
        lofi_score, _ = score_song(lofi_song, profile)
        assert rock_score > lofi_score

    def test_rank_returns_list(self, sample_songs):
        profile = UserProfile(preferred_genre="rock")
        result = rank_songs(sample_songs, profile, top_k=3)
        assert isinstance(result, list)

    def test_rank_respects_top_k(self, sample_songs):
        profile = UserProfile(preferred_genre="pop")
        result = rank_songs(sample_songs, profile, top_k=2)
        assert len(result) <= 2

    def test_rank_is_sorted_descending(self, sample_songs):
        profile = UserProfile(preferred_genre="rock", preferred_mood="intense")
        result = rank_songs(sample_songs, profile, top_k=5)
        scores = [r.score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_confidence_high_for_score_above_75(self):
        assert get_confidence(0.80) == "high"

    def test_confidence_medium_for_score_50_to_75(self):
        assert get_confidence(0.60) == "medium"

    def test_confidence_low_for_score_below_50(self):
        assert get_confidence(0.40) == "low"


# ---------------------------------------------------------------------------
# 6. Explanations are included
# ---------------------------------------------------------------------------


class TestExplanations:
    def test_explanation_is_non_empty(self, sample_songs):
        profile = UserProfile(preferred_genre="rock")
        _, explanation = score_song(sample_songs[0], profile)
        assert len(explanation) > 0

    def test_genre_match_mentioned_in_explanation(self, sample_songs):
        profile = UserProfile(preferred_genre="rock")
        _, explanation = score_song(sample_songs[0], profile)  # rock song
        assert "genre match" in explanation

    def test_mood_match_mentioned_in_explanation(self, sample_songs):
        profile = UserProfile(preferred_mood="chill")
        _, explanation = score_song(sample_songs[1], profile)  # chill song
        assert "mood match" in explanation

    def test_agent_output_contains_why(self, agent):
        result = agent.run("I want happy music")
        assert "Why:" in result

    def test_agent_output_contains_genre_field(self, agent):
        result = agent.run("I want pop music")
        assert "Genre:" in result


# ---------------------------------------------------------------------------
# 7. Vague request uses fallback
# ---------------------------------------------------------------------------


class TestVagueBehavior:
    def test_vague_request_marked_as_vague(self, agent):
        profile = agent.parse_request("I want dragoncore spaceship music")
        assert profile.is_vague is True

    def test_specific_request_not_marked_vague(self, agent):
        profile = agent.parse_request("I want nostalgic rock")
        assert profile.is_vague is False

    def test_vague_request_returns_recommendations(self, agent):
        result = agent.run("I want dragoncore spaceship music")
        assert "Score:" in result

    def test_fallback_note_appears_for_vague_request(self, agent):
        result = agent.run("something something xyz")
        assert "fallback" in result.lower() or "vague" in result.lower()

    def test_empty_preferences_returns_results(self, agent):
        # When nothing is parsed, the system should still return songs
        result = agent.run("just give me something good")
        assert "Score:" in result


# ---------------------------------------------------------------------------
# 8. Guardrail edge cases
# ---------------------------------------------------------------------------


class TestGuardrails:
    def test_validate_song_rejects_missing_decade(self):
        row = {"id": "1", "title": "T", "artist": "A", "genre": "pop",
               "mood": "happy", "energy": "0.5", "popularity": "70", "decade": ""}
        valid, msg = validate_song(row)
        assert valid is False

    def test_validate_song_rejects_bad_energy(self):
        row = {"id": "1", "title": "T", "artist": "A", "genre": "pop",
               "mood": "happy", "energy": "1.5", "popularity": "70", "decade": "2020s"}
        valid, msg = validate_song(row)
        assert valid is False

    def test_validate_song_rejects_bad_popularity(self):
        row = {"id": "1", "title": "T", "artist": "A", "genre": "pop",
               "mood": "happy", "energy": "0.5", "popularity": "150", "decade": "2020s"}
        valid, msg = validate_song(row)
        assert valid is False

    def test_validate_song_accepts_valid_row(self):
        row = {"id": "1", "title": "T", "artist": "A", "genre": "pop",
               "mood": "happy", "energy": "0.5", "popularity": "70", "decade": "2020s"}
        valid, _ = validate_song(row)
        assert valid is True
