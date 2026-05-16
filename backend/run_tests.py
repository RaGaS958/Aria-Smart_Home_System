#!/usr/bin/env python3
"""
run_tests.py — ARIA Backend · Local Test Pipeline Runner
=========================================================

Runs the full test suite locally with the same logic as CI.
Provides a color-coded summary table, coverage badge, and exit code.

Usage
-----
  python run_tests.py                   # run everything
  python run_tests.py --suite tools     # only test_tools.py
  python run_tests.py --suite helpers   # only test_helpers.py
  python run_tests.py --suite endpoints # only test_endpoints.py
  python run_tests.py --suite ws        # only test_websocket.py
  python run_tests.py --suite scheduler # only test_scheduler.py
  python run_tests.py --fast            # skip coverage (faster)
  python run_tests.py --verbose         # pytest -vv
  python run_tests.py --stop-on-fail    # -x flag

Exit codes
----------
  0  all tests passed
  1  one or more tests failed
  2  dependency missing (install requirements first)
  3  coverage below threshold
"""

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Colours (fallback to plain text on Windows without ANSI support)
# ──────────────────────────────────────────────────────────────────────────────
USE_COLOR = sys.platform != "win32" or os.environ.get("FORCE_COLOR")

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

GREEN   = lambda t: _c("32;1", t)
RED     = lambda t: _c("31;1", t)
YELLOW  = lambda t: _c("33;1", t)
CYAN    = lambda t: _c("36;1", t)
BLUE    = lambda t: _c("34;1", t)
BOLD    = lambda t: _c("1",    t)
DIM     = lambda t: _c("2",    t)
MAGENTA = lambda t: _c("35;1", t)

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
COVERAGE_THRESHOLD = 70        # fail if coverage < this percent
BACKEND_DIR        = Path(__file__).parent
TESTS_DIR          = BACKEND_DIR / "tests"

SUITES = {
    "tools":     TESTS_DIR / "test_tools.py",
    "helpers":   TESTS_DIR / "test_helpers.py",
    "endpoints": TESTS_DIR / "test_endpoints.py",
    "ws":        TESTS_DIR / "test_websocket.py",
    "scheduler": TESTS_DIR / "test_scheduler.py",
}

REQUIRED_PACKAGES = [
    "pytest", "pytest_asyncio", "httpx", "fastapi",
    "pydantic", "starlette", "dotenv",
]

# ──────────────────────────────────────────────────────────────────────────────
# Data
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class SuiteResult:
    name: str
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration: float = 0.0
    returncode: int = 0
    output: str = ""

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.errors

    @property
    def ok(self) -> bool:
        return self.returncode == 0

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _sep(char="─", width=72) -> str:
    return DIM(char * width)


def _check_deps() -> bool:
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(RED("✗ Missing packages:"), ", ".join(missing))
        print(YELLOW("  Install with: pip install pytest pytest-asyncio httpx pytest-cov anyio[trio]"))
        return False
    return True


def _write_env() -> None:
    """Write a minimal .env so main.py doesn't complain about missing keys."""
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        env_path.write_text(
            "OPENWEATHER_API_KEY=test_key\n"
            "TAVILY_API_KEY=test_key\n"
            "MISTRAL_API_KEY=test_key\n"
        )
        print(DIM("  ⓘ  Created test .env with dummy keys"))


def _parse_pytest_output(output: str) -> tuple[int, int, int, int]:
    """Extract passed/failed/error/skipped counts from pytest terminal output."""
    passed = failed = errors = skipped = 0
    # Match the summary line e.g. "5 passed, 2 failed, 1 error, 1 skipped"
    for match in re.finditer(r"(\d+)\s+(passed|failed|error|skipped)", output):
        n, kind = int(match.group(1)), match.group(2)
        if kind == "passed":  passed  = n
        elif kind == "failed":  failed  = n
        elif kind == "error":   errors  = n
        elif kind == "skipped": skipped = n
    return passed, failed, errors, skipped


def _parse_coverage(output: str) -> Optional[int]:
    """Extract total coverage % from pytest-cov output."""
    m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    return int(m.group(1)) if m else None


def _run_suite(
    name: str,
    path: Path,
    verbose: bool,
    with_coverage: bool,
    stop_on_fail: bool,
    extra_flags: list[str],
) -> SuiteResult:
    cmd = [
        sys.executable, "-m", "pytest",
        str(path),
        "--tb=short",
        "--no-header",
        "--color=yes",
        "-m", "not integration",
    ]
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    if stop_on_fail:
        cmd.append("-x")
    if with_coverage:
        cmd += [
            f"--cov={BACKEND_DIR / 'main'}",
            "--cov-report=term-missing",
            "--cov-append",         # accumulate across suites
        ]
    cmd.extend(extra_flags)

    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(BACKEND_DIR),
        env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
    )
    duration = time.perf_counter() - t0

    combined = proc.stdout + proc.stderr
    passed, failed, errors, skipped = _parse_pytest_output(combined)

    return SuiteResult(
        name=name,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        duration=duration,
        returncode=proc.returncode,
        output=combined,
    )


def _print_suite_header(name: str) -> None:
    label = f"  Suite: {name.upper()}  "
    pad   = "─" * ((72 - len(label)) // 2)
    print(f"\n{CYAN(pad + label + pad)}")


def _print_suite_result(result: SuiteResult) -> None:
    icon  = GREEN("✓") if result.ok else RED("✗")
    color = GREEN if result.ok else RED
    status = "PASSED" if result.ok else "FAILED"
    print(
        f"  {icon}  {color(status):12s}  "
        f"{GREEN(str(result.passed))} passed  "
        f"{(RED(str(result.failed)) if result.failed else DIM('0')) } failed  "
        f"{(YELLOW(str(result.errors)) if result.errors else DIM('0'))} errors  "
        f"{DIM(f'{result.duration:.2f}s')}"
    )


def _print_summary(results: list[SuiteResult], coverage: Optional[int], total_time: float) -> None:
    print(f"\n{_sep('═')}")
    print(BOLD("  ARIA BACKEND · TEST SUMMARY"))
    print(_sep())

    # Column widths
    col = [18, 8, 8, 8, 8, 10]

    def row(*cells, color=None):
        parts = []
        for c, w in zip(cells, col):
            s = str(c).ljust(w)
            parts.append(color(s) if color else s)
        print("  " + "  ".join(parts))

    row("Suite", "Passed", "Failed", "Errors", "Skip", "Time", color=BOLD)
    print(_sep())

    all_passed = all_failed = all_errors = all_skipped = 0
    for r in results:
        status_color = GREEN if r.ok else RED
        row(
            r.name,
            r.passed,
            r.failed or "─",
            r.errors or "─",
            r.skipped or "─",
            f"{r.duration:.2f}s",
            color=status_color if not r.ok else None,
        )
        all_passed  += r.passed
        all_failed  += r.failed
        all_errors  += r.errors
        all_skipped += r.skipped

    print(_sep())
    row(
        "TOTAL",
        all_passed,
        all_failed or "─",
        all_errors or "─",
        all_skipped or "─",
        f"{total_time:.2f}s",
        color=BOLD,
    )
    print(_sep('═'))

    # Coverage badge
    if coverage is not None:
        bar_filled = int(coverage / 5)   # 20 chars = 100%
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        cov_color = GREEN if coverage >= COVERAGE_THRESHOLD else RED
        print(f"\n  Coverage  [{cov_color(bar)}]  {cov_color(f'{coverage}%')}  "
              f"(threshold {COVERAGE_THRESHOLD}%)")
        if coverage < COVERAGE_THRESHOLD:
            print(RED(f"  ✗ Coverage {coverage}% is below the required {COVERAGE_THRESHOLD}%"))

    # Final verdict
    total_fail = all_failed + all_errors
    print()
    if total_fail == 0:
        print(GREEN("  ✓  All tests passed!") + f"  {DIM(f'({all_passed} tests in {total_time:.1f}s)')}")
    else:
        print(RED(f"  ✗  {total_fail} test(s) failed."))
    print(_sep('═'))


def _print_failures(results: list[SuiteResult]) -> None:
    """Print stdout/stderr of failed suites for quick debugging."""
    for r in results:
        if not r.ok:
            print(f"\n{RED('─' * 72)}")
            print(RED(f"  FAILURE OUTPUT — {r.name.upper()}"))
            print(RED('─' * 72))
            # Only print the pytest short-test summary section
            lines = r.output.splitlines()
            capture = False
            for line in lines:
                if "FAILURES" in line or "ERROR" in line or "short test" in line.lower():
                    capture = True
                if capture:
                    print(line)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ARIA Backend — local test pipeline runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py
  python run_tests.py --suite tools --verbose
  python run_tests.py --fast --stop-on-fail
        """,
    )
    parser.add_argument(
        "--suite", choices=list(SUITES.keys()),
        help="Run a single test suite (default: all)",
    )
    parser.add_argument("--fast",         action="store_true", help="Skip coverage collection")
    parser.add_argument("--verbose",      action="store_true", help="pytest -vv output")
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop on first failure (-x)")
    args = parser.parse_args()

    # ── Banner ──────────────────────────────────────────────────────────────
    print(_sep('═'))
    print(BOLD("  ◉  ARIA BACKEND · TEST PIPELINE"))
    print(DIM(f"     Python {sys.version.split()[0]}  |  CWD: {BACKEND_DIR}"))
    print(_sep('═'))

    # ── Preflight ───────────────────────────────────────────────────────────
    print(f"\n{BOLD('[ 1/4 ]')} Checking dependencies…")
    if not _check_deps():
        return 2

    print(f"\n{BOLD('[ 2/4 ]')} Preparing environment…")
    _write_env()

    # Reset coverage data so --cov-append starts clean
    cov_data = BACKEND_DIR / ".coverage"
    if cov_data.exists():
        cov_data.unlink()

    # ── Determine which suites to run ────────────────────────────────────────
    suites_to_run = {args.suite: SUITES[args.suite]} if args.suite else SUITES
    with_coverage  = not args.fast

    # ── Run suites ───────────────────────────────────────────────────────────
    print(f"\n{BOLD('[ 3/4 ]')} Running {len(suites_to_run)} suite(s)…")
    results: list[SuiteResult] = []
    pipeline_start = time.perf_counter()

    for name, path in suites_to_run.items():
        _print_suite_header(name)
        if not path.exists():
            print(YELLOW(f"  ⚠  {path.name} not found — skipping"))
            results.append(SuiteResult(name=name, returncode=0))
            continue

        result = _run_suite(
            name=name,
            path=path,
            verbose=args.verbose,
            with_coverage=with_coverage,
            stop_on_fail=args.stop_on_fail,
            extra_flags=[],
        )
        results.append(result)
        _print_suite_result(result)

        # Print truncated output on failure
        if not result.ok:
            # Show last 30 lines of pytest output
            tail = "\n".join(result.output.splitlines()[-30:])
            print(DIM(tail))

        if args.stop_on_fail and not result.ok:
            print(RED("\n  ⛔  Stopping pipeline on first failure (--stop-on-fail)"))
            break

    total_time = time.perf_counter() - pipeline_start

    # ── Coverage report ──────────────────────────────────────────────────────
    coverage_pct: Optional[int] = None
    if with_coverage and cov_data.exists():
        print(f"\n{BOLD('[ 4/4 ]')} Generating coverage report…")
        cov_proc = subprocess.run(
            [sys.executable, "-m", "pytest",
             "--cov=main", "--cov-report=term-missing",
             "--cov-report=html:htmlcov",
             "-m", "not integration",
             "--tb=no", "-q",
             str(TESTS_DIR)],
            capture_output=True, text=True,
            cwd=str(BACKEND_DIR),
            env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
        )
        coverage_pct = _parse_coverage(cov_proc.stdout + cov_proc.stderr)
        html_dir = BACKEND_DIR / "htmlcov" / "index.html"
        if html_dir.exists():
            print(DIM(f"  HTML report → file://{html_dir}"))
    else:
        print(f"\n{BOLD('[ 4/4 ]')} Coverage skipped (--fast mode)")

    # ── Summary ──────────────────────────────────────────────────────────────
    _print_summary(results, coverage_pct, total_time)
    _print_failures(results)

    # ── Exit code ────────────────────────────────────────────────────────────
    any_failed = any(not r.ok for r in results)
    below_cov  = (coverage_pct is not None) and (coverage_pct < COVERAGE_THRESHOLD)

    if any_failed:
        return 1
    if below_cov:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
