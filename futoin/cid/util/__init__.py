#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
