from most_recent_file.get_candidates import get_candidates
from pathlib import Path
from more_itertools import ilen


def test_get_candidates_only_returns_files(tmp_path: Path):
    folder = tmp_path
    file = folder.joinpath("file")
    file.touch()

    assert ilen(get_candidates(folder)) == 0
    assert ilen(get_candidates(file)) == 1
