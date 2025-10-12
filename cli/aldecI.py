"""AlDeci CLI bootstrap."""
from __future__ import annotations

import argparse
import sys


def create_aldeci_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aldecI",
        description="AlDeci command line interface (bootstrap phase)",
        add_help=True,
    )
    parser.add_argument(
        "--backend",
        choices=["local", "http"],
        default="local",
        help="Execution backend to target.",
    )
    parser.add_argument(
        "--overlay",
        choices=["demo", "enterprise"],
        default="demo",
        help="Overlay configuration to apply.",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = create_aldeci_parser()
    parser.parse_args(argv)
    parser.print_help(sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
