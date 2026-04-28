from typing import List, Optional

from src.user_profile import UserProfile
from src.retrieval import load_songs, retrieve_candidates
from src.recommender_engine import rank_songs, Recommendation, CONFIDENCE_THRESHOLD
from src.guardrails import validate_request, check_genre_support, check_mood_support
from src.knowledge_retrieval import retrieve_snippets, apply_knowledge_hints
from src.specialization import apply_style, validate_style
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
      2. retrieve knowledge snippets (RAG enhancement)
      3. parse natural language → UserProfile
      4. apply knowledge hints to augment profile
      5. retrieve candidate songs (RAG-style)
      6. score and rank candidates
      7. self-check output quality
      8. return structured, human-readable results

    Optional parameters on run():
      show_steps=True  — append an Agent Reasoning Trace to the output
      style            — "default" | "professional" | "casual" | "technical"
    """

    def __init__(self, songs_path: Optional[str] = None):
        self.songs = load_songs(songs_path) if songs_path else load_songs()
        logger.info(f"Agent ready — {len(self.songs)} songs in catalog.")

    # ------------------------------------------------------------------
    # Step 3: Parse
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
    # Step 7: Self-check
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
                flags.append("IMPORTANT NOTE: Request was vague — showing a diverse fallback selection.")
            else:
                flags.append(
                    "IMPORTANT NOTE: No catalog songs matched your preferences — "
                    "showing fallback recommendations."
                )

        if profile.preferred_genre and not any(
            r.song.genre == profile.preferred_genre for r in recommendations
        ):
            flags.append(
                f"IMPORTANT NOTE: Genre '{profile.preferred_genre}' is not represented in top results."
            )

        if profile.preferred_mood and not any(
            r.song.mood == profile.preferred_mood for r in recommendations
        ):
            flags.append(
                f"IMPORTANT NOTE: Mood '{profile.preferred_mood}' is not represented in top results."
            )

        return flags

    # ------------------------------------------------------------------
    # Step 8: Format
    # ------------------------------------------------------------------

    def format_results(
        self,
        recommendations: List[Recommendation],
        flags: List[str],
        retrieval_mode: str,
        style: str = "default",
        knowledge_note: Optional[str] = None,
    ) -> str:
        lines = ["=" * 70, "  MUSIC RECOMMENDATIONS", "=" * 70]

        if flags:
            for flag in flags:
                if flag.startswith("IMPORTANT NOTE:"):
                    lines.append("")
                    lines.append("  " + "!" * 66)
                    lines.append(f"  !!!  {flag}  !!!")
                    lines.append("  " + "!" * 66)
                else:
                    lines.append(f"  {flag}")
            lines.append("")

        if not recommendations:
            lines.append("  No recommendations available.")
            lines.append("=" * 70)
            return "\n".join(lines)

        lines.append(f"  Retrieval mode: {retrieval_mode.upper()}")
        if knowledge_note:
            lines.append(f"  {knowledge_note}")
        lines.append("")

        for i, rec in enumerate(recommendations, start=1):
            lines.append(f"  {i}. {rec.song.title} — {rec.song.artist}")
            lines.append(
                f"     Genre: {rec.song.genre}  |  Mood: {rec.song.mood}  |  Decade: {rec.song.decade}"
            )
            lines.append(
                f"     Score: {rec.score:.4f}  |  Confidence: {rec.confidence.upper()}"
            )
            styled_explanation = apply_style(rec.explanation, style)
            lines.append(f"     Why: {styled_explanation}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        user_request: str,
        show_steps: bool = False,
        style: str = "default",
    ) -> str:
        """
        Execute the full agentic workflow for a user request.

        Args:
            user_request: natural language music preference string
            show_steps:   when True, appends a structured Agent Reasoning Trace
            style:        output style — "default", "professional", "casual", "technical"

        Returns a formatted, human-readable recommendation string.
        """
        style = validate_style(style)
        trace: List[str] = []

        logger.info(f"--- New request: '{user_request}' ---")

        # 1. Validate
        is_valid, error_msg = validate_request(user_request)
        if not is_valid:
            logger.warning(f"Rejected: {error_msg}")
            return f"[Input Error] {error_msg}"

        if show_steps:
            trace.append("1. Validation: PASSED")

        # 2. Retrieve knowledge snippets
        snippets, matched_entries = retrieve_snippets(user_request)

        # 3. Parse
        profile = self.parse_request(user_request)

        # 4. Apply knowledge hints (fills dimensions the parser left as None)
        applied_hints = apply_knowledge_hints(profile, matched_entries)

        if show_steps:
            trace.append(
                f"2. Parsed preferences — genre: {profile.preferred_genre}, "
                f"mood: {profile.preferred_mood}, energy: {profile.target_energy}, "
                f"decade: {profile.preferred_decade}, vague: {profile.is_vague}"
            )
            if snippets:
                trace.append(f"3. Knowledge snippets: {len(snippets)} matched")
                for s in snippets:
                    trace.append(f"   - {s}")
                if applied_hints:
                    for h in applied_hints:
                        trace.append(f"   + Applied: {h}")
            else:
                trace.append("3. Knowledge snippets: none matched")

        # 5. Retrieve
        candidates, retrieval_mode = retrieve_candidates(profile, self.songs)
        logger.info(f"Retrieved {len(candidates)} candidates (mode: {retrieval_mode}).")

        if show_steps:
            trace.append(
                f"4. Retrieval mode: {retrieval_mode.upper()}, "
                f"candidates: {len(candidates)}"
            )

        if not candidates:
            return "[Error] The song catalog is empty."

        # 6. Score & rank
        recommendations = rank_songs(candidates, profile, top_k=5)

        if show_steps:
            conf_summary = ", ".join(r.confidence.upper() for r in recommendations)
            trace.append(
                "5. Scoring strategy: weighted formula "
                "(genre 30%, mood 30%, energy 20%, popularity 10%, decade 10%)"
            )
            trace.append(f"6. Confidence summary: [{conf_summary}]")

        # 7. Self-check
        flags = self.self_check(recommendations, retrieval_mode, profile)
        for flag in flags:
            logger.warning(flag)

        if show_steps:
            if flags:
                trace.append(f"7. Self-check: {len(flags)} warning(s)")
                for f in flags:
                    trace.append(f"   - {f}")
            else:
                trace.append("7. Self-check: no warnings")
            top_score = recommendations[0].score if recommendations else 0.0
            trace.append(
                f"8. Decision: returning {len(recommendations)} recommendation(s), "
                f"top score {top_score:.4f}"
            )

        # 8. Format and return
        knowledge_note = None
        if snippets:
            names = "; ".join(s.split(":")[0] for s in snippets)
            knowledge_note = f"Knowledge used: {names}"

        result = self.format_results(
            recommendations, flags, retrieval_mode,
            style=style,
            knowledge_note=knowledge_note,
        )

        if show_steps and trace:
            trace_block = "\n".join(
                ["", "=" * 70, "  AGENT REASONING TRACE", "=" * 70]
                + [f"  {line}" for line in trace]
                + ["=" * 70]
            )
            result = result + trace_block

        logger.info("Run complete.")
        return result
