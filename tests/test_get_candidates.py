from pathlib import Path

import git
from more_itertools import ilen

import most_recent_file.get_candidates as subject
import logging

logger = logging.getLogger(__name__)


def test_is_hidden():
    assert subject.is_hidden(Path(".hidden"))
    assert subject.is_hidden(Path("nested/.hidden"))
    assert not subject.is_hidden(Path("visible"))
    assert not subject.is_hidden(Path(".nested/visible"))


def test_has_hidden_parent():
    assert subject.has_hidden_parent(
        Path("before/.hidden/after/visible"), relative_to=Path("before")
    )
    assert not subject.has_hidden_parent(
        Path("before/.hidden/after/visible"), relative_to=Path("before/.hidden/after")
    )
    assert not subject.has_hidden_parent(Path(".hidden"), relative_to=Path())


def test_remove_gitignored(tmp_path: Path):
    git.Repo.init(path=tmp_path)
    tmp_path.joinpath("included").touch()
    included = subject.remove_gitignored(iter(tmp_path.rglob("*")), root=tmp_path)
    assert ilen(included) == 1  # Ignored .git contents

    tmp_path.joinpath("excluded").touch()
    tmp_path.joinpath(".gitignore").write_text("/excluded")

    included = subject.remove_gitignored(iter(tmp_path.rglob("*")), root=tmp_path)
    assert ilen(included) == 2  # Including .gitignore


def test_argument_list_too_long(tmp_path: Path):
    """GitPython will call subproces.Popen, which in turn calls `exec`, leaving a real possibility that we hit ERR2BIG with long argument lists."""
    git.Repo.init(path=tmp_path)
    logger.info(tmp_path)

    for i in range(50_000):
        tmp_path.joinpath(f"file{i}").touch()

    logger.info("Created files")
    subject.remove_gitignored(iter(tmp_path.rglob("*")), root=tmp_path)
