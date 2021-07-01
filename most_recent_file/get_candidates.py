from itertools import tee
from pathlib import Path
from typing import Iterable, Iterator

import git
from git import InvalidGitRepositoryError


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def has_hidden_parent(path: Path, /, relative_to: Path) -> bool:
    return any(
        map(
            is_hidden,
            path.relative_to(relative_to).parents,
        ),
    )


def remove_gitignored(paths: Iterator[Path], /, root: Path) -> Iterator[Path]:
    try:
        repo = git.Repo(path=root, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return paths

    dot_git = Path(repo.common_dir)
    paths = filter(lambda path: not path.is_relative_to(dot_git), paths)

    p0, p1 = tee(paths)

    ignored = set(map(Path, repo.ignored(*p0)))

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
