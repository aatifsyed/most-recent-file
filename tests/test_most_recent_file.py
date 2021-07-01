import dataclasses
import logging
import random
from pathlib import Path
from typing import List
from time import sleep
from datetime import timedelta

import git
import hypothesis
import most_recent_file as subject
import pytest
from more_itertools import consume

logger = logging.getLogger(__name__)


def millisleep(milliseconds: float):
    sleep(timedelta(milliseconds=milliseconds).total_seconds())


@dataclasses.dataclass
class PreparedFolder:
    folder: Path
    nodes: List[Path]  # Arbitrary order


@pytest.fixture
def simple_folder(tmp_path: Path):
    paths = [
        tmp_path.joinpath("A"),
        tmp_path.joinpath("B"),
        tmp_path.joinpath("C"),
    ]
    for path in paths:
        path.touch()
        millisleep(10)  # Allow the clock to tick
    return PreparedFolder(tmp_path, paths)


def test_picks_most_recently_modified_file(simple_folder: PreparedFolder):
    paths = simple_folder.nodes
    paths.sort(key=lambda path: path.stat().st_mtime_ns)
    expected = paths[-1]
    random.shuffle(paths)
    output = subject.main(
        paths=paths,
        recurse=False,
        method=subject.MostRecentMethod.MODIFIED,
        include_hidden_files=False,
        include_hidden_folders=False,
        do_special_git_processing=False,
    )
    assert output == expected


def test_picks_most_recently_modified_file_recursive(simple_folder: PreparedFolder):
    paths = simple_folder.nodes
    paths.sort(key=lambda path: path.stat().st_mtime_ns)
    expected = paths[-1]

    output = subject.main(
        paths=[simple_folder.folder],
        recurse=True,
        method=subject.MostRecentMethod.MODIFIED,
        include_hidden_files=False,
        include_hidden_folders=False,
        do_special_git_processing=False,
    )
    assert output == expected


def test_picks_most_recently_modified_file_git_aware(simple_folder: PreparedFolder):
    paths = simple_folder.nodes
    paths.sort(key=lambda path: path.stat().st_mtime_ns)
    gitignore_me = paths[-1]
    expected = paths[-2]

    git.Repo.init(simple_folder.folder)

    gitignore = simple_folder.folder.joinpath(".gitignore")
    gitignore.touch()

    gitignore.write_text(gitignore.relative_to(simple_folder.folder).as_posix())
    gitignore.write_text(gitignore_me.relative_to(simple_folder.folder).as_posix())

    random.shuffle(paths)
    output = subject.main(
        paths=paths,
        recurse=False,
        method=subject.MostRecentMethod.MODIFIED,
        include_hidden_files=False,
        include_hidden_folders=False,
        do_special_git_processing=True,
    )
    assert output == expected


def test_picks_most_recently_modified_file_hidden(simple_folder: PreparedFolder):
    paths = simple_folder.nodes
    hidden = simple_folder.folder.joinpath(".hidden")
    hidden.touch()
    paths.append(hidden)
    random.shuffle(paths)
    output = subject.main(
        paths=paths,
        recurse=False,
        method=subject.MostRecentMethod.MODIFIED,
        include_hidden_files=True,
        include_hidden_folders=False,
        do_special_git_processing=False,
    )
    assert output == hidden


def test_picks_most_recently_modified_file_not_hidden(simple_folder: PreparedFolder):
    paths = simple_folder.nodes
    paths.sort(key=lambda path: path.stat().st_mtime_ns)
    expected = paths[-1]

    hidden = simple_folder.folder.joinpath(".hidden")
    hidden.touch()
    paths.append(hidden)

    random.shuffle(paths)
    output = subject.main(
        paths=paths,
        recurse=False,
        method=subject.MostRecentMethod.MODIFIED,
        include_hidden_files=False,
        include_hidden_folders=False,
        do_special_git_processing=False,
    )
    assert output == expected


def test_git_aware_ignore_dot_git_folder(simple_folder: PreparedFolder):
    logger.info(simple_folder)
    git.Repo.init(simple_folder.folder)

    paths = simple_folder.nodes
    paths.sort(key=lambda path: path.stat().st_mtime_ns)
    expected = paths[-1]

    random.shuffle(paths)
    output = subject.main(
        paths=[simple_folder.folder],
        recurse=True,
        method=subject.MostRecentMethod.MODIFIED,
        include_hidden_files=False,
        include_hidden_folders=False,
        do_special_git_processing=True,
    )
    assert output == expected
