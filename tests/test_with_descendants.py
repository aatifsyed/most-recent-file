from most_recent_file.get_candidates import with_descendants
from pathlib import Path
from more_itertools import consume


def test_with_descendants(tmp_path: Path):
    folder = tmp_path.joinpath("folder")
    hidden_folder = tmp_path.joinpath(".hidden_folder")

    empty_folder = tmp_path.joinpath("empty folder")
    empty_hidden_folder = tmp_path.joinpath(".empty_hidden_folder")

    file_in_folder = folder.joinpath("file_in_folder")
    hidden_file_in_folder = folder.joinpath(".hidden_file_in_folder")

    file_in_hidden_folder = hidden_folder.joinpath("file_in_hidden_folder")
    hidden_file_in_hidden_folder = hidden_folder.joinpath(
        ".hidden_file_in_hidden_folder"
    )

    consume(map(Path.mkdir, [folder, hidden_folder, empty_folder, empty_hidden_folder]))

    consume(
        map(
            Path.touch,
            [
                file_in_folder,
                hidden_file_in_folder,
                file_in_hidden_folder,
                hidden_file_in_hidden_folder,
            ],
        )
    )
