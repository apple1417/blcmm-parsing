import argparse
from typing import Any

from pytest import CallInfo, Collector, CollectReport, Item, Parser, TestReport


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
