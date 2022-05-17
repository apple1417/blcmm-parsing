#!/usr/bin/env python3
import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
import xml.parsers.expat.errors as xp_errors
from collections import Counter
from enum import Enum, auto
from os import PathLike
from pathlib import Path
from typing import Any

NO_ELEMENTS_CODE: int = xp_errors.codes[xp_errors.XML_ERROR_NO_ELEMENTS]

TESTS_FOLDER: Path = Path("tests")
INPUT_SUFFIX: str = "in"
OUTPUT_SUFFIX: str = "out"


class TestResult(Enum):
    """
    Enum holding the various test results.
    """
    PASS = auto()
    FAIL = auto()
    CRASH = auto()
    TIMEOUT = auto()


def canonicalize_possibly_empty(*args: Any, **kwargs: Any) -> str | None:
    """
    Wrapper around `ET.canonicalize` which allows files to be completely empty, and supresses
     parsing exceptions.
    Returns an empty string on no elements parsing exceptions, or None on others.

    Sets a few default arguments to make for better comparisons. Manually specifiying these will
     overwrite them.

    Args: Passthroughs to `ET.canonicalize`.
    """
    kwargs = {
        "strip_text": True
    } | kwargs
    try:
        return ET.canonicalize(*args, **kwargs)  # type: ignore
    except ET.ParseError as ex:
        if ex.code == NO_ELEMENTS_CODE:
            return ""
        else:
            return None


def run_test(
    program: list[str],
    test_input: str | bytes | PathLike[str] | PathLike[bytes] | int,
    expected: str,
    timeout: float = 10
) -> TestResult:
    """
    Runs a single test.

    Args:
        program: The test program to invoke, along with any required arguments.
        test_input: Path to the input test file.
        expected: The canonicalized expected output.
        timeout: The timeout to give the test program.
    Returns:
        The test result.
    """
    proc: subprocess.CompletedProcess[bytes]
    with open(test_input) as file:
        try:
            proc = subprocess.run(
                program,
                stdin=file,
                stdout=subprocess.PIPE,
                timeout=timeout,
                check=True
            )
        except subprocess.TimeoutExpired:
            return TestResult.TIMEOUT
        except subprocess.CalledProcessError:
            return TestResult.CRASH

    processed = canonicalize_possibly_empty(proc.stdout)

    if processed == expected:
        return TestResult.PASS
    else:
        return TestResult.FAIL


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Runs all test cases against a parser program."
    )
    parser.add_argument(
        "program",
        nargs=argparse.REMAINDER,
        metavar="...",
        help="The program to invoke, including any required arguments."
    )
    parser.add_argument(
        "-c", "--categories",
        nargs="*",
        default=None,
        help="Limit tests to the given categories. If not supplied, runs all tests."
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=10,
        help="The timeout for each individual parser run, in seconds."
    )

    args = parser.parse_args()

    passed_counts: Counter[str] = Counter()
    total_counts: Counter[str] = Counter()

    for test_in in sorted(TESTS_FOLDER.glob(f"*/*.{INPUT_SUFFIX}")):
        test_name = str(test_in.relative_to(TESTS_FOLDER).with_suffix(""))
        category = test_in.parts[1]

        if args.categories and category not in args.categories:
            continue

        test_out = test_in.with_suffix(f".{OUTPUT_SUFFIX}")
        if not test_out.exists():
            sys.stderr.write(
                f"Skipping '{test_name}' because it does not have a corosponding output file.\n"
            )
            continue

        expected_result = canonicalize_possibly_empty(from_file=test_out)
        if expected_result is None:
            sys.stderr.write(
                f"Skipping '{test_name}' because parsing it's output file failed.\n"
            )
            continue

        sys.stdout.write(f"{test_name}: ")
        result = run_test(args.program, test_in, expected_result, args.timeout)
        sys.stdout.write(result.name + "\n")

        total_counts[category] += 1
        if result == TestResult.PASS:
            passed_counts[category] += 1

    overall_passed = passed_counts.total()
    overall_total = total_counts.total()
    overall_percent = (overall_passed / overall_total) * 100
    sys.stdout.write(
        f"\n"
        f"Overall: {overall_passed}/{overall_total} ({overall_percent: >2.0f}%)\n"
        f"================================\n"
    )
    for category in sorted(total_counts.keys()):
        passed = passed_counts[category]
        total = total_counts[category]
        percent = (passed / total) * 100
        sys.stdout.write(f"{category}: {passed}/{total} ({percent: >2.0f}%)\n")
