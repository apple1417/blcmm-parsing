import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

import pytest

from . import ParserTestFiles, find_test_cases

TESTS_FOLDER: Path = Path(__file__).parent


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


@pytest.mark.timeout(10)
@pytest.mark.parametrize("test_files", find_test_cases(TESTS_FOLDER), ids=lambda f: str(f))
def test_parser(test_files: ParserTestFiles, test_runner: Callable[[Path], str]) -> None:
    processed = canonicalize(test_runner(test_files.input))
    expected_result = canonicalize(test_files.output.read_text())

    assert expected_result == processed
