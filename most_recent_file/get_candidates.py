from itertools import chain, tee
from most_recent_file.utils import split_accumulator_before
from pathlib import Path
from typing import Iterable, Iterator
import subprocess
import logging


import git
from git import InvalidGitRepositoryError

logger = logging.getLogger(__name__)

__all__ = ["is_hidden", "has_hidden_parent", "remove_gitignored", "get_candidates"]


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
    # GitPython will call subprocess, which calls exec, which has an argument length limit.
    # On large repos, we will hit ERR2BIG with our files, so anticipate this
    ARG_MAX = int(
        subprocess.run(
            ["getconf", "ARG_MAX"], capture_output=True, check=True, text=True
        ).stdout
    )

    logger.debug(f"{ARG_MAX=}")

    arguments = split_accumulator_before(
        iterable=paths,
        predicate=lambda lis: len(" ".join(str(p) for p in lis)) >= int(ARG_MAX * 0.8),
    )

    ignoreds = map(lambda args: repo.ignored(*args), arguments)

    return map(Path, chain.from_iterable(ignoreds))


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

    if not include_hidden_files:
        paths = filter(lambda path: not is_hidden(path) and path.is_file(), paths)

    if not descend_hidden_directories:
        paths = filter(
            lambda path: not has_hidden_parent(path, relative_to=root), paths
        )

    if not include_gitignored:
        paths = remove_gitignored(paths, root=root)

    if not include_folders:
        paths = filter(lambda path: not path.is_dir(), paths)

    return paths
