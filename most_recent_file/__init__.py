import argparse
import dataclasses
import enum
import logging
from functools import partial
from itertools import chain
from pathlib import Path
from typing import Callable, List

import argcomplete
import git

from most_recent_file.enum_action import enum_action
from most_recent_file.logging_action import log_level_action
from most_recent_file.utils import debug_iterable_length, filter_out, with_children

logger = logging.getLogger(__name__)


class MostRecentMethod(enum.Enum):
    # These are `partial` because bare lambdas will be treated as methods, not members
    # https://stackoverflow.com/a/40339397
    ACCESSED: Callable[[Path], float] = partial(lambda path: path.stat().st_atime)
    CREATED: Callable[[Path], float] = partial(lambda path: path.stat().st_ctime)
    MODIFIED: Callable[[Path], float] = partial(lambda path: path.stat().st_mtime)


def in_repo(path: Path):
    try:
        git.Repo(path, search_parent_directories=True)
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
        ignored = set(map(Path, self.repo.ignored(*paths)))
        logger.debug(
            f"{len(paths - ignored)}/{len(paths)} under {self.path} are git included"
        )
        return paths - ignored


def main(
    paths: List[Path],
    recurse: bool,
    method: MostRecentMethod,
    include_hidden_files: bool,
    include_hidden_folders: bool,
    do_special_git_processing: bool,
):
    logger.debug(f"Processing {len(paths)} top-level paths")

    if do_special_git_processing:
        gitpaths = map(GitPath.from_path, filter_out(in_repo, paths))
        gitpaths = debug_iterable_length(
            logger=logger,
            format_string="{length} of which are in a git repository",
            iterable=gitpaths,
        )
        gitpaths = chain.from_iterable(
            map(partial(GitPath.git_included, recurse=recurse), gitpaths)
        )

    processed_paths = iter(paths)

    if recurse:
        processed_paths = chain.from_iterable(map(with_children, processed_paths))

    if do_special_git_processing:
        processed_paths = chain(processed_paths, gitpaths)

    processed_paths = filter(Path.is_file, processed_paths)

    if not include_hidden_files:
        processed_paths = filter(
            lambda path: not path.name.startswith("."), processed_paths
        )

    candidate_paths = list(processed_paths)

    if len(candidate_paths) == 0:
        raise RuntimeError("No files to sort")

    candidate_paths.sort(key=method.value)

    return candidate_paths[-1]


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
        "--include-hidden-files",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include hidden files in the search results.",
    )
    parser.add_argument(
        "--include-hidden-folders",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Recurse into hidden folders",
    )
    parser.add_argument(
        "--include-gitignored",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include gitignored files in the search results.",
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

    output = main(
        paths=args.path,
        recurse=args.recurse,
        method=args.method,
        include_hidden_files=args.include_hidden_files,
        include_hidden_folders=args.include_hidden_folders,
        do_special_git_processing=not args.include_gitignored,
    )
    print(output.as_posix())
