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
from . import simple_memo as _simple_memo
from . import complex_memo as _complex_memo
from . import log as _log

_SYSTEM_VER = 'system'


@_simple_memo
def binaryVersions():
    detect = _ext.detect

    if detect.isDebian() or detect.isUbuntu():
        return ['5.6', '7.0', '7.1', '7.2', '7.3']

    if detect.isSCLSupported():
        return ['5.6', '7.0', '7.1', '7.2', '7.3']

    if detect.isArchLinux():
        # return ['5.6', '7.0', '7.1']
        return None

    if detect.isAlpineLinux():
        alpine_ver = detect.alpineLinuxVersion()

        if alpine_ver >= ['3', '8']:
            return ['5.6', '7.2']

        if alpine_ver >= ['3', '6']:
            return ['5.6', '7.1']

        if alpine_ver >= ['3', '5']:
            return ['5.6', '7.0']

        return ['5.6']

    if detect.isMacOS():
        return ['7.1', '7.2', '7.3']

    return None


@_complex_memo
def basePackage(ver):
    detect = _ext.detect
    ver_nodot = ver.replace('.', '')

    if detect.isDebian() or detect.isUbuntu():
        if ver == _SYSTEM_VER:
            if detect.osCodeName() in ['jessie', 'trusty']:
                return 'php5'

            return 'php'

        return 'php{0}'.format(ver)

    if detect.isSCLSupported():
        if isIUSVer(ver):
            return 'php{0}u'.format(ver_nodot)
        else:
            return 'rh-php{0}'.format(ver_nodot)

    if detect.isArchLinux():
        if isArchLatest(ver):
            return 'php'

        return 'php{0}'.format(ver_nodot)

    if detect.isAlpineLinux():
        if isAlpineSplit():
            return 'php{0}'.format(ver.split('.')[0])

        return 'php'

    if detect.isMacOS():
        return 'php@{0}'.format(ver)

    if detect.isFedora():
        return 'php'

    if detect.isOpenSUSE():
        return 'php7'

    if detect.isSLES():
        return 'php7'

    return 'php'


def createBinDir(env, src_bin):
    ospath = _ext.ospath
    os = _ext.os
    pathutil = _ext.pathutil

    php_dir = ospath.join(os.environ['HOME'], '.php', env['phpVer'])
    php_dir = env.setdefault('phpDir', php_dir)

    php_bin_dir = ospath.join(php_dir, 'bin')
    php_bin = ospath.join(php_bin_dir, 'php')

    if not ospath.exists(php_bin_dir):
        os.makedirs(php_bin_dir)

    _ext.pathutil.addBinPath(php_bin_dir, True)

    if ospath.exists(src_bin):
        if ospath.islink(php_bin) and os.readlink(php_bin) == src_bin:
            pass
        else:
            pathutil.rmTree(php_bin)
            os.symlink(src_bin, php_bin)

        env['phpBin'] = php_bin
        env['phpFakeBinDir'] = php_bin_dir
        return True

    elif 'phpBin' in env:
        del env['phpBin']

    return False


@_simple_memo
def isAlpineSplit():
    return _ext.detect.alpineLinuxVersion() >= ['3', '5']


def isArchLatest(ver):
    # return ver == '7.1'
    return True


def isIUSVer(ver):
    return ver == '7.1'


def installedExtensions(env):
    known = {k: None for k in knownExtensions()}
    # ---
    res = _ext.executil.callExternal(
        [env['phpBin'], '-m'],
        verbose=False)
    res = res.strip().split('\n')

    for r in res:
        r = r.lower().strip()

        if r == 'Zend OPcache':
            r = 'opcache'

        if r == 'mysqlnd':
            r = 'mysql'

        if r in known:
            known[r] = True

    return known


def extPackages(env, known=None):  # NOTE: do not cache
    ver = env['phpVer']
    base_pkg = basePackage(ver)
    pkg_prefix = '{0}-'.format(base_pkg)
    pkg_prefix2 = None
    detect = _ext.detect
    install = _ext.install

    known = known or installedExtensions(env)
    update = {}
    pkg2key = {}
    found = []

    # ---
    if detect.isDebian() or detect.isUbuntu():
        pkg2key = {
            'mysqlnd': 'mysql',
        }
        pkg_prefix2 = 'php-'

    elif detect.isSCLSupported():
        if isIUSVer(ver):
            pkg_prefix2 = '{0}-pecl-'.format(base_pkg)
        else:
            pkg_prefix = '{0}-php-'.format(base_pkg)
            pkg_prefix2 = '{0}-php-pecl-'.format(base_pkg)

        pkg2key = {
            'mysqlnd': 'mysql',
            'process': 'pcntl',
        }

    elif detect.isArchLinux() or detect.isGentoo():
        pkg_prefix = None

    elif detect.isMacOS():
        pkg2key = {
            'pdo-pgsql': 'pgsql',
        }

    elif detect.isFedora():
        pkg_prefix2 = pkg_prefix + 'pecl-'
        pkg2key = {
            'mysqlnd': 'mysql',
            'process': 'pcntl',
        }

    # ---
    if pkg_prefix:
        found += install.search(pkg_prefix)

    if pkg_prefix2:
        found += install.search(pkg_prefix2)

    # ---
    if found:
        for p in found:
            # NOTE: in that order!
            if pkg_prefix2:
                k = p.replace(pkg_prefix2, '')

            k = k.replace(pkg_prefix, '')

            if not k:
                continue

            k = pkg2key.get(k, k)

            if k in known:
                update[k] = p

    # ---
    for (k, v) in update.items():
        if k in known:
            if not known[k]:
                known[k] = v
        else:
            _log.errorExit('Unknown generic PHP ext "{0}"'.format(k))

    return known


def knownExtensions():
    return [
        'amqp',
        'apcu',
        'ast',
        'bcmath',
        'bz2',
        'blitz',
        'calendar',
        'ctype',
        'curl',
        'couchbase',
        'date',
        'ds',
        'ev',
        'enchant',
        'event',
        'exif',
        'fileinfo',
        'filter',
        'ftp',
        'gettext',
        'gd',
        'gearman',
        'geoip',
        'gmagick',
        'gmp',
        'gnupg',
        'grpc',
        'hash',
        'http',
        'iconv',
        'imagick',
        'imap',
        'intl',
        'json',
        'ldap',
        'kafka',
        'mailparse',
        'mbstring',
        'mysql',
        'mcrypt',
        'memcache',
        'memcached',
        'mongodb',
        'msgpack',
        'odbc',
        'opcache',
        'openssl',
        'pcntl',
        'pcre',
        'pdo',
        'pdo_mysql',
        'pdo_pgsql',
        'pdo_sqlite',
        'phar',
        'pgsql',
        'posix',
        'pspell',
        'readline',
        'recode',
        'redis',
        'session',
        'shmop',
        'snmp',
        'simplexml',
        'soap',
        'sockets',
        'spl',
        'sqlite3',
        'ssh2',
        'sysvmsg',
        'sysvsem',
        'sysvshm',
        'tokenizer',
        'uv',
        'xdebug',
        'xml',
        'xmlreader',
        'xmlrpc',
        'xmlwriter',
        'xsl',
        'zlib',
        'zip',
        'zmq',
    ]


def installExtensions(env, exts, permissive=True):
    exts = _ext.configutil.listify(exts)

    # ---
    known = installedExtensions(env)

    for ext in exts:
        if ext in known:
            if known[ext] != True:
                break
        else:
            _log.errorExit('Unknown PHP extension "{0}"\nKnown: \n* {1}'.format(
                ext, '\n* '.join(knownExtensions())))
    else:
        return

    # ---
    mapping = extPackages(env, known)
    install = _ext.install

    to_install = []

    for ext in exts:
        if ext in mapping:
            pkg = mapping[ext]

            if type(pkg) == type(''):
                to_install.append(pkg)
            elif not pkg:
                msg = 'Not supported PHP extension: {0}'.format(ext)

                if permissive:
                    _log.warn(msg)
                else:
                    _log.errorExit(msg)
        else:
            _log.errorExit('Unknown PHP extension "{0}"\nKnown: \n* {1}'.format(
                ext, '\n* '.join(knownExtensions())))

    # ---
    detect = _ext.detect

    if detect.isDisabledToolsSetup(env):
        _log.errorExit(
            'environment requires external management of tools')
        return

    if detect.isExternalToolsSetup(env):
        _ext.executil.externalSetup(env, [
            'tool', 'install', 'php'])
        return

    # ---
    for pkg in to_install:
        install.deb(pkg)
        install.rpm(pkg)
        install.brew(pkg)
        install.apk(pkg)
        install.pacman(pkg)
        install.emerge(pkg)
