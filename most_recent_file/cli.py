import argparse
import logging
from pathlib import Path

import argcomplete
from logging_actions import log_level_action

from most_recent_file import __version__, logger
from most_recent_file.main import main


def cli():
    parser = argparse.ArgumentParser(
        description="Get the most recent file out of the ones given, applying searching and filtering according to the command line options."
    )
    parser.add_argument(
        "path",
        metavar="PATH",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Maybe be a file or folder. If a file, it is a candidate for most recent. If a folder, and --recurse is specified, files from it will be candidates. (default: current directory)",
    )
    parser.add_argument(
        "-r",
        "--recurse",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="If one of the given PATHs is a folder, recursively expand it into files (and therefore search them).",
    )
    parser.add_argument(
        "--hidden",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include hidden files as candidates.",
    )
    parser.add_argument(
        "--recurse-hidden",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Recurse into hidden folders.",
    )
    parser.add_argument(
        "--gitignored",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include gitignored files as candidates.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        action=log_level_action(logger),
        default="info",
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    logger.addHandler(hdlr=logging.StreamHandler())
    logger.debug(f"{args=}")

    result = main(
        roots=args.path,
        sort_method=lambda path: path.stat().st_mtime,
        recurse=args.recurse,
        include_hidden_files=args.hidden,
        include_gitignored=args.gitignored,
        include_folders=False,
        descend_hidden_directories=args.recurse_hidden,
    )

    print(result)
