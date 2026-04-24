# Applied AI Music Recommendation System

## Project Summary

A content-based music recommendation system that accepts natural-language requests, parses them
into structured preference profiles, retrieves candidate songs from a local catalog, and returns
ranked recommendations with plain-language explanations.

The system demonstrates three applied AI techniques in a single, testable pipeline: RAG-style
retrieval, an agentic multi-step workflow, and a reliability layer with guardrails, structured
logging, and automated tests. Each recommendation includes a score, a confidence label, and a
"Why" explanation that makes the system's reasoning transparent rather than opaque.

Real-world music platforms like Spotify and YouTube use collaborative filtering and content-based
models at scale. This system focuses on the content-based side: matching song attributes to user
preferences using a transparent weighted formula — a scaled-down version of production logic that
is fully inspectable and testable.

---

## Original Project Reference

This project extends the **Music Recommender Simulation**, a baseline content-based recommender
that scored songs against a fixed user profile using nine acoustic features (genre, mood, energy,
acousticness, tempo, danceability, popularity, instrumentalness, and speechiness). The simulation
used a static `UserProfile` object and a single weighted-sum formula with five named scoring modes
(BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED, DISCOVERY).

The Applied AI System replaces the static profile with natural-language parsing, adds RAG-style
retrieval, and wraps the pipeline in an agentic controller with self-checking and structured
output. The original simulation's 96 tests remain in `tests/test_recommender.py` and continue to
pass alongside the new test suite.

---

## Architecture Overview

The system runs a six-step pipeline on every request:

1. **Validate** — guardrails reject empty, whitespace-only, or too-short input before it reaches the pipeline
2. **Parse** — natural language is mapped to a structured `UserProfile` (genre, mood, energy, decade) using keyword tables
3. **Retrieve** — the catalog is pre-filtered using a three-tier RAG-style strategy (EXACT, PARTIAL, or FALLBACK) before scoring
4. **Score** — each candidate song is scored with a five-dimension weighted formula and assigned a confidence label
5. **Self-check** — the agent inspects its own output for quality issues (low confidence, too few results, fallback mode, missing genre or mood in top results)
6. **Format** — results are assembled into a structured, human-readable block with score, confidence, and a "Why" explanation per song

![System Architecture](assets/system_architecture.png)

Full component reference and data flow details: [docs/architecture.md](docs/architecture.md)

---

## Setup Instructions

Requirements: Python 3.8+

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd applied-ai-system-project

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Mac / Linux
# .venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the interactive recommender
python3 main.py

# 5. Run all tests
pytest

# 6. Run the clean test summary
python3 tests/run_tests.py
```

Expected test result: **139 passed**

---

## Sample Interactions

All outputs below are real terminal output from `python3 main.py`.

![System running with 139 tests passing](assets/step-1.png)

---

### Input 1: Specific genre, mood, and energy

```text
What kind of music are you looking for? I want nostalgic rock with high energy
```

```text
======================================================================
  MUSIC RECOMMENDATIONS
======================================================================
  Retrieval mode: PARTIAL

  1. Storm Runner — Voltline
     Genre: rock  |  Mood: intense  |  Decade: 2010s
     Score: 0.6040  |  Confidence: MEDIUM
     Why: genre match (rock) | mood mismatch (intense ≠ moody) | energy 0.91 (target 0.85) | popularity 66

  2. Late Night Kings — Cipher Block
     Genre: hip-hop  |  Mood: moody  |  Decade: 2010s
     Score: 0.5960  |  Confidence: MEDIUM
     Why: genre mismatch (hip-hop ≠ rock) | mood match (moody) | energy 0.74 (target 0.85) | popularity 68

  3. Night Drive Loop — Neon Echo
     Genre: synthwave  |  Mood: moody  |  Decade: 2010s
     Score: 0.5870  |  Confidence: MEDIUM
     Why: genre mismatch (synthwave ≠ rock) | mood match (moody) | energy 0.75 (target 0.85) | popularity 57

======================================================================
```

PARTIAL retrieval mode activated because "nostalgic" maps to mood `moody` and "rock" maps to genre
`rock`, but the catalog has no song with both attributes. The parser extracted three signals from
one sentence (genre, mood, energy), and the scorer surfaced the closest matches with full
transparency on every mismatch.

---

### Input 2: Exact genre and mood match

```text
What kind of music are you looking for? give me chill lofi music from the 2010s
```

```text
======================================================================
  MUSIC RECOMMENDATIONS
======================================================================
  WARNING: Only 2 result(s) found — catalog may be too small for this query.

  Retrieval mode: EXACT

  1. Midnight Coding — LoRoom
     Genre: lofi  |  Mood: chill  |  Decade: 2010s
     Score: 0.8550  |  Confidence: HIGH
     Why: genre match (lofi) | mood match (chill) | popularity 55 | decade match (2010s)

  2. Library Rain — Paper Lanterns
     Genre: lofi  |  Mood: chill  |  Decade: 2010s
     Score: 0.8480  |  Confidence: HIGH
     Why: genre match (lofi) | mood match (chill) | popularity 48 | decade match (2010s)

======================================================================
```

EXACT retrieval mode activated because genre, mood, and decade were all specified and matched. Both
results received HIGH confidence. The self-check correctly flagged that only 2 results were
returned — a real signal that the 20-song catalog is the limiting factor, not the algorithm.

---

### Input 3: Unrecognized request (fallback)

```text
What kind of music are you looking for? I want dragoncore spaceship music
```

```text
======================================================================
  MUSIC RECOMMENDATIONS
======================================================================
  NOTE: Request was vague — showing a diverse fallback selection.

  Retrieval mode: FALLBACK

  1. Gym Hero — Max Pulse
     Genre: pop  |  Mood: intense  |  Decade: 2020s
     Score: 0.5320  |  Confidence: MEDIUM
     Why: popularity 82

  2. Sunrise City — Neon Echo
     Genre: pop  |  Mood: happy  |  Decade: 2020s
     Score: 0.5280  |  Confidence: MEDIUM
     Why: popularity 78

  3. Sugar & Smoke — Redd Velvet
     Genre: r&b  |  Mood: happy  |  Decade: 2020s
     Score: 0.5270  |  Confidence: MEDIUM
     Why: popularity 77

  4. Bassline Therapy — Flow State
     Genre: hip-hop  |  Mood: focused  |  Decade: 2010s
     Score: 0.5240  |  Confidence: MEDIUM
     Why: popularity 74

  5. Pulse Sequence — Grid Voltage
     Genre: electronic  |  Mood: intense  |  Decade: 2020s
     Score: 0.5210  |  Confidence: MEDIUM
     Why: popularity 71

======================================================================
```

The parser extracted nothing recognizable and marked the request as vague. The agent activated
FALLBACK mode and returned the full catalog ranked by popularity alone — all other preference
weights defaulted to their neutral 0.5 contribution. The self-check surfaced the vague status
explicitly rather than returning results silently.

---

## Design Decisions

### Content-based approach

Content-based filtering matches item attributes directly to a user's stated preferences without
requiring user history or behavior data. This was the appropriate choice for a system with a static
catalog and no feedback loop — it makes the scoring logic fully inspectable and deterministic.

### RAG-style retrieval

Scoring every song in the catalog on every request does not scale and can surface irrelevant
results when preferences are specific. Pre-filtering the catalog before scoring
(EXACT → PARTIAL → FALLBACK) reduces the candidate set to the most relevant songs first. This
mirrors how production retrieval-augmented systems work: retrieve a focused set, then rank within
it. The retrieval mode is surfaced to the user in every output so the reasoning path is visible.

### Agentic workflow

Wrapping the pipeline in `AppliedMusicAgent` rather than a single scoring function creates clear
separation between steps, makes each stage independently testable, and enables the self-check step
to inspect its own output before returning it. The agent can reason about result quality — low
confidence, fallback mode, small result set — and surface those signals explicitly rather than
returning results with no context.

### Trade-offs

- The catalog contains 20 songs. Retrieval mode and confidence labels are accurate, but result
  diversity is limited by catalog size, not by the algorithm.
- There is no ML model. The scoring formula is hand-tuned and static. It does not learn from user
  behavior or adapt across sessions.
- Genre and mood matching is binary (exact string comparison). Adjacent genres such as "rock" and
  "indie rock" receive zero partial credit, which can produce unexpected mismatches.
- The parser uses keyword tables. Phrasing not covered by the tables is silently ignored, which can
  cause under-parsing on complex or unusual requests.

---

## Testing Summary

**Framework:** pytest

**Total tests:** 139 — 43 new functionality tests (`tests/test_functionality.py`) and 96 original
simulation tests (`tests/test_recommender.py`)

**Test categories (functionality suite):**

- `TestGuardrails` — validates that empty, whitespace-only, and malformed inputs are rejected
  before reaching the pipeline; also tests CSV row validation (bad energy value, bad popularity
  value, missing decade field)
- `TestScoring` — verifies that the weighted formula produces scores in [0.0, 1.0], that genre
  matches outrank mismatches, that results are sorted descending, and that confidence labels map
  correctly to score thresholds
- `TestDeduplication` — confirms that exact and case-insensitive duplicate songs are removed and
  that the first occurrence is always preserved
- `TestVagueBehavior` — checks that unrecognized requests are flagged as vague, that FALLBACK mode
  activates, and that results still return rather than crashing
- `TestExplanations` — asserts that every recommendation includes a non-empty explanation string
  and that genre and mood matches are named explicitly in the "Why" field
- `TestNormalRequest` — end-to-end output format checks: MUSIC RECOMMENDATIONS header, Score,
  Confidence, Why fields present, and correct return type
- `TestEmptyInput` — empty and whitespace-only strings return an error message without raising an
  exception
- `TestUnknownGenre` — unrecognized genres fall back gracefully without crashing

**Failures encountered:** None. All 139 tests passed on first full run after the pipeline was
complete.

**What the tests revealed:** The deduplication tests surfaced a design question early — should
deduplication happen at load time or query time? Keeping it in `load_songs()` is more efficient
and easier to test in isolation, so that became the decision. The self-check tests confirmed that
quality warnings (low confidence, fallback mode, small result set) are surfaced explicitly rather
than silently absorbed.

Run the clean summary:

```bash
python3 tests/run_tests.py
```

---

## Reflection

Building this system made the gap between "a script that recommends songs" and "a system with
observable, testable reasoning" concrete. A simple script returns results. A system with
guardrails, structured logging, self-checking, and 139 automated tests makes it possible to trust
what the results mean and understand why they change when something in the pipeline shifts.

Explainability turned out to be a design constraint, not a feature added at the end. Because every
recommendation had to include a "Why" string, the scoring function had to track which sub-scores
fired and why — not just return a number. That requirement shaped the data model from the beginning
and made the system easier to debug and test than a black-box approach would have been.

Testing is what separates a working prototype from something you can reason about confidently. The
139 tests are not just a safety net — they are a specification. The test for "unknown genre uses
fallback" documents expected system behavior as clearly as any written spec would, and it will
catch regressions automatically if the retrieval logic changes. The original simulation's 96 tests
provided that foundation and made the new functionality suite faster to write because the scoring
logic was already verified.

The clearest difference between this and a simple script is that this system knows when it does
not know. When a request is vague, the agent says so. When confidence is low, it says so. When the
catalog is too small to satisfy a query, it says so. That kind of self-awareness is what makes
applied AI systems trustworthy in practice — and it only exists because the pipeline was designed
to expose it, and the tests were written to verify it.
