import json
from pathlib import Path
import shutil
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
def test_blimp_parser(
    test_files: ParserTestFiles,
    test_runner: Callable[[Path], str],
    tmp_path: Path
) -> None:
    # For bl3hotfix tests, copy to a temp file ending in just `.bl3hotfix`, incase the parser is
    #  checking extensions
    input_file = test_files.input
    if test_files.input.suffixes == [".bl3hotfix", ".in"]:
        input_file = tmp_path / test_files.input.stem
        shutil.copy(test_files.input, input_file)
    
    output = test_runner(input_file)
    output_json = json.loads(output)
    case_adjusted_output = {k.lower(): v for k, v in output_json.items()}
    expected_result = json.load(test_files.output.open())

    assert case_adjusted_output == expected_result
