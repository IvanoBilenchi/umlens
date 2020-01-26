# Adapted from: https://github.com/mitsuhiko/werkzeug
import collections
import functools


class _Missing:

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'


_missing = _Missing()


# noinspection PyPep8Naming
class memoized:
    def __init__(self, func):
        self.func = func
        self.cache = {}

    # noinspection PyArgumentList
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    # noinspection PyUnusedLocal
    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)


# noinspection PyPep8Naming
class cached_property:
    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value
