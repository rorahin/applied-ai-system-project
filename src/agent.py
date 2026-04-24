from typing import List, Optional

from src.user_profile import UserProfile
from src.retrieval import load_songs, retrieve_candidates
from src.recommender_engine import rank_songs, Recommendation, CONFIDENCE_THRESHOLD
from src.guardrails import validate_request, check_genre_support, check_mood_support
from src.logger import setup_logger

logger = setup_logger()

# ---------------------------------------------------------------------------
# Keyword lookup tables — longest keys are checked first so multi-word
# phrases like "high energy" beat single-word "high".
# ---------------------------------------------------------------------------

GENRE_KEYWORDS = {
    "hip-hop": "hip-hop",
    "hiphop": "hip-hop",
    "indie pop": "indie pop",
    "indie folk": "indie folk",
    "indie": "indie pop",
    "rap": "hip-hop",
    "rnb": "r&b",
    "r&b": "r&b",
    "rhythm and blues": "r&b",
    "electronica": "electronic",
    "electronic": "electronic",
    "edm": "electronic",
    "synthwave": "synthwave",
    "ambient": "ambient",
    "classical": "classical",
    "country": "country",
    "metal": "metal",
    "lofi": "lofi",
    "lo-fi": "lofi",
    "lo fi": "lofi",
    "jazz": "jazz",
    "rock": "rock",
    "pop": "pop",
}

# Maps user language → catalog moods (catalog uses: happy, chill, intense,
# relaxed, focused, moody, melancholy)
MOOD_KEYWORDS = {
    "old school": "moody",
    "oldschool": "moody",
    "throwback": "moody",
    "nostalgic": "moody",
    "melancholy": "melancholy",
    "heartbreak": "melancholy",
    "aggressive": "intense",
    "workout": "intense",
    "pumped": "intense",
    "intense": "intense",
    "energetic": "focused",
    "hype": "intense",
    "peaceful": "chill",
    "mellow": "chill",
    "relaxed": "relaxed",
    "soothing": "chill",
    "focused": "focused",
    "moody": "moody",
    "upbeat": "happy",
    "joyful": "happy",
    "cheerful": "happy",
    "happy": "happy",
    "calm": "chill",
    "chill": "chill",
    "sad": "melancholy",
    "blue": "melancholy",
}

# Maps user language → target_energy float (longest phrase wins)
ENERGY_KEYWORDS = {
    "very high energy": 0.92,
    "high energy": 0.85,
    "high-energy": 0.85,
    "low energy": 0.25,
    "low-energy": 0.25,
    "medium energy": 0.55,
}

DECADE_KEYWORDS = {
    "nineties": "1990s",
    "1990s": "1990s",
    "90s": "1990s",
    "aughts": "2000s",
    "2000s": "2000s",
    "00s": "2000s",
    "2010s": "2010s",
    "10s": "2010s",
    "2020s": "2020s",
    "20s": "2020s",
}


class AppliedMusicAgent:
    """
    Agentic controller for the full music recommendation workflow.

    Workflow:
      1. validate input
      2. parse natural language → UserProfile
      3. retrieve candidate songs (RAG-style)
      4. score and rank candidates
      5. self-check output quality
      6. return structured, human-readable results
    """

    def __init__(self, songs_path: Optional[str] = None):
        self.songs = load_songs(songs_path) if songs_path else load_songs()
        logger.info(f"Agent ready — {len(self.songs)} songs in catalog.")

    # ------------------------------------------------------------------
    # Step 2: Parse
    # ------------------------------------------------------------------

    def parse_request(self, raw_request: str) -> UserProfile:
        """Convert a natural language request string into a UserProfile."""
        text = raw_request.lower().strip()
        profile = UserProfile(raw_request=raw_request)

        # Check longest keywords first to prefer specific multi-word phrases
        for keyword in sorted(GENRE_KEYWORDS, key=len, reverse=True):
            if keyword in text:
                genre = check_genre_support(GENRE_KEYWORDS[keyword])
                if genre:
                    profile.preferred_genre = genre
                    break

        for keyword in sorted(MOOD_KEYWORDS, key=len, reverse=True):
            if keyword in text:
                mood = check_mood_support(MOOD_KEYWORDS[keyword])
                if mood:
                    profile.preferred_mood = mood
                    break

        for keyword in sorted(ENERGY_KEYWORDS, key=len, reverse=True):
            if keyword in text:
                profile.target_energy = ENERGY_KEYWORDS[keyword]
                break

        for keyword in sorted(DECADE_KEYWORDS, key=len, reverse=True):
            if keyword in text:
                profile.preferred_decade = DECADE_KEYWORDS[keyword]
                break

        if "popular" in text or "mainstream" in text:
            profile.popularity_preference = "popular"
        elif "niche" in text or "underground" in text:
            profile.popularity_preference = "niche"

        # Mark as vague when nothing useful was extracted
        profile.is_vague = not any([
            profile.preferred_genre,
            profile.preferred_mood,
            profile.target_energy,
            profile.preferred_decade,
        ])

        logger.info(
            f"Parsed — genre: {profile.preferred_genre}, mood: {profile.preferred_mood}, "
            f"energy: {profile.target_energy}, decade: {profile.preferred_decade}, "
            f"vague: {profile.is_vague}"
        )
        return profile

    # ------------------------------------------------------------------
    # Step 5: Self-check
    # ------------------------------------------------------------------

    def self_check(
        self,
        recommendations: List[Recommendation],
        retrieval_mode: str,
        profile: UserProfile,
    ) -> List[str]:
        """
        Inspect recommendation quality and return a list of warning/note strings.
        Flags: low confidence, too few results, no exact matches, fallback mode.
        """
        flags: List[str] = []

        if not recommendations:
            flags.append("WARNING: No recommendations could be generated.")
            return flags

        if len(recommendations) < 3:
            flags.append(
                f"WARNING: Only {len(recommendations)} result(s) found — "
                "catalog may be too small for this query."
            )

        all_low = all(r.confidence == "low" for r in recommendations)
        if all_low:
            flags.append("WARNING: All results have LOW confidence — weak match to your preferences.")

        top_score = recommendations[0].score
        if top_score < CONFIDENCE_THRESHOLD:
            flags.append(
                f"WARNING: Best match score is {top_score:.2f} — no strong matches found."
            )

        if retrieval_mode == "fallback":
            if profile.is_vague:
                flags.append("NOTE: Request was vague — showing a diverse fallback selection.")
            else:
                flags.append(
                    "NOTE: No catalog songs matched your preferences — "
                    "showing fallback recommendations."
                )

        if profile.preferred_genre and not any(
            r.song.genre == profile.preferred_genre for r in recommendations
        ):
            flags.append(
                f"NOTE: Genre '{profile.preferred_genre}' is not represented in top results."
            )

        if profile.preferred_mood and not any(
            r.song.mood == profile.preferred_mood for r in recommendations
        ):
            flags.append(
                f"NOTE: Mood '{profile.preferred_mood}' is not represented in top results."
            )

        return flags

    # ------------------------------------------------------------------
    # Step 6: Format
    # ------------------------------------------------------------------

    def format_results(
        self,
        recommendations: List[Recommendation],
        flags: List[str],
        retrieval_mode: str,
    ) -> str:
        lines = ["=" * 70, "  MUSIC RECOMMENDATIONS", "=" * 70]

        if flags:
            for flag in flags:
                lines.append(f"  {flag}")
            lines.append("")

        if not recommendations:
            lines.append("  No recommendations available.")
            lines.append("=" * 70)
            return "\n".join(lines)

        lines.append(f"  Retrieval mode: {retrieval_mode.upper()}")
        lines.append("")

        for i, rec in enumerate(recommendations, start=1):
            lines.append(f"  {i}. {rec.song.title} — {rec.song.artist}")
            lines.append(
                f"     Genre: {rec.song.genre}  |  Mood: {rec.song.mood}  |  Decade: {rec.song.decade}"
            )
            lines.append(
                f"     Score: {rec.score:.4f}  |  Confidence: {rec.confidence.upper()}"
            )
            lines.append(f"     Why: {rec.explanation}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, user_request: str) -> str:
        """
        Execute the full agentic workflow for a user request.
        Returns a formatted, human-readable recommendation string.
        """
        logger.info(f"--- New request: '{user_request}' ---")

        # 1. Validate
        is_valid, error_msg = validate_request(user_request)
        if not is_valid:
            logger.warning(f"Rejected: {error_msg}")
            return f"[Input Error] {error_msg}"

        # 2. Parse
        profile = self.parse_request(user_request)

        # 3. Retrieve
        candidates, retrieval_mode = retrieve_candidates(profile, self.songs)
        logger.info(f"Retrieved {len(candidates)} candidates (mode: {retrieval_mode}).")
        if not candidates:
            return "[Error] The song catalog is empty."

        # 4. Score & rank
        recommendations = rank_songs(candidates, profile, top_k=5)

        # 5. Self-check
        flags = self.self_check(recommendations, retrieval_mode, profile)
        for flag in flags:
            logger.warning(flag)

        # 6. Format and return
        result = self.format_results(recommendations, flags, retrieval_mode)
        logger.info("Run complete.")
        return result
