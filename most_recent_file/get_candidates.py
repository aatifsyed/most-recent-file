from typing import Iterable
from pathlib import Path, WindowsPath
from itertools import chain


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def with_descendants(
    path: Path, /, descend_hidden_folders: bool, include_hidden_files: bool
) -> Iterable[Path]:
    if not include_hidden_files and is_hidden(path):
        yield from ()
    else:
        yield path

    for child in path.glob("*"):
        if is_hidden(child):
            if child.is_dir() and descend_hidden_folders:
                yield from with_descendants(child)
            else:
                raise NotImplementedError
        else:
            yield from with_descendants(
                child,
                descend_hidden_folders=descend_hidden_folders,
                include_hidden_files=include_hidden_files,
            )


def get_candidates(path: Path, /, recurse: bool) -> Iterable[Path]:
    if path.is_file() and not recurse:
        return [path]
    else:
        return []
