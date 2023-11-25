from __future__ import annotations
from functools import cached_property
from typing import TypeVar, Type, Iterable
from weakref import WeakKeyDictionary

T = TypeVar('T')

__all__ = ['remove_inherited_attributes']


class Copy:
    cache: dict[type, Copy] = WeakKeyDictionary()
    copies: dict[Attrs, Type[T]]
    original: type

    def __new__(cls, original: type | Copy):
        if isinstance(original, Copy):
            return original
        if original in cls.cache:
            return cls.cache[original]
        result = super().__new__(cls)
        cls.cache[original] = result
        return result

    def __init__(self, original: type):
        self.original = original
        # noinspection PyTypeChecker
        self.copies = WeakKeyDictionary()

    def __repr__(self):
        return f'Copy({self.original.__name__})'


class Attrs(frozenset):
    cache: dict[frozenset, Attrs] = WeakKeyDictionary()
    dicts: dict[type, dict]
    bases: dict[type, Type[T]]

    def __new__(cls, args: Attrs | Iterable[str]):
        if isinstance(args, Attrs):
            return args
        if isinstance(args, str):
            args = args,
        self = super().__new__(cls, args)
        if self in cls.cache:
            return cls.cache[self]
        cls.cache[self] = self
        self.dicts = WeakKeyDictionary()  # memoized dicts for reconstruction
        self.bases = WeakKeyDictionary()  # memoized bases for reconstruction
        return self

    def __repr__(self):
        return f"Attrs({', '.join(self)})"


class Removal:
    copy: Copy
    attrs: Attrs

    def __init__(self, copy: Copy, attrs: Attrs | Iterable[str]):
        self.copy = Copy(copy)
        self.attrs = Attrs(attrs)

    @cached_property
    def dicts(self):
        # returns a mapping of each class to its __dict__ with the attributes removed
        dicts = self.attrs.dicts
        mro = self.copy.original.mro()
        for cls in mro:
            if cls in dicts:
                continue
            __dict__ = cls.__dict__.copy()
            for attr in self.attrs:
                if attr in cls.__dict__:
                    del __dict__[attr]
            dicts[cls] = __dict__
        return dicts

    @cached_property
    def bases(self):
        # returns a mapping of each class to a copy of the class with the new dict and bases being other copies
        stack = self.copy.original.mro()
        # noinspection PyTypeChecker
        bases = self.attrs.bases
        dicts = self.dicts
        i = -1

        while stack:
            cls = stack[i]
            # skip if memoized
            if cls in bases:
                stack.pop(i)
                continue

            # reuse if unchanged
            reuse = True
            for attr in self.attrs:
                if attr in cls.__dict__:
                    reuse = False
                    break
            for base in cls.__bases__:
                assert base in bases
                if bases[base] is not base:
                    reuse = False
                    break
            if reuse:
                stack.pop(i)
                bases[cls] = cls
                continue

            # memoize copy
            __dict__ = dicts[cls]
            name = cls.__name__
            meta = cls.__class__
            __bases__ = tuple([
                bases[base]
                for base in cls.__bases__
            ])
            # noinspection PyTypeChecker
            copy = meta(name, __bases__, __dict__)
            bases[cls] = copy
            # cache the copy for the (class, attrs) pair
            Copy(cls).copies[self.attrs] = copy
            stack.pop(i)
            i = -1

        return bases

    @property
    def result(self) -> Type[T]:
        copy = self.copy
        result = self.bases[copy.original]
        for attr in self.attrs:
            assert not hasattr(result, attr)
        if len(copy.copies) > 1:
            attrs = list(copy.copies)
            raise Warning(
                f'Class {copy.original} has already been copied for removal with {attrs}; '
                f'this may lead to issues if inheriting from copies from different removals.'
            )
        return result


def remove_inherited_attributes(
        cls: Type[T],
        *attrs: str,
) -> Type[T]:
    """

    :param cls: The class that inherits the undesired attributes
    :param attrs: The attributes to remove from the class
    :return: A copy of the class with the attributes removed
    """
    removal = Removal(cls, attrs)
    result = removal.result
    return result


if __name__ == '__main__':
    """
    import remove_inherited_attributes
    remove_inherited_attributes(DataFrame, '__getattr__')
    """

    from pandas import DataFrame
    from geopandas import GeoDataFrame

    assert Attrs('__getattr__') is Attrs('__getattr__')
    assert Attrs('__getattr__') == Attrs('__getattr__')

    # test that the removal works
    dataframe = remove_inherited_attributes(DataFrame, '__getattr__')
    assert not hasattr(dataframe, '__getattr__')
    assert hasattr(DataFrame, '__getattr__')

    # test removal works for subclasses
    geodataframe = remove_inherited_attributes(GeoDataFrame, '__getattr__')
    assert not hasattr(geodataframe, '__getattr__')
    assert hasattr(GeoDataFrame, '__getattr__')

    # test that the process correctly shares base classes
    result = set(dataframe.mro()).intersection(geodataframe.mro())
    expected = set(DataFrame.mro()).intersection(GeoDataFrame.mro())
    assert len(result) == len(expected)
