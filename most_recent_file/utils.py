from typing import Callable, Iterable, List, TypeVar
from itertools import chain
from most_recent_file import logger

__all__ = ["split_accumulator_before"]


T = TypeVar("T")


def split_accumulator_before(
    iterable: Iterable[T], predicate: Callable[[List[T]], bool]
) -> Iterable[List[T]]:
    iterator = iter(iterable)
    current: List[T] = []

    while True:
        logger.debug(f"{len(current)=}")
        try:
            t = next(iterator)
            if predicate(list(chain(current, [t]))):
                logger.debug(f"yield list of {len(current)}")
                yield current
                current = []
            current.append(t)
        except StopIteration:
            yield current
            return
