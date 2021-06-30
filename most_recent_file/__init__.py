import argparse
import logging
import enum
from pathlib import Path
from typing import Callable, List
from functools import partial

logger = logging.getLogger(__name__)


class MostRecentMethod(enum.Enum):
    ACCESSED: Callable[[Path], float] = partial(lambda path: path.stat().st_atime)
    CREATED: Callable[[Path], float] = partial(lambda path: path.stat().st_ctime)
    MODIFIED: Callable[[Path], float] = partial(lambda path: path.stat().st_mtime)

    @classmethod
    def from_string(cls, s: str):
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError(f"{s} is not a valid variant of {cls}")

    def __str__(self) -> str:
        return self.name.lower()


def main():
    parser = argparse.ArgumentParser(
        description="Get the most recent file out of the ones given"
    )
    parser.add_argument(
        "path",
        metavar="PATH",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Maybe be a file or folder. If a file, it may be determined to be the most recent. If a folder, and --recurse is specified, files from it may be determined to be the most recent. (default: current directory)",
    )
    parser.add_argument(
        "-r",
        "--recurse",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="If one of the given PATHs is a folder, recursively expand it into files (and therefore search them).",
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=[variant.name.lower() for variant in MostRecentMethod],
        default=MostRecentMethod.MODIFIED,
        type=MostRecentMethod.from_string,
        help="How to determine the most recent file. (default: %(default)s)",
    )

    parser.add_argument(
        "-l",
        "--log-level",
        type=lambda arg: getattr(logging, arg.upper()),
        default=logging.INFO,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    logger.debug(args)

    paths: List[Path] = args.path

    if args.recurse:
        logging.debug("Expand out our path list")
        for path in paths:
            if path.is_dir():
                logging.debug(f"expanding {path}")
                paths.extend(
                    path.iterdir()
                )  # Safe because paths is a linked list, and we're not changing order

    paths = list(filter(Path.is_file, paths))

    assert len(paths) > 1, "No files to sort"

    paths.sort(key=lambda path: getattr(path.stat(), args.method))

    logging.debug(paths)

    string = paths[-1].as_posix()

    print(string)
