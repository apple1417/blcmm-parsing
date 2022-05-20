import json
from pathlib import Path
from typing import Callable

import pytest

from tests import ParserTestFiles, find_test_cases

TESTS_FOLDER: Path = Path(__file__).parent / "cases"


@pytest.mark.timeout(10)
@pytest.mark.parametrize(
    "test_files",
    find_test_cases(TESTS_FOLDER, output_suffix=".json"),
    ids=lambda f: str(f)
)
def test_blimp_parser(test_files: ParserTestFiles, test_runner: Callable[[Path], str]) -> None:
    output = test_runner(test_files.input)
    output_json = json.loads(output)
    case_adjusted_output = {k.lower(): v for k, v in output_json.items()}
    expected_result = json.load(test_files.output.open())

    assert case_adjusted_output == expected_result
