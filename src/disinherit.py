from __future__ import annotations

import sys
from functools import cached_property
from importlib import import_module
from types import ModuleType
from typing import Iterable
from typing import TypeVar, Type

T = TypeVar('T')


class Attrs(frozenset):
    cache: dict[frozenset, Attrs] = {}

    def __new__(cls, args: Attrs | Iterable[str]):
        if isinstance(args, Attrs):
            return args
        if isinstance(args, str):
            args = args,
        self = super().__new__(cls, args)
        if self in cls.cache:
            return cls.cache[self]
        cls.cache[self] = self
        return self

    def __repr__(self):
        return f"{{{''.join(self)}}}"

    @cached_property
    def name_copy(self) -> dict[str, ModuleType]:
        # todo: maybe weakref?
        return {}

    def disinherit(self, item: Type[T]) -> Type[T]:
        # backup current modules
        roots = {
            cls.__module__.partition('.')[0]
            for cls in item.mro()
        }
        backup = {
            key: value
            for key, value in sys.modules.items()
            if any(
                key.startswith(root)
                for root in roots
            )
        }

        # generate new or reuse existing copies
        name_copy = self.name_copy
        for key in backup:
            if key in name_copy:
                sys.modules[key] = name_copy[key]
            else:
                del sys.modules[key]

        module = import_module(item.__module__)
        result = getattr(module, item.__name__)

        # restore backup
        for key, value in backup.items():
            name_copy[key] = import_module(key)
            sys.modules[key] = value

        # remove attributes
        for cls in result.mro():
            for attr in self:
                if attr in cls.__dict__:
                    delattr(cls, attr)

        return result


def disinherit(
        cls: Type[T],
        *attrs: str,
) -> Type[T]:
    """
    :param cls: The class that inherits the undesired attributes
    :param attrs: The attributes to remove from the class
    :return: A copy of the class with the attributes removed

    Warning: do not call this function in the same module as the class you are copying.
    This only supports classes that are imported from another module.
    """
    attrs = Attrs(attrs)
    result = attrs.disinherit(cls)

    # todo: init_subclass to raise when inheritance conflict occurs
    return result


if __name__ == '__main__':
    from pandas import DataFrame
    from geopandas import GeoDataFrame

    dataframe = disinherit(DataFrame, '__getattr__')

    assert not hasattr(dataframe, '__getattr__')
    assert hasattr(DataFrame, '__getattr__')

    geodataframe = disinherit(GeoDataFrame, '__getattr__')
    assert hasattr(DataFrame, '__getattr__')
    assert not hasattr(geodataframe, '__getattr__')
    assert hasattr(GeoDataFrame, '__getattr__')

    assert len(GeoDataFrame.mro()) == len(geodataframe.mro())
    assert len(DataFrame.mro()) == len(dataframe.mro())

    expected = set(GeoDataFrame.mro()).intersection(DataFrame.mro())
    result = set(geodataframe.mro()).intersection(dataframe.mro())
    assert len(result) == len(expected)
