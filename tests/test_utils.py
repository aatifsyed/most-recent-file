from most_recent_file.utils import split_accumulator_before


def test_split_accumulator_before():
    splits = split_accumulator_before(
        iterable=range(7), predicate=lambda lis: len(lis) >= 3
    )
    assert list(splits) == [[0, 1], [2, 3], [4, 5], [6]]
