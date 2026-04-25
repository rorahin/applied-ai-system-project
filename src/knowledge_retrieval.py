"""
Knowledge retrieval for the Applied AI Music Recommendation System.

Loads docs/music_knowledge_base.md and retrieves relevant guidance snippets
based on a user request. Matched entries augment a UserProfile with dimensions
the keyword parser did not extract, improving retrieval and scoring quality.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.logger import setup_logger

logger = setup_logger()

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_KB_PATH = os.path.join(_PROJECT_ROOT, "docs", "music_knowledge_base.md")


@dataclass
class KnowledgeEntry:
    """One parsed entry from the knowledge base."""
    name: str
    keywords: List[str]
    energy: Optional[float] = None
    mood: Optional[str] = None
    decade: Optional[str] = None
    note: str = ""


def load_knowledge_base(path: str = DEFAULT_KB_PATH) -> List[KnowledgeEntry]:
    """
    Parse music_knowledge_base.md into a list of KnowledgeEntry objects.

    Splits on level-3 markdown headers (### entry-name) and reads
    bullet-point fields for keywords, energy, mood, decade, and note.
    Returns an empty list if the file is not found.
    """
    entries: List[KnowledgeEntry] = []

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logger.warning(f"Knowledge base not found: {path}")
        return entries

    sections = re.split(r"^### ", content, flags=re.MULTILINE)

    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().splitlines()
        name = lines[0].strip()

        keywords: List[str] = []
        energy: Optional[float] = None
        mood: Optional[str] = None
        decade: Optional[str] = None
        note: str = ""

        for line in lines[1:]:
            if "**keywords**" in line:
                raw = line.split(":", 1)[-1].strip()
                keywords = [k.strip() for k in raw.split(",") if k.strip()]
            elif "**energy**" in line:
                raw_energy = line.split(":", 1)[-1].strip()
                if raw_energy:
                    try:
                        energy = float(raw_energy)
                    except ValueError:
                        pass
            elif "**mood**" in line:
                raw_mood = line.split(":", 1)[-1].strip()
                if raw_mood:
                    mood = raw_mood
            elif "**decade**" in line:
                raw_decade = line.split(":", 1)[-1].strip()
                if raw_decade:
                    decade = raw_decade
            elif "**note**" in line:
                note = line.split(":", 1)[-1].strip()

        if name and keywords:
            entries.append(KnowledgeEntry(
                name=name,
                keywords=keywords,
                energy=energy,
                mood=mood,
                decade=decade,
                note=note,
            ))

    logger.info(f"Knowledge base loaded: {len(entries)} entries.")
    return entries


def retrieve_snippets(
    user_request: str,
    kb_path: str = DEFAULT_KB_PATH,
) -> Tuple[List[str], List[KnowledgeEntry]]:
    """
    Match a user request against knowledge base keywords.

    Returns a tuple of:
        - snippet_strings: human-readable guidance lines for display
        - matched_entries: structured entries for profile augmentation

    Each entry matches at most once even if multiple keywords hit.
    """
    entries = load_knowledge_base(kb_path)
    text = user_request.lower()

    snippets: List[str] = []
    matched: List[KnowledgeEntry] = []

    for entry in entries:
        for keyword in entry.keywords:
            if keyword.lower() in text:
                snippets.append(f"{entry.name}: {entry.note}")
                matched.append(entry)
                break

    return snippets, matched


def apply_knowledge_hints(profile, matched_entries: List[KnowledgeEntry]) -> List[str]:
    """
    Augment a UserProfile using matched knowledge entries.

    Only fills in dimensions the parser left as None — never overwrites
    a value the parser already set.

    Returns a list of human-readable applied-hint descriptions for the
    agent reasoning trace.
    """
    applied: List[str] = []

    for entry in matched_entries:
        if entry.energy is not None and profile.target_energy is None:
            profile.target_energy = entry.energy
            applied.append(f"energy → {entry.energy:.2f} (from '{entry.name}' knowledge)")

        if entry.mood and profile.preferred_mood is None:
            profile.preferred_mood = entry.mood
            applied.append(f"mood → '{entry.mood}' (from '{entry.name}' knowledge)")

        if entry.decade and profile.preferred_decade is None:
            profile.preferred_decade = entry.decade
            applied.append(f"decade → '{entry.decade}' (from '{entry.name}' knowledge)")

    # Recompute is_vague: hints may have filled dimensions the parser left empty
    if applied:
        profile.is_vague = not any([
            profile.preferred_genre,
            profile.preferred_mood,
            profile.target_energy,
            profile.preferred_decade,
        ])

    return applied
