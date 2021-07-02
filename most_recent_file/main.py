from itertools import chain
from pathlib import Path
from typing import Callable, List, TypeVar

from _typeshed import SupportsLessThan

from most_recent_file.get_candidates import get_candidates

__all__ = ["main"]


T = TypeVar("T", bound=SupportsLessThan)


def main(
    roots: List[Path],
    sort_method: Callable[[Path], T],
    recurse: bool,
    include_hidden_files: bool,
    include_gitignored: bool,
    include_folders: bool,
    descend_hidden_directories: bool,
) -> Path:
    candidates = chain.from_iterable(
        map(
            lambda root: get_candidates(
                root,
                recurse=recurse,
                include_hidden_files=include_hidden_files,
                include_gitignored=include_gitignored,
                include_folders=include_folders,
                descend_hidden_directories=descend_hidden_directories,
            ),
            roots,
        )
    )
    ordered = sorted(candidates, key=sort_method)
    try:
        return ordered.pop()
    except IndexError:
        raise RuntimeError("No candidates match the specified criteria")
