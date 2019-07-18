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

from __future__ import print_function

from ..coloring import Coloring
from ..mixins.ondemand import ext as _ext


def info(msg, label=None):
    if label:  # for backward compatibility
        infoLabel(label, msg)
        return

    line = Coloring.info('INFO: ' + msg)
    print(line, file=_ext.sys.stderr)


def infoLabel(label, msg):
    line = Coloring.infoLabel(label) + Coloring.info(msg)
    print(line, file=_ext.sys.stderr)


def warn(msg):
    print(Coloring.warn('WARNING: ' + msg), file=_ext.sys.stderr)


def errorExit(msg):
    raise RuntimeError(msg)
