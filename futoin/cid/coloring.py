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


import sys


class Coloring:
    __slots__ = ()
    _color = sys.stdout.isatty()

    @classmethod
    def enable(cls, val):
        cls._color = val

    @classmethod
    def wrap(cls, text, escape):
        if cls._color:
            ESC = chr(0x1B)
            return ESC + escape + str(text) + ESC + '[0m'
        else:
            return text

    @classmethod
    def error(cls, text):
        # bright red on black
        return cls.wrap(text, '[1;31m')

    @classmethod
    def warn(cls, text):
        # yellow on black
        return cls.wrap(text, '[33m')

    @classmethod
    def info(cls, text):
        # cyan on black
        return cls.wrap(text, '[36m')

    @classmethod
    def infoLabel(cls, text):
        # bright cyan on black
        return cls.wrap(text, '[1;36m')

    @classmethod
    def label(cls, text):
        # bright
        return cls.wrap(text, '[1m')
