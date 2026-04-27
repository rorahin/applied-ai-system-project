# Presentation Script — Applied AI Music Recommendation System

Estimated time: 5–7 minutes

---

## 1. Introduction (30–45 seconds)

The project is called the Applied AI Music Recommendation System.

The problem it solves is simple to state but harder to build correctly: a user types a
natural-language music preference — something like "I want nostalgic rock with high energy" —
and the system returns ranked song recommendations with a plain-language explanation of why each
one was chosen.

Why does this matter? Real music platforms like Spotify and YouTube do this at scale using
collaborative filtering and neural models. This project focuses on the content-based side of that
problem — matching song attributes to stated preferences using a transparent, inspectable formula.
The goal was to build something that works reliably and explains its reasoning, not just something
that returns results.

---

## 2. System Overview (1 minute)

The system is a six-step agentic pipeline. Every request goes through the same stages in order:

1. **Validate** — guardrails reject empty or invalid input before it reaches the pipeline
2. **Parse** — natural language is mapped to a structured preference profile: genre, mood, energy, decade
3. **Retrieve** — the catalog is pre-filtered before scoring using a three-tier strategy: EXACT, PARTIAL, or FALLBACK
4. **Score** — each candidate is scored with a five-dimension weighted formula
5. **Self-check** — the agent inspects its own output for quality issues before returning it
6. **Format** — results come back with a score, confidence label, and a "Why" explanation per song

Three applied AI features are woven into that pipeline: RAG-style retrieval, an agentic
multi-step workflow, and a reliability layer with guardrails, logging, and 139 automated tests.

---

## 3. Demo Walkthrough (2–3 minutes)

I will run three inputs live to show how the system behaves across different request types.

---

**Input 1 — Normal request:**

```
I want nostalgic rock with high energy
```

What to highlight:

- The parser extracts three signals from one sentence: genre = rock, mood = moody (from
  "nostalgic"), energy = 0.85 (from "high energy")
- PARTIAL retrieval activates because no single song matches both genre and mood exactly
- Every result shows which dimensions matched and which did not — no hidden reasoning
- MEDIUM confidence on all three results — the system is honest about a partial match

---

**Input 2 — Edge case (exact match):**

```
give me chill lofi music from the 2010s
```

What to highlight:

- All three dimensions (genre, mood, decade) match catalog entries — EXACT retrieval activates
- Both results score HIGH confidence
- The self-check fires a warning: only 2 results found — the catalog is the limiting factor, not
  the algorithm
- This is the system surfacing its own limitation explicitly rather than silently returning a
  short list

---

**Input 3 — Vague / unrecognized request:**

```
I want dragoncore spaceship music
```

What to highlight:

- The parser extracts nothing — no genre, mood, energy, or decade recognized
- The profile is marked vague and FALLBACK mode activates
- Results are ranked by popularity alone — all other weights default to neutral
- The self-check surfaces a NOTE explaining the fallback rather than returning results silently
- The system does not crash, does not return an error, and does not fabricate a match

---

## 4. Architecture (1 minute)

The architecture diagram shows the full pipeline as a directed flow.

[Point to the diagram at assets/system_architecture.png]

- The main path flows top to bottom: User → main.py → Guardrails → Parser → Retriever → Scorer
  → Self-Check → Formatter → Output
- The CSV catalog feeds directly into the Retriever — that is the RAG-style retrieval step
- Logger receives events from every stage via dotted lines — it is a side channel, not part of
  the main flow
- pytest verifies Guardrails, Retriever, Scorer, and Formatter independently via dotted lines —
  every layer is tested, not just the entry point

The diagram is intentionally simple. The goal was a flow that someone unfamiliar with the code
could read in thirty seconds and understand what the system does.

---

## 5. Reliability (1 minute)

The reliability layer has four parts:

**Guardrails** — invalid input is rejected before it reaches the pipeline. Empty strings,
whitespace-only requests, and malformed CSV rows are all caught at the boundary.

**Confidence scoring** — every recommendation includes a numeric score and a label: HIGH (≥ 0.75),
MEDIUM (≥ 0.50), LOW (< 0.50). The system's uncertainty is always visible.

**Self-check** — after ranking, the agent inspects its own output. It flags low confidence,
too few results, fallback mode, and missing genre or mood in top results. The flags appear in
every output block.

**139 automated tests** — 43 new functionality tests covering guardrails, scoring, deduplication,
vague behavior, explanations, and end-to-end output format, plus 96 original simulation tests.
All 139 pass. Run them with:

```bash
pytest
# or
python3 tests/run_tests.py
```

---

## 6. Reflection (45 seconds)

The most important thing I learned is the difference between a system that produces output and a
system that produces trustworthy output.

Before adding guardrails and self-check, the system returned results silently for every input —
empty strings, nonsense requests, single characters. Everything looked fine. Guardrails and
self-check are what turned it from a script into a system you can reason about.

The biggest challenge was the scoring weight distribution. Genre and mood together account for
60% of the score. Once I understood that, I could reason about why certain rankings looked
unintuitive and explain them — rather than just accept them as outputs from a formula.

If I had more time, I would expand the catalog, add fuzzy genre matching to give partial credit
for adjacent genres, and build a feedback loop so the system could learn from what a user skipped
or replayed.

---

## How to Record the Loom Video

**Before recording:**

- Have a terminal open at the project root with the virtual environment activated
- Keep the recording under 7 minutes
- Do NOT show setup, installation, or code — focus entirely on system behavior

**Steps:**

1. Open your terminal and navigate to the project directory:

```bash
cd applied-ai-system-project
```

2. Run the system and record these three inputs one at a time:

```bash
python3 main.py
```

Input 1: `I want nostalgic rock with high energy`
Input 2: `give me chill lofi music from the 2010s`
Input 3: `I want dragoncore spaceship music`

For each input, pause briefly after the output appears and narrate:
- what retrieval mode fired and why
- what the confidence labels mean
- any self-check warnings and what they indicate

3. Run the test suite and show the clean summary:

```bash
python3 tests/run_tests.py
```

Narrate: "139 tests, all passing — guardrails, scoring, deduplication, vague behavior, and
end-to-end format."

4. Run the evaluation harness:

```bash
python3 evaluation/run_evaluation.py
```

Narrate: "8 predefined cases covering the full behavior range — all pass."

**What to show:**

- Agent reasoning trace output (retrieval mode, confidence, self-check flags)
- Confidence labels on each recommendation
- Fallback behavior on the vague input
- Test and evaluation summary screens

**What to skip:**

- Virtual environment setup
- File structure walkthrough
- Code editor or source files
