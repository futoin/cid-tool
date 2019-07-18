#!/usr/bin/env python

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

"""FutoIn CID v{0}

This command is alias for "cid tool exec" of FutoIn Continuous Integration & Delivery Tool.

Experience has shown that this command is used a lot in development process and
requires a dedicated alias.

Usage:
    cte <tool_name> [<tool_arg>...]
    cte list
"""

from __future__ import print_function

from .cidtool import CIDTool
from .coloring import Coloring

import os
import sys

from . import __version__ as version

if sys.version_info < (2, 7):
    print('Sorry, but only Python version >= 2.7 is supported!', file=sys.stderr)
    sys.exit(1)

__all__ = ['run']


def runInner():
    argv = sys.argv

    try:
        tool = argv[1]
    except IndexError:
        tool = None

    if tool is None or tool in ('-h', '--help', 'help'):
        print(__doc__.format(version))
    else:
        ospath = os.path

        if 'CID_COLOR' in os.environ:
            Coloring.enable(os.environ['CID_COLOR'] == 'yes')

        overrides = {}
        overrides['wcDir'] = ospath.realpath('.')

        # ---
        overrides['toolVer'] = None
        overrides['toolDetect'] = False

        # ---
        cit = CIDTool(overrides=overrides)
        cit.cte(tool, argv[2:])


def run():
    try:
        runInner()
    except Exception as e:
        print(file=sys.stderr)
        print(Coloring.error('ERROR: ' + str(e)), file=sys.stderr)
        print(file=sys.stderr)
        import traceback
        print(Coloring.warn(traceback.format_exc()), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt as e:
        print(file=sys.stderr)
        print(Coloring.error('Exit on user abort'), file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
