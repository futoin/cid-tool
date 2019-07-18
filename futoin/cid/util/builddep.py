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

from ..mixins.ondemand import ext as _ext
from . import log as _log

_BUIID_DEP_PREFIX = '_bdep_'
_SYSTEM_VER = 'system'


def essential():
    _ext.install.SUSEConnectVerArch('sle-module-toolchain')
    _ext.install.SUSEConnectVerArch('sle-sdk', True)

    _ext.install.deb([
        'build-essential',
    ])
    _ext.install.rpm([
        'binutils',
        'gcc',
        'gcc-c++',
        'glibc-devel',
        'libtool',
        'make',
        'patch'
    ])

    _ext.install.yum('redhat-rpm-config')

    _ext.install.apk([
        'build-base',
        'linux-headers',
    ])


def require(env, dep):
    dep = _ext.configutil.listify(dep)

    essential()

    for d in dep:
        m = '{0}{1}'
        m = m.format(_BUIID_DEP_PREFIX, d.replace('-', ''))
        m = globals().get(m, None)

        if m:
            m(env)
        else:
            _log.errorExit('Unknown build dep "{0}"'.format(d))


def available():
    ret = []

    for m in globals():
        if m.startswith(_BUIID_DEP_PREFIX):
            m = m.replace(_BUIID_DEP_PREFIX, '')
            ret.append(m)

    return ret


def _bdep_ruby(env):
    detect = _ext.detect
    ver = env['rubyVer']

    if ver == _SYSTEM_VER:
        _ext.install.deb(['ruby-dev'])
        _ext.install.rpm(['ruby-devel'])
        _ext.install.apk(['ruby-dev'])
    elif detect.isSCLSupported():
        devver = ver.replace('.', '')

        if devver == '19':
            sclname = 'ruby193-ruby-devel'
        elif devver == '20':
            sclname = 'ruby200-ruby-devel'
        else:
            sclname = 'rh-ruby{0}-ruby-devel'.format(devver)

        _ext.install.rpm(sclname)
    elif detect.isDebian() or detect.isUbuntu():
        if ver == '1.9':
            pkgver = '1.9.[0-9]'
        else:
            pkgver = ver

        _ext.install.deb([
            'ruby{0}-dev'.format(pkgver),
        ])


def _bdep_python(env):
    if int(env['pythonVer'].split('.')[0]) == 3:
        _ext.install.deb(['python3-dev'])
        _ext.install.zypper(['python3-devel'])
        _ext.install.yum(['python3-devel'])
        _ext.install.yum(['python34-devel'])
        _ext.install.apk(['python3-dev'])
    else:
        _ext.install.deb(['python-dev'])
        _ext.install.rpm(['python-devel'])
        _ext.install.apk(['python2-dev'])


def _bdep_ssl(env):
    _bdep_ssl10(env)


def _bdep_ssl10(env):
    apt_cache = _ext.pathutil.which('apt-cache')

    if apt_cache and _ext.executil.callExternal([apt_cache, 'search', 'libssl1.0-dev']).strip():
        _ext.install.deb('libssl1.0-dev')
    else:
        _ext.install.deb('libssl-dev')
    _ext.install.rpm('openssl-devel')
    _ext.install.rpm('libopenssl-devel')
    _ext.install.apk('libressl-dev')
    # _ext.install.pacman('openssl')
    _ext.install.pacman('openssl-1.0')
    _ext.install.brew('openssl')


def _bdep_mysqlclient(env):
    _ext.install.deb('libmysqlclient-dev')
    _ext.install.deb('default-libmysqlclient-dev')

    if _ext.detect.isOracleLinux():
        _ext.install.yum(['mariadb-devel', 'mariadb-libs'])
    else:
        _ext.install.yum('mysql-devel')

    _ext.install.zypper('libmysqlclient-devel')
    _ext.install.pacman('libmariadbclient')
    _ext.install.apk('mariadb-dev')
    _ext.install.brew('mysql')


def _bdep_postgresql(env):
    _ext.install.deb('libpq-dev')
    _ext.install.rpm(['postgresql-devel', 'postgresql-libs'])
    _ext.install.pacman('postgresql')
    _ext.install.apk('postgresql-dev')
    _ext.install.brew('postgresql')


def _bdep_imagemagick(env):
    _ext.install.deb('libmagick-dev')
    _ext.install.rpm(['imagemagick', 'imagemagick-devel'])
    _ext.install.pacman('imagemagick')
    _ext.install.apk('imagemagick-dev')
    _ext.install.brew('imagemagick')


def _bdep_tzdata(env):
    _ext.install.deb('tzdata')
    _ext.install.rpm('tzdata')
    _ext.install.pacman('tzdata')
    _ext.install.apk('tzdata')


def _bdep_libxml2(env):
    _ext.install.deb('libxml2-dev')
    _ext.install.rpm('libxml2-devel')
    _ext.install.pacman('libxml2')
    _ext.install.apk('libxml2')
    _ext.install.brew('libxml2')
