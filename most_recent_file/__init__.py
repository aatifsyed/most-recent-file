import argparse
import dataclasses
import enum
import logging
from itertools import chain
from functools import partial
from pathlib import Path
from typing import Callable, List

import git

from most_recent_file.enum_action import enum_action
from most_recent_file.logging_action import LoggingAction
from most_recent_file.utils import filter_out, with_children

logger = logging.getLogger(__name__)


class MostRecentMethod(enum.Enum):
    # These are `partial` because bare lambdas will be treated as methods, not members
    # https://stackoverflow.com/a/40339397
    ACCESSED: Callable[[Path], float] = partial(lambda path: path.stat().st_atime)
    CREATED: Callable[[Path], float] = partial(lambda path: path.stat().st_ctime)
    MODIFIED: Callable[[Path], float] = partial(lambda path: path.stat().st_mtime)


def in_repo(path: Path):
    try:
        repo = git.Repo(path, search_parent_directories=True)
        return True
    except git.InvalidGitRepositoryError:
        return False


@dataclasses.dataclass
class GitPath:
    repo: git.Repo
    path: Path

    @classmethod
    def from_path(cls, path):
        repo = git.Repo(path, search_parent_directories=True)
        return cls(repo, path)

    def git_included(self, /, recurse: bool):
        if recurse:
            paths = set(with_children(self.path))
        else:
            paths = {self.path}
        ignored = set(self.repo.ignored(*paths))
        return paths - ignored


def main(
    paths: List[Path],
    recurse: bool,
    method: MostRecentMethod,
    include_hidden: bool,
    do_special_git_processing: bool,
):
    logger.debug(f"Processing {len(paths)} top-level paths")

    if do_special_git_processing:
        gitpaths = list(map(GitPath.from_path, filter_out(in_repo, paths)))
        logger.debug(f"{len(gitpaths)} of which are in a git repository")
        git_processed_paths = chain.from_iterable(
            map(partial(GitPath.git_included, recurse=recurse), gitpaths)
        )

    if recurse:
        paths = map(with_children, paths)

    if include_hidden:
        paths = filter(lambda path: not path.name.startswith("."), paths)

    paths = list(filter(Path.is_file, paths))

    if len(paths) == 0:
        raise RuntimeError("No files to sort")

    paths.sort(key=method.value)

    string = paths[-1].as_posix()

    print(string)


def cli():
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
        default=MostRecentMethod.MODIFIED,
        action=enum_action(MostRecentMethod),
        help="How to determine the most recent file.",
    )
    parser.add_argument(
        "-H",
        "--include-hidden",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include hidden files in the search results.",
    )
    parser.add_argument(
        "-I",
        "--include-gitignored",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include gitignored files in the search results.",
    )
    parser.add_argument("-l", "--log-level", action=LoggingAction, default="info")
    args = parser.parse_args()
    logger.debug(args)

    main(
        paths=args.path,
        recurse=args.recurse,
        method=args.method,
        include_hidden=args.include_hidden,
        do_special_git_processing=not args.include_gitignored,
    )
