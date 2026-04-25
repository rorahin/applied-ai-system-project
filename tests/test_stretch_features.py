"""
Tests for the four optional stretch features:

  1. RAG Enhancement — knowledge base loading and retrieval
  2. Agentic Workflow Enhancement — show_steps trace
  3. Specialization Simulation — style modes
  4. Evaluation Harness — eval_cases.json exists and is valid
"""

import json
import os

import pytest

from src.agent import AppliedMusicAgent
from src.knowledge_retrieval import (
    apply_knowledge_hints,
    load_knowledge_base,
    retrieve_snippets,
)
from src.specialization import apply_style, validate_style
from src.song import Song
from src.user_profile import UserProfile


# ---------------------------------------------------------------------------
# Shared fixture — small catalog covering intense and focused moods
# ---------------------------------------------------------------------------


@pytest.fixture
def agent(tmp_path):
    """Agent backed by a minimal six-song CSV for stretch feature tests."""
    rows = [
        "id,title,artist,genre,mood,energy,popularity,decade",
        "1,Rock Anthem,Band A,rock,intense,0.90,80,2010s",
        "2,Chill Vibes,Artist B,lofi,chill,0.30,60,2010s",
        "3,Happy Days,Pop Star,pop,happy,0.70,90,2020s",
        "4,Focus Flow,LoRoom,lofi,focused,0.40,52,2020s",
        "5,Gym Hero,Max Pulse,pop,intense,0.93,82,2020s",
        "6,Sad Song,Artist C,indie folk,melancholy,0.40,55,2000s",
    ]
    csv_path = tmp_path / "songs.csv"
    csv_path.write_text("\n".join(rows))
    return AppliedMusicAgent(songs_path=str(csv_path))


# ---------------------------------------------------------------------------
# 1. RAG Enhancement — knowledge base
# ---------------------------------------------------------------------------


class TestKnowledgeBase:
    def test_knowledge_base_loads(self):
        entries = load_knowledge_base()
        assert len(entries) > 0

    def test_all_entries_have_keywords(self):
        entries = load_knowledge_base()
        for entry in entries:
            assert len(entry.keywords) > 0, f"Entry '{entry.name}' has no keywords"

    def test_retrieve_snippets_workout(self):
        snippets, matched = retrieve_snippets("workout music")
        assert len(matched) > 0
        names = [e.name for e in matched]
        assert "workout" in names

    def test_retrieve_snippets_focus(self):
        snippets, matched = retrieve_snippets("focus music")
        assert len(matched) > 0
        names = [e.name for e in matched]
        assert "focus" in names

    def test_retrieve_snippets_no_match(self):
        snippets, matched = retrieve_snippets("xyz dragoncore spaceship")
        assert snippets == []
        assert matched == []

    def test_retrieve_snippets_returns_note_text(self):
        snippets, matched = retrieve_snippets("workout music")
        assert len(snippets) > 0
        assert isinstance(snippets[0], str)
        assert len(snippets[0]) > 5

    def test_apply_hints_sets_energy_for_workout(self):
        _, matched = retrieve_snippets("workout music")
        profile = UserProfile()
        apply_knowledge_hints(profile, matched)
        assert profile.target_energy is not None
        assert profile.target_energy >= 0.85

    def test_apply_hints_sets_mood_for_focus(self):
        _, matched = retrieve_snippets("focus music")
        profile = UserProfile()
        apply_knowledge_hints(profile, matched)
        assert profile.preferred_mood == "focused"

    def test_apply_hints_does_not_override_existing_mood(self):
        _, matched = retrieve_snippets("focus music")
        profile = UserProfile(preferred_mood="chill")
        apply_knowledge_hints(profile, matched)
        assert profile.preferred_mood == "chill"  # parser value preserved

    def test_apply_hints_does_not_override_existing_energy(self):
        _, matched = retrieve_snippets("workout music")
        profile = UserProfile(target_energy=0.50)
        apply_knowledge_hints(profile, matched)
        assert profile.target_energy == 0.50  # parser value preserved

    def test_knowledge_augments_vague_profile(self):
        _, matched = retrieve_snippets("focus music")
        # Simulate the state parse_request produces for a fully unrecognized request
        profile = UserProfile(is_vague=True)
        apply_knowledge_hints(profile, matched)
        assert profile.is_vague is False

    def test_knowledge_note_appears_in_output(self, agent):
        result = agent.run("workout music")
        assert "Knowledge used" in result

    def test_workout_retrieval_is_not_fallback(self, agent):
        result = agent.run("workout music")
        assert "Retrieval mode: FALLBACK" not in result

    def test_focus_retrieval_is_not_fallback(self, agent):
        result = agent.run("focus music")
        assert "Retrieval mode: FALLBACK" not in result


# ---------------------------------------------------------------------------
# 2. Agentic Workflow Enhancement — show_steps
# ---------------------------------------------------------------------------


class TestShowSteps:
    def test_show_steps_false_no_trace(self, agent):
        result = agent.run("I want rock music", show_steps=False)
        assert "AGENT REASONING TRACE" not in result

    def test_show_steps_default_no_trace(self, agent):
        result = agent.run("I want rock music")
        assert "AGENT REASONING TRACE" not in result

    def test_show_steps_true_includes_trace(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "AGENT REASONING TRACE" in result

    def test_trace_includes_validation(self, agent):
        result = agent.run("I want chill music", show_steps=True)
        assert "Validation" in result

    def test_trace_includes_retrieval_mode(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "Retrieval mode:" in result

    def test_trace_includes_candidate_count(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "candidates:" in result

    def test_trace_includes_confidence_summary(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "Confidence summary" in result

    def test_trace_includes_self_check(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "Self-check" in result

    def test_trace_includes_decision(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "Decision" in result

    def test_show_steps_still_has_recommendations(self, agent):
        result = agent.run("I want rock music", show_steps=True)
        assert "MUSIC RECOMMENDATIONS" in result
        assert "Score:" in result

    def test_show_steps_error_returns_error(self, agent):
        result = agent.run("", show_steps=True)
        assert "Error" in result
        assert "AGENT REASONING TRACE" not in result

    def test_knowledge_snippets_appear_in_trace(self, agent):
        result = agent.run("workout music", show_steps=True)
        assert "Knowledge snippets" in result


# ---------------------------------------------------------------------------
# 3. Specialization Simulation — style modes
# ---------------------------------------------------------------------------


class TestSpecialization:
    def test_validate_style_valid(self):
        assert validate_style("professional") == "professional"
        assert validate_style("casual") == "casual"
        assert validate_style("technical") == "technical"
        assert validate_style("default") == "default"

    def test_validate_style_invalid_falls_back(self):
        assert validate_style("fancy") == "default"
        assert validate_style("") == "default"
        assert validate_style("PROFESSIONAL") == "default"  # case-sensitive

    def test_default_explanation_unchanged(self):
        exp = "genre match (rock) | mood mismatch (chill != intense) | popularity 80"
        assert apply_style(exp, "default") == exp

    def test_professional_uses_semicolons(self):
        exp = "genre match (rock) | mood match (intense) | popularity 80"
        result = apply_style(exp, "professional")
        assert ";" in result
        assert "|" not in result

    def test_casual_replaces_genre_match(self):
        exp = "genre match (rock) | mood match (intense)"
        result = apply_style(exp, "casual")
        assert "genre fits" in result

    def test_casual_replaces_mood_mismatch(self):
        exp = "mood mismatch (chill != intense)"
        result = apply_style(exp, "casual")
        assert "vibe is a bit off" in result

    def test_technical_adds_weight_annotation(self):
        exp = "genre match (rock) | popularity 80"
        result = apply_style(exp, "technical")
        assert "[w=0.30]" in result
        assert "[w=0.10]" in result

    def test_technical_annotates_energy(self):
        exp = "energy 0.91 (target 0.85)"
        result = apply_style(exp, "technical")
        assert "[w=0.20]" in result

    def test_professional_output_differs_from_casual(self, agent):
        result_pro = agent.run("I want rock music", style="professional")
        result_cas = agent.run("I want rock music", style="casual")
        assert result_pro != result_cas

    def test_technical_output_differs_from_default(self, agent):
        result_def = agent.run("I want rock music", style="default")
        result_tech = agent.run("I want rock music", style="technical")
        assert result_def != result_tech

    def test_invalid_style_does_not_crash(self, agent):
        result = agent.run("I want rock music", style="xyz_invalid")
        assert "MUSIC RECOMMENDATIONS" in result

    def test_recommendations_same_across_styles(self, agent):
        result_def = agent.run("I want rock music", style="default")
        result_tech = agent.run("I want rock music", style="technical")
        # Same song should appear in both
        assert "Rock Anthem" in result_def
        assert "Rock Anthem" in result_tech

    def test_scores_same_across_styles(self, agent):
        import re
        result_def = agent.run("I want rock music", style="default")
        result_pro = agent.run("I want rock music", style="professional")
        scores_def = re.findall(r"Score:\s+([\d.]+)", result_def)
        scores_pro = re.findall(r"Score:\s+([\d.]+)", result_pro)
        assert scores_def == scores_pro


# ---------------------------------------------------------------------------
# 4. Evaluation Harness — basic sanity checks
# ---------------------------------------------------------------------------


class TestEvaluationHarness:
    def test_eval_cases_file_exists(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "evaluation", "eval_cases.json")
        assert os.path.exists(path), f"eval_cases.json not found at {path}"

    def test_eval_cases_loads_as_json(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "evaluation", "eval_cases.json")
        with open(path) as f:
            cases = json.load(f)
        assert isinstance(cases, list)
        assert len(cases) >= 8

    def test_eval_cases_have_required_fields(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "evaluation", "eval_cases.json")
        with open(path) as f:
            cases = json.load(f)
        required = {"name", "input", "should_error"}
        for case in cases:
            missing = required - set(case.keys())
            assert not missing, f"Case '{case.get('name')}' missing fields: {missing}"

    def test_eval_script_exists(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "evaluation", "run_evaluation.py")
        assert os.path.exists(path)
