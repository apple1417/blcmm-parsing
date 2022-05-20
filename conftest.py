import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from pytest import CallInfo, Collector, CollectReport, Config, Item, Parser, TestReport


@pytest.fixture(scope="session")
def test_runner(pytestconfig: Config) -> Callable[[Path], str]:
    """
    Fixture returning a function which will run the test program on the given input file.
    Subprocess stderr will be piped to python's stderr.

    Args:
        input_file: The file to pass to the program's stdin.
    Returns:
        The program's stdout output.
    Raises:
        CalledProcessError: If the process does not exit with code 0
    """
    def runner(input_file: Path) -> str:
        proc: subprocess.CompletedProcess[str]
        with input_file.open() as file:
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
        return proc.stdout
    return runner


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--program",
        nargs=argparse.REMAINDER,
        required=True,
        help="The program to invoke. Specify multiple times if you need arguments."
    )


def pytest_exception_interact(
    node: Item | Collector,
    call: CallInfo[Any],
    report: CollectReport | TestReport
) -> None:
    # Hack to limit exceptions to just the outermost frame
    call.excinfo.traceback[:] = call.excinfo.traceback[:1]  # type: ignore
    call.excinfo.traceback[0]._rawentry.tb_next = None  # type: ignore
    report.longrepr = call.excinfo.getrepr()  # type: ignore
