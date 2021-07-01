from itertools import chain
from pathlib import Path
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")


def filter_out(predicate: Callable[[T], bool], lis: List[T]) -> List[T]:
    """Removes instances of T from lis if `predicate` returns `True`, returning the removed items"""
    matching_indices = map(lambda tup: tup[0], enumerate(filter(predicate, lis)))
    return list(map(lambda index: lis.pop(index), reversed(list(matching_indices))))


def with_children(path: Path) -> Iterable[Path]:
    return chain([path], path.rglob("*"))
