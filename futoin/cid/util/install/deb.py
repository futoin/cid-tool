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


def deb(packages):
    if not _ext.detect.isDeb():
        return

    apt_get = _ext.pathutil.which('apt-get')

    packages = _ext.configutil.listify(packages)

    _ext.os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
    _ext.executil.trySudoCall(
        [apt_get, 'install', '-y',
            '--no-install-recommends',
            '-o', 'Dpkg::Options::=--force-confdef',
            '-o', 'Dpkg::Options::=--force-confold'] + packages,
        errmsg='you may need to install the packages manually !'
    )


def aptRepo(name, entry, gpg_key=None, codename_map=None, repo_base=None):
    if not _ext.detect.isDeb():
        return

    deb([
        'software-properties-common',
        'apt-transport-https',
        'ca-certificates',
        'lsb-release',
    ])
    apt_add_repository = _ext.pathutil.which('apt-add-repository')

    if not apt_add_repository:
        return

    if gpg_key:
        tmp_dir = _ext.pathutil.tmpCacheDir(prefix='cidgpg')
        tf = _ext.ospath.join(tmp_dir, 'key.gpg')
        _ext.pathutil.writeBinaryFile(tf, gpg_key)

        _ext.executil.trySudoCall(
            ['apt-key', 'add', tf],
            errmsg='you may need to import the PGP key manually!'
        )

        _ext.os.remove(tf)

    codename = _ext.detect.osCodeName()

    if codename_map:
        try:
            repo_info = _ext.urllib.urlopen(
                '{0}/{1}'.format(repo_base, codename)).read()
        except:
            fallback_codename = codename_map.get(codename, codename)
            _log.warn('Fallback to codename: {0}'.format(
                fallback_codename))
            codename = fallback_codename

    entry = entry.replace('$codename$', codename)

    _ext.executil.trySudoCall(
        [apt_add_repository, '--yes', entry],
        errmsg='you may need to add the repo manually!'
    )

    _ext.executil.trySudoCall(
        ['apt-get', 'update'],
        errmsg='you may need to update APT cache manually!'
    )


def dpkg(env, name, url, apt_update=False):
    if not _ext.detect.isDeb():
        return

    pathutil = _ext.pathutil
    apt_cache = pathutil.which('apt-cache')

    if apt_cache and _ext.executil.callExternal([apt_cache, 'show', name], suppress_fail=True):
        _ext.install.deb(name)
    else:
        dpkg = pathutil.which('dpkg')

        if _ext.executil.callExternal([dpkg, '-s', name], suppress_fail=True):
            return

        cache_file = pathutil.cacheDownloadFile(env, url)
        _ext.executil.trySudoCall([dpkg, '-i', cache_file])

    if apt_update:
        _ext.executil.trySudoCall(
            ['apt-get', 'update'],
            errmsg='you may need to update APT cache manually!'
        )
