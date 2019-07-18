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

from ...mixins.ondemand import ext as _ext
from .. import complex_memo as _complex_memo

from .apk import *
from .deb import *
from .ebuild import *
from .macos import *
from .pacman import *
from .rpm import *
from .java import *


def debrpm(packages):
    deb(packages)
    rpm(packages)


def generic(packages):
    apk(packages)
    deb(packages)
    brew(packages)
    pacman(packages)
    rpm(packages)

    # too different
    # emerge(packages)


@_complex_memo
def search(pattern):
    detect = _ext.detect
    pathutil = _ext.pathutil

    found = []

    # --
    apt_cache = _ext.pathutil.which('apt-cache')
    yum = _ext.pathutil.which('yum')
    dnf = _ext.pathutil.which('dnf')
    zypper = _ext.pathutil.which('zypper')

    if apt_cache:
        found = _ext.executil.callExternal(
            [apt_cache, '--names-only', 'search', pattern],
            suppress_fail=True)
        found = found.strip().split('\n')

    elif dnf or yum:
        found = _ext.executil.callExternal(
            [dnf or yum, 'search', '-q', pattern],
            suppress_fail=True)
        found = (found or '').strip().split('\n')
        found = [(f + '.').split('.')[0] for f in found]

    elif zypper:
        zypper = _ext.pathutil.which('zypper')
        res = _ext.executil.callExternal(
            [zypper, '--non-interactive', '--no-refresh',
                'search', '-t', 'package', pattern],
            suppress_fail=False)  # make user aware of failures @SLES

        found = []

        for f in (res or '').split('\n'):
            f = f.split('|')

            if len(f) > 2 and f[1] and f[1][0] != '-':
                f = f[1].strip()
                found.append(f)

    elif detect.isMacOS():
        found = _ext.install.brewSearch(pattern)

    elif detect.isAlpineLinux():
        apk = '/sbin/apk'
        found = _ext.executil.callExternal(
            [apk, 'search', pattern],
            suppress_fail=True)
        found = found.strip().split('\n')
        found = ['-'.join(f.split('-')[:-2]) for f in found]

    res = []

    for r in found:
        r = r.split()

        if r:
            r = r[0].strip()
            if r:
                res.append(r)

    return res
