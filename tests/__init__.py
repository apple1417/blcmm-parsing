import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class ParserTestFiles:
    """
    Data class holding a pair of input/output test case files.
    """
    input: Path
    output: Path
    test_folder: Path

    def __str__(self) -> str:
        return ".".join(self.input.relative_to(self.test_folder).with_suffix("").parts)


def find_test_cases(
    test_folder: Path,
    input_suffix: str = ".in",
    output_suffix: str = ".out"
) -> Iterator[ParserTestFiles]:
    """
    Find all pairs of input/output test case files in a given folder.
    Expects both files to have the same name, just with different file extensions.

    Args:
        test_folder: The folder to search through.
        input_suffix: The file extension of input files.
        output_suffix: The file extension of output files.
    Returns:
        An iterator of found test case files.
    """
    for input_file in sorted(test_folder.glob(f"**/*{input_suffix}")):
        output_file = input_file.with_suffix(output_suffix)
        if not output_file.exists():
            warnings.warn(
                f"Skipping '{input_file}' because it does not have a corosponding output file."
            )
            continue
        yield ParserTestFiles(input_file, output_file, test_folder)
