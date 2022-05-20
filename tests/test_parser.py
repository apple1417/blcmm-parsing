import subprocess
import sys
import warnings
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pytest
from pytest import Config

TESTS_FOLDER: Path = Path(__file__).parent
INPUT_SUFFIX: str = "in"
OUTPUT_SUFFIX: str = "out"


@dataclass
class ParserTestFiles:
    input: Path
    output: Path

    def __str__(self) -> str:
        return ".".join(self.input.relative_to(TESTS_FOLDER).with_suffix("").parts)


def canonicalize(xml: str) -> str:
    """
    Wrapper around `ET.canonicalize` which dumps invalid files to stderr when parsing fails.

    Also contains default canonicalize args for better comparisons

    Args:
        xml: The xml string to canonicalize.
    Returns:
        The canonicalized xml, or an empty string if there were no elements
    """

    try:
        return ET.canonicalize(xml, strip_text=True, with_comments=False)
    except ET.ParseError as ex:
        sys.stderr.write(f"Invalid XML:\n{xml}\n")
        raise ex


def find_test_cases() -> Iterator[ParserTestFiles]:
    for input_file in sorted(TESTS_FOLDER.glob(f"*/*.{INPUT_SUFFIX}")):
        output_file = input_file.with_suffix(f".{OUTPUT_SUFFIX}")
        if not output_file.exists():
            warnings.warn(
                f"Skipping '{input_file}' because it does not have a corosponding output file."
            )
            continue
        yield ParserTestFiles(input_file, output_file)


@pytest.mark.timeout(10)
@pytest.mark.parametrize("test_files", find_test_cases(), ids=lambda f: str(f))
def test_parser(pytestconfig: Config, test_files: ParserTestFiles) -> None:
    expected_result = canonicalize(test_files.output.read_text())

    proc: subprocess.CompletedProcess[str]
    with test_files.input.open() as file:
        proc = subprocess.run(
            pytestconfig.getoption("program"),
            stdin=file,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=pytestconfig.getoption("timeout"),
            encoding="utf-8"
        )
    if proc.stderr:
        sys.stderr.write(proc.stderr + "\n")
    proc.check_returncode()

    processed = canonicalize(proc.stdout)

    assert expected_result == processed
