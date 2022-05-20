import json
from pathlib import Path
from typing import Callable

import pytest

from tests import ParserTestFiles, find_test_cases

TESTS_FOLDER: Path = Path(__file__).parent / "cases"


@pytest.mark.timeout(10)
@pytest.mark.parametrize("test_files", find_test_cases(TESTS_FOLDER), ids=lambda f: str(f))
def test_blimp_parser(test_files: ParserTestFiles, test_runner: Callable[[Path], str]) -> None:
    processed = json.loads(test_runner(test_files.input))
    expected_result = json.load(test_files.output.open())

    assert processed == expected_result
