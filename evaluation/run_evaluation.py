"""
Evaluation harness for the Applied AI Music Recommendation System.

Loads evaluation/eval_cases.json, runs the agent on each input,
checks expected behavior, and prints a clean summary report.

Usage:
    python3 evaluation/run_evaluation.py
"""

import json
import os
import re
import sys

# Ensure project root is on the path regardless of CWD
_EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_EVAL_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from src.agent import AppliedMusicAgent  # noqa: E402

_CASES_PATH = os.path.join(_EVAL_DIR, "eval_cases.json")


def load_cases(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_scores(output: str) -> list:
    """Pull every 'Score: X.XXXX' value from an output string."""
    return [float(m) for m in re.findall(r"Score:\s+([\d.]+)", output)]


def check_case(case: dict, output: str) -> tuple:
    """
    Validate one output against its expected behavior.

    Returns (passed: bool, failure_details: list[str]).
    """
    passed = True
    details = []

    if case.get("should_error"):
        if "error" not in output.lower() and "Error" not in output:
            passed = False
            details.append("expected an error message but output looks normal")
    else:
        if "[Input Error]" in output or output.strip().startswith("[Error]"):
            passed = False
            details.append(f"unexpected error in output: {output[:80]}")

    mode = case.get("expected_retrieval_mode")
    if mode and not case.get("should_error"):
        expected_line = f"Retrieval mode: {mode.upper()}"
        if expected_line not in output:
            passed = False
            details.append(f"expected '{expected_line}' but not found in output")

    keyword = case.get("expected_keyword")
    if keyword and keyword not in output:
        passed = False
        details.append(f"expected keyword '{keyword}' not found in output")

    min_conf = case.get("minimum_confidence")
    if min_conf and not case.get("should_error"):
        if min_conf == "high":
            if "Confidence: HIGH" not in output:
                passed = False
                details.append("expected at least one HIGH confidence result")
        elif min_conf == "medium":
            if "Confidence: HIGH" not in output and "Confidence: MEDIUM" not in output:
                passed = False
                details.append("expected at least one MEDIUM or HIGH confidence result")

    if case.get("expect_fallback") and not case.get("should_error"):
        if "FALLBACK" not in output and "fallback" not in output.lower():
            passed = False
            details.append("expected fallback mode but 'fallback' not in output")

    return passed, details


def main():
    cases = load_cases(_CASES_PATH)
    agent = AppliedMusicAgent()

    results = []
    all_scores = []
    fallback_count = 0

    for case in cases:
        output = agent.run(case["input"])
        passed, details = check_case(case, output)

        scores = extract_scores(output)
        all_scores.extend(scores)

        if "FALLBACK" in output or "fallback" in output.lower():
            if not case.get("should_error"):
                fallback_count += 1

        results.append({
            "name": case["name"],
            "passed": passed,
            "details": details,
            "output_snippet": output[:120].replace("\n", " "),
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    avg_conf = sum(all_scores) / len(all_scores) if all_scores else 0.0
    status = "PASS" if failed_count == 0 else "REVIEW NEEDED"

    print()
    print("EVALUATION RESULTS")
    print("-" * 40)
    print(f"Total Cases    : {total}")
    print(f"Passed         : {passed_count}")
    print(f"Failed         : {failed_count}")
    print(f"Fallback Cases : {fallback_count}")
    print(f"Avg Confidence : {avg_conf:.4f}")
    print("-" * 40)
    print(f"Status         : {status}")
    print()

    if failed_count > 0:
        print("Failed Cases:")
        for r in results:
            if not r["passed"]:
                print(f"  [FAIL] {r['name']}")
                for d in r["details"]:
                    print(f"    Expected : {d}")
                print(f"    Output   : {r['output_snippet']}...")
                print()


if __name__ == "__main__":
    main()
