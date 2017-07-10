
from functools import wraps as _wraps


def simple_memo(f):
    @_wraps(f)
    def wrap():
        fdict = f.__dict__

        if 'cached_val' in fdict:
            return fdict['cached_val']

        val = f()
        fdict['cached_val'] = val
        return val

    return wrap


def complex_memo(f):
    f.cached = {}

    @_wraps(f)
    def wrap(*args, **kwargs):
        cached = f.cached
        key = str(args) + str(kwargs)
        if key in cached:
            return cached[key]

        val = f(*args, **kwargs)

        if val is not None:
            cached[key] = val

        return val

    return wrap
