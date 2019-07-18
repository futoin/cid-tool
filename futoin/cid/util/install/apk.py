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


def apk(packages):
    if _ext.detect.isApk():
        packages = _ext.configutil.listify(packages)

        apk = '/sbin/apk'

        _ext.executil.trySudoCall(
            [apk, 'add'] + packages,
            errmsg='you may need to install the build deps manually !'
        )


def apkRepo(url, tag=None):
    if not _ext.detect.isApk():
        return

    apk = '/sbin/apk'
    repo_file = '/etc/apk/repositories'

    # version
    releasever = _ext.pathutil.readTextFile('/etc/alpine-release')
    releasever = releasever.strip().split('.')
    releasever = '.'.join(releasever[:2])
    repoline = url.replace('$releasever', releasever)

    # tag
    if tag:
        repoline = '@{0} {1}'.format(tag, repoline)

    repos = _ext.pathutil.readTextFile(repo_file).split("\n")
    repos = [r.strip() for r in repos]

    if repoline not in repos:
        _ext.executil.trySudoCall(
            ['/usr/bin/tee', '-a', repo_file],
            errmsg='you may need to add the repo manually!',
            input=repoline
        )
        _ext.executil.trySudoCall(
            [apk, 'update'],
            errmsg='you may need to update manually!'
        )


def apkCommunity():
    _ext.install.apkRepo(
        'http://dl-cdn.alpinelinux.org/alpine/v$releasever/community')
