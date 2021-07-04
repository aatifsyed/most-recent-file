import logging
import multiprocessing
from functools import partial
from itertools import chain, starmap, tee
from pathlib import Path
from typing import Iterable, Iterator, TypeVar

import git
from git import InvalidGitRepositoryError
from more_itertools import chunked

logger = logging.getLogger(__name__)

__all__ = ["is_hidden", "has_hidden_parent", "remove_gitignored", "get_candidates"]

T = TypeVar("T")


def debug_length(iterable: Iterable[T], format: str) -> Iterable[T]:
    if logger.isEnabledFor(logging.DEBUG):
        lis = list(iterable)
        logger.debug(format.format(length=len(lis)))
        return iter(lis)
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


def ignored(repo: git.Repo, *paths: Path) -> Iterable[Path]:
    # Can't pickle lambdas, but can pickle top-level functions and then partial them
    return map(Path, repo.ignored(*paths))


def gitignored(repo: git.Repo, paths: Iterable[Path]) -> Iterable[Path]:
    # GitPython will call subprocess, which calls exec, which has an argument length limit.
    # On large repos, we will hit ERR2BIG with our files, so workaround this
    CHUNK_SIZE = 100
    with multiprocessing.Pool() as pool:
        i = pool.starmap(partial(ignored, repo), chunked(paths, CHUNK_SIZE))

    return chain.from_iterable(i)


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
