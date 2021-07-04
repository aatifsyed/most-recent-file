import logging
import multiprocessing
from functools import partial
from itertools import chain, tee
from pathlib import Path
from sys import stderr
from tempfile import SpooledTemporaryFile
from typing import Iterable, Iterator, TypeVar

import git
import subprocess
from git import InvalidGitRepositoryError
from more_itertools import chunked

logger = logging.getLogger(__name__)

__all__ = ["is_hidden", "has_hidden_parent", "remove_gitignored", "get_candidates"]

T = TypeVar("T")


def debug_length(iterable: Iterator[T], format: str) -> Iterator[T]:
    if logger.isEnabledFor(logging.DEBUG):
        lis = list(iterable)
        logger.debug(format.format(length=len(lis)))
        return iter(lis)
    else:
        return iterable


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def has_hidden_parent(path: Path, /, relative_to: Path) -> bool:
    return any(
        map(
            is_hidden,
            path.relative_to(relative_to).parents,
        ),
    )


def gitignored(repo: git.Repo, paths: Iterable[Path]) -> Iterable[Path]:
    # git.Repo.ignored will call subprocess, which calls exec, which has an argument length limit.
    # On large repos, we will hit ERR2BIG with our files, so workaround this

    process = subprocess.Popen(
        ["git", "check-ignore", "--stdin"],
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=repo.working_tree_dir,
    )

    stdin = "\n".join(str(path) for path in paths)
    stdout, stderr = process.communicate(input=stdin)
    process.wait()

    return map(Path, stdout.splitlines())


def remove_gitignored(paths: Iterator[Path], /, root: Path) -> Iterator[Path]:
    try:
        repo = git.Repo(path=root, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return paths

    dot_git = Path(repo.common_dir)
    paths = filter(lambda path: not path.is_relative_to(dot_git), paths)

    p0, p1 = tee(paths)

    ignored = set(gitignored(repo=repo, paths=p0))

    return filter(lambda path: path not in ignored, p1)


def get_candidates(
    root: Path,
    /,
    recurse: bool,
    include_hidden_files: bool,
    include_gitignored: bool,
    include_folders: bool,
    descend_hidden_directories: bool,
) -> Iterable[Path]:
    root = root.resolve()

    if recurse:
        paths = iter(root.rglob("*"))
    else:
        paths = iter([root])

    paths = debug_length(paths, "Initial discovery: {length} paths")

    if not include_hidden_files:
        paths = filter(lambda path: not is_hidden(path) and path.is_file(), paths)
        paths = debug_length(paths, "After removing hidden files: {length} paths")

    if not descend_hidden_directories:
        paths = filter(
            lambda path: not has_hidden_parent(path, relative_to=root), paths
        )
        paths = debug_length(paths, "After removing hidden directories: {length} paths")

    if not include_gitignored:
        paths = remove_gitignored(paths, root=root)
        paths = debug_length(paths, "After removing gitignored: {length} paths")

    if not include_folders:
        paths = filter(lambda path: not path.is_dir(), paths)

    paths = debug_length(paths, "Returning: {length} paths")
    return paths
