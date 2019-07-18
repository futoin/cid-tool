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
from .. import log as _log


def _brew():
    return _ext.pathutil.which('brew')


def brewTap(tap):
    if not _ext.detect.isBrew():
        return

    brew = _brew()
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()
    _ext.executil.callExternal(brew_sudo + [brew, 'tap', tap], cwd='/')


def brewUnlink(formula=None, search=None):
    if not _ext.detect.isBrew():
        return

    brew = _brew()
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()

    flist = []

    if formula is not None:
        formula = _ext.configutil.listify(formula)
        flist += formula

    if search:
        flist += _ext.executil.callExternal([brew,
                                             'search', search], cwd='/').split()

    for f in flist:
        try:
            _ext.executil.callExternal(
                brew_sudo + [brew, 'unlink', f], cwd='/')
        except _ext.subprocess.CalledProcessError:
            _log.warn('You may need to unlink the formula manually!')


def brew(packages, cask=False):
    if not _ext.detect.isBrew():
        return

    packages = _ext.configutil.listify(packages)

    os = _ext.os
    brew = _brew()
    brew_sudo = os.environ.get('brewSudo', '').split()
    saved_mask = os.umask(0o022)

    try:
        for package in packages:
            try:
                if cask:
                    _ext.executil.callExternal(
                        brew_sudo + [brew, 'cask', 'install', package],
                        cwd='/',
                        user_interaction=True)
                elif brew == '/usr/local/bin/brew':
                    _ext.executil.callExternal(
                        brew_sudo + [brew, 'install',
                                     '--force-bottle', package],
                        cwd='/')
                else:
                    _ext.executil.callExternal(
                        brew_sudo + [brew, 'install', package],
                        cwd='/')
            except _ext.subprocess.CalledProcessError:
                _log.warn('You may need to enable the package manually')
    finally:
        os.umask(saved_mask)


def brewSearch(pattern, cask=False):
    if not _ext.detect.isBrew():
        return

    os = _ext.os
    brew = _brew()
    brew_sudo = os.environ.get('brewSudo', '').split()
    saved_mask = os.umask(0o022)

    pattern = '/{0}/'.format(pattern)

    if cask:
        cmd = [brew, 'cask', 'search', pattern]
    else:
        cmd = [brew, 'search', pattern]

    try:
        res = _ext.executil.callExternal(
            brew_sudo + cmd,
            cwd='/', verbose=False)
    finally:
        os.umask(saved_mask)

    return list(filter(None, res.strip().split('\n')))


def dmg(packages):
    if not _ext.detect.isMacOS():
        return

    packages = _ext.configutil.listify(packages)

    os = _ext.os
    path = _ext.pathutil
    glob = _ext.glob

    curl = _ext.pathutil.which('curl')
    hdiutil = _ext.pathutil.which('hdiutil')
    installer = _ext.pathutil.which('installer')
    volumes_dir = '/Volumes'

    for package in packages:
        base_name = package.split('/')[-1]
        local_name = os.path.join(os.environ['HOME'])

        # TODO: change to use env timeouts
        _ext.executil.callExternal([
            curl,
            '-fsSL',
            '--connect-timeout', '10',
            '--max-time', '300',
            '-o', base_name,
            package
        ])

        volumes = set(os.listdir(volumes_dir))
        _ext.executil.trySudoCall([hdiutil, 'attach', local_name])
        volume = (set(os.listdir(volumes_dir)) - volumes)[0]

        pkg = glob.glob(os.path.join(volumes_dir, volume, '*.pkg'))
        _ext.executil.trySudoCall([installer, '-package', pkg, '-target', '/'])

        _ext.executil.trySudoCall([hdiutil, 'dettach', local_name])
