"""
Clean test runner for the Applied AI Music Recommendation System.

Usage:
    python tests/run_tests.py

Prints only a final summary — no dots, no individual test lines.
"""

import os
import pytest


class _ResultCounter:
    """Pytest plugin that silently counts pass / fail / skip outcomes."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def pytest_runtest_logreport(self, report):
        if report.passed and report.when == "call":
            self.passed += 1
        elif report.failed and report.when in ("call", "setup", "teardown"):
            self.failed += 1
        elif report.skipped and report.when in ("call", "setup"):
            self.skipped += 1


def main():
    tests_dir = os.path.dirname(os.path.abspath(__file__))

    counter = _ResultCounter()
    pytest.main(
        [tests_dir, "-p", "no:terminal"],
        plugins=[counter],
    )

    total = counter.passed + counter.failed + counter.skipped
    status = "ALL TESTS PASSED ✅" if counter.failed == 0 else "SOME TESTS FAILED ❌"

    print()
    print("TEST RESULTS")
    print("-" * 40)
    print(f"Total Tests : {total}")
    print(f"Passed      : {counter.passed}")
    print(f"Failed      : {counter.failed}")
    print(f"Skipped     : {counter.skipped}")
    print("-" * 40)
    print(f"Status      : {status}")
    print()


if __name__ == "__main__":
    main()
