from typing import Callable, Iterable, List, TypeVar
from itertools import chain
import logging

__all__ = ["split_accumulator_before"]


T = TypeVar("T")


def split_accumulator_before(
    iterable: Iterable[T], predicate: Callable[[List[T]], bool]
) -> Iterable[List[T]]:
    iterator = iter(iterable)
    current: List[T] = []

    while True:
        try:
            t = next(iterator)
            if predicate(list(chain(current, [t]))):
                yield current
                current = []
            current.append(t)
        except StopIteration:
            yield current
            return
