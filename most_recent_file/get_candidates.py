from typing import Iterable
from pathlib import Path


def get_candidates(path: Path) -> Iterable[Path]:
    if path.is_file():
        return [path]
    else:
        return []
