from itertools import chain, tee
import logging
from pathlib import Path
from typing import Any, Callable, Iterable, List, TypeVar

T = TypeVar("T")


def filter_out(predicate: Callable[[T], bool], lis: List[T]) -> List[T]:
    """Removes instances of T from lis if `predicate` returns `True`, returning the removed items"""
    matching_indices = map(lambda tup: tup[0], enumerate(filter(predicate, lis)))
    return list(map(lambda index: lis.pop(index), reversed(list(matching_indices))))


def with_children(path: Path) -> Iterable[Path]:
    return chain([path], path.rglob("*"))


def sidemap(side_effect_fn: Callable[[T], Any], iterable: Iterable[T]) -> Iterable[T]:
    for t in iterable:
        side_effect_fn(t)
        yield t


def debug_iterable_length(
    logger: logging.Logger, format_string: str, iterable: Iterable[T]
):
    if logger.isEnabledFor(logging.DEBUG):
        i0, i1 = tee(iterable)
        logger.debug(format_string.format(length=sum(1 for _ in i0)))
        iterable = i1
    return iterable
