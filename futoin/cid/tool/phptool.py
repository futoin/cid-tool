
from __future__ import print_function, absolute_import

import os
import fnmatch
import glob
import subprocess

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class phpTool(BashToolMixIn, CurlToolMixIn, RuntimeTool):
    """PHP is a popular general-purpose scripting language that is especially suited to web development.

Home: http://php.net/


By default the latest available PHP binary is used for the following OSes:
* Debian & Ubuntu - uses Sury (https://deb.sury.org/) builds 5.6, 7.0 & 7.1.
* CentOS, RHEL & Oracle Linux - uses SCL 5.6 & 7.0

You can forbid source builds by setting phpBinOnly to non-empty string.

However, if phpVer is set then we use php-build which make consume a lot of time and
resources due to lack of trusted binary builds.
"""
    PHP_DIR = os.path.join(os.environ['HOME'], '.php')

    def getDeps(self):
        return (
            ['phpbuild'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        php_ver = env['phpVer']

        if php_ver == self.SYSTEM_VER:
            self._systemDeps()
            return

        if env['phpBinOnly']:
            self._installBinaries(env)
            return

        php_dir = env['phpDir']

        try:
            os.makedirs(php_dir)
        except:
            pass

        self._buildDeps(env)

        old_tmpdir = os.environ.get('TMPDIR', '/tmp')
        os.environ['TMPDIR'] = os.path.join(php_dir, '..')
        self._callExternal(
            [env['phpbuildBin'], env['phpSrcVer'], env['phpDir']])
        os.environ['TMPDIR'] = old_tmpdir

    def _installBinaries(self, env):
        ver = env['phpVer']

        if self._isDebian():
            repo = env.get('phpSuryRepo', 'https://packages.sury.org/php')
            gpg = self._callCurl(env, [repo + '/apt.gpg'])

            self._addAptRepo(
                'sury', "deb {0} $codename$ main".format(repo), gpg)
            self._requireDeb('php' + ver)

        elif self._isUbuntu():
            self._addAptRepo('sury', 'ppa:ondrej/php', None)
            self._requireDeb('php' + ver)

        elif self._isSCLSupported():
            if self._isPHPSCL(env):
                ver = ver.replace('.', '')

                self._requireSCL()

                self._requireYum([
                    'rh-php{0}'.format(ver),
                    'rh-php{0}-php-devel'.format(ver),
                ])
            else:
                self._errorExit('Only SCL packages are supported so far')

        elif self._isMacOS():
            self._requireBrewTap('homebrew/homebrew-php')
            ver = ver.replace('.', '')
            base_formula = 'homebrew/php/php{0}'.format(ver)

            self._requireBrewUnlink(search='/homebrew\/php\/php[0-9]{2}$/')
            self._requireBrew(base_formula)

            formulas = [
                'apcu',
                'opcache',
            ]

            self._requireBrew(['{0}-{1}'.format(base_formula, f)
                               for f in formulas])

        else:
            self._systemDeps()

    def _isPHPSCL(self, env):
        return env['phpVer'] in ('5.6', '7.0')

    def updateTool(self, env):
        pass

    def uninstallTool(self, env):
        if env['phpVer'] == self.SYSTEM_VER or env['phpBinOnly']:
            return super(phpTool, self).uninstallTool(env)

        php_dir = env['phpDir']

        if os.path.exists(php_dir):
            self._rmTree(php_dir)

        self._have_tool = False

    def envNames(self):
        return ['phpDir', 'phpBin', 'phpVer', 'phpfpmVer', 'phpBinOnly', 'phpSuryRepo']

    def initEnv(self, env):
        #---
        # TODO: rewrite similar to ruby, and add dynamic detection
        if self._isDebian() or self._isUbuntu():
            php_latest = '7.1'
        elif self._isSCLSupported():
            php_latest = '7.0'
        elif self._isAlpineLinux():
            php_latest = '7.0'
        elif self._isMacOS():
            php_latest = '7.1'
        else:
            php_latest = None

        #---
        if 'phpfpmVer' in env:
            php_ver = env.setdefault('phpVer', env['phpfpmVer'])

        if php_latest:
            php_ver = env.setdefault('phpVer', php_latest)
            phpBinOnly = True

            if php_ver[0] == '5' and php_ver != '5.6':
                php_ver = '5.6'
                self._warn('Forcing PHP 5.6 for PHP 5.x requirement')
            elif php_ver == '7':
                php_ver = php_latest
            elif self._isMacOS():
                # Homebrew supports all
                pass
            elif php_ver > php_latest:
                phpBinOnly = False
                self._warn(
                    'Binary builds are supported only for 5.6 - {0}'.format(php_latest))

            env['phpVer'] = php_ver
        else:
            phpBinOnly = False
            php_ver = env.setdefault('phpVer', self.SYSTEM_VER)

        if phpBinOnly:
            env['phpBinOnly'] = phpBinOnly
        else:
            phpBinOnly = env.setdefault('phpBinOnly', phpBinOnly)

        #---
        if php_ver == self.SYSTEM_VER:
            super(phpTool, self).initEnv(env)
            return
        elif phpBinOnly:
            if self._isDebian() or self._isUbuntu():
                bin_name = 'php' + php_ver
                super(phpTool, self).initEnv(env, bin_name)

            elif self._isSCLSupported():
                if self._isPHPSCL(env):
                    ver = env['phpVer'].replace('.', '')
                    try:
                        env_to_set = self._callBash(
                            env, 'scl enable rh-php{0} env'.format(ver), verbose=False)
                    except subprocess.CalledProcessError:
                        return

                    self._updateEnvFromOutput(env_to_set)
                    super(phpTool, self).initEnv(env)
                else:
                    pass

            elif self._isAlpineLinux():
                bin_name = 'php' + php_ver[0]
                super(phpTool, self).initEnv(env, bin_name)

            elif self._isMacOS():
                brew_prefix = env['brewDir']
                formula = 'php' + php_ver.replace('.', '')
                php_dir = os.path.join(brew_prefix, 'opt', formula, 'bin')

                if os.path.exists(php_dir):
                    self._addBinPath(php_dir, True)
                    super(phpTool, self).initEnv(env)

            return
        else:
            def_dir = os.path.join(
                env['phpbuildDir'], 'share', 'php-build', 'definitions')

            if not os.path.exists(def_dir):
                return

            defs = os.listdir(def_dir)
            defs = fnmatch.filter(defs, php_ver + '*')

            if not defs:
                self._errorExit('PHP version "{0}" not found'.format(php_ver))

            def castver(v):
                try:
                    return int(v)
                except:
                    return -1

            defs.sort(key=lambda v: [castver(u) for u in v.split('.')])
            php_ver = defs[-1]

            env['phpSrcVer'] = php_ver

        php_dir = env.setdefault('phpDir', os.path.join(self.PHP_DIR, php_ver))
        php_bin_dir = os.path.join(php_dir, 'bin')
        php_bin = os.path.join(php_bin_dir, 'php')

        if os.path.exists(php_bin):
            self._have_tool = True
            self._addBinPath(php_bin_dir, True)
            env.setdefault('phpBin', php_bin)

    def _buildDeps(self, env):
        self._requireBuildDep(env, [
            'ssl',
            'mysqlclient',
            'postgresql',
        ])
        # APT
        #---
        self._requireDeb([
            'build-essential',
            'bison',
            'automake',
            'autoconf',
            'libtool',
            're2c',
            'libcurl4-openssl-dev',
            'libtidy-dev',
            'libpng-dev',
            'libmcrypt-dev',
            'libjpeg-dev',
            'libreadline-dev',
            'libbz2-dev',
            'libc-client-dev',
            'libdb-dev',
            'libedit-dev',
            'libenchant-dev',
            'libevent-dev',
            'libexpat1-dev',
            'libfreetype6-dev',
            'libgcrypt11-dev',
            'libgd2-dev',
            'libglib2.0-dev',
            'libgmp3-dev',
            'libicu-dev',
            'libjpeg-dev',
            'libkrb5-dev',
            'libldap2-dev',
            'libmagic-dev',
            'libmhash-dev',
            'libonig-dev',
            'libpam0g-dev',
            'libpcre3-dev',
            'libpng-dev',
            'libpspell-dev',
            'libqdbm-dev',
            'librecode-dev',
            'libsasl2-dev',
            'libsnmp-dev',
            'libsqlite3-dev',
            'libwrap0-dev',
            'libxmltok1-dev',
            'libxml2-dev',
            'libvpx-dev',
            'libxslt1-dev',
            'unixodbc-dev',
            'zlib1g-dev',
        ])

        # Extra repo before the rest
        #---
        self._requireYumEPEL()

        self._requireRpm([
            'binutils',
            'patch',
            'git',
            'gcc',
            'gcc-c++',
            'make',
            'autoconf',
            'automake',
            'libtool',
            'bison',
            're2c',
            'glibc-devel',
            'libxml2-devel',
            'pkgconfig',
            'curl-devel',
            'libpng-devel',
            'libjpeg-devel',
            'libXpm-devel',
            'freetype-devel',
            'gmp-devel',
            'libmcrypt-devel',
            'aspell-devel',
            'recode-devel',
            'libicu-devel',
            'oniguruma-devel',
            'libtidy-devel',
            'libxslt-devel',
            'readline-devel',
            'zlib-devel',
            'pcre-devel',
        ])

        self._requireYum('bzip2-devel')
        self._requireZypper('libbz2-devel')

        self._requireEmergeDepsOnly(['dev-lang/php'])
        self._requirePacman([
            'patch',
            'git',
            'gcc',
            'make',
            'autoconf',
            'automake',
            'libtool',
            'bison',
            're2c',
            'glibc',
            'libxml2',
            'curl',
            'libpng',
            'libjpeg',
            'libxpm',
            'freetype2',
            'gmp',
            'libmcrypt',
            'aspell',
            'recode',
            'icu',
            'oniguruma',
            'tidy',
            'libxslt',
            'readline',
            'zlib',
            'pcre',
        ])

        #---
        systemctl = self._which('systemctl')

        if systemctl:
            self._requireDeb(['libsystemd-dev'])
            self._requireRpm(['systemd-devel'])
            with_systemd = ' --with-fpm-systemd'
        else:
            with_systemd = ' --without-fpm-systemd'

        multiarch = None
        dpkgarch = self._which('dpkg-architecture')

        if dpkgarch:
            multiarch = self._callExternal(
                [dpkgarch, '-qDEB_HOST_MULTIARCH']).strip()

        if multiarch:
            if os.path.exists(os.path.join('/usr/include', multiarch, 'curl')):
                curl_dir = os.path.join(env['phpDir'], '..', 'curl')

                try:
                    os.mkdir(curl_dir)
                    os.symlink(os.path.join('/usr/include', multiarch),
                               os.path.join(curl_dir, 'include'))
                    os.symlink(os.path.join('/usr/lib', multiarch),
                               os.path.join(curl_dir, 'lib'))
                except Exception as e:
                    # print(e)
                    pass
            else:
                curl_dir = '/usr/include'

            with_libdir = ' --with-libdir={0} --with-curl={1}'.format(
                os.path.join('lib', multiarch),
                curl_dir,
            )
        else:
            with_libdir = ''
        #---
        from ..details.resourcealgo import ResourceAlgo
        cpu_count = ResourceAlgo().cpuLimit({})

        os.environ['PHP_BUILD_EXTRA_MAKE_ARGUMENTS'] = '-j{0}'.format(
            cpu_count)

        os.environ['PHP_BUILD_CONFIGURE_OPTS'] = ' \
            --disable-debug \
            --with-regex=php \
            --enable-calendar \
            --enable-sysvsem \
            --enable-sysvshm \
            --enable-sysvmsg \
            --enable-bcmath \
            --disable-cgi \
            --disable-phpdbg \
            --enable-fpm \
            --with-bz2 \
            --enable-ctype \
            --without-db4 \
            --without-qdbm \
            --without-gdbm \
            --with-iconv \
            --enable-exif \
            --enable-ftp \
            --with-gettext \
            --enable-mbstring \
            --with-onig=/usr \
            --with-pcre-regex=/usr \
            --enable-shmop \
            --enable-sockets \
            --enable-wddx \
            --with-libxml-dir=/usr \
            --with-zlib \
            --with-kerberos=/usr \
            --with-openssl=/usr \
            --enable-soap \
            --enable-zip \
            --with-mhash=yes \
            --with-system-tzdata \
            ' + with_systemd + with_libdir

    def _systemDeps(self):
        self._requireDeb([
            'php.*-cli',
            'php.*-fpm',
            "php.*-apcu",
            "php.*-curl",
            "php.*-gd",
            "php.*-geoip",
            "php.*-gmp",
            "php.*-imagick",
            "php.*-imap",
            "php.*-intl",
            "php.*-json",
            "php.*-ldap",
            "php.*-mcrypt",
            "php.*-msgpack",
            "php.*-ssh2",
            "php.*-soap",
            "php.*-sqlite",
            "php.*-xml",
            "php.*-xmlrpc",
            "php.*-xsl",
        ])

        # SuSe-like
        self._requireZypper([
            'php?',
            'php*-fpm',
            'php*-bcmath',
            'php*-bz2',
            'php*-calendar',
            'php*-ctype',
            'php*-curl',
            'php*-dom',
            'php*-exif',
            'php*-fileinfo',
            'php*-gettext',
            'php*-gmp',
            'php*-iconv',
            'php*-imap',
            'php*-intl',
            'php*-json',
            'php*-ldap',
            'php*-mbstring',
            'php*-mcrypt',
            'php*-pcntl',
            'php*-pdo',
            'php*-phar',
            'php*-soap',
            'php*-sockets',
            'php*-sqlite',
            'php*-tidy',
            'php*-xmlreader',
            'php*-xmlrpc',
            'php*-xmlwriter',
            'php*-xsl',
            'php*-zip',
            'php*-zlib',
        ])

        # RedHat-like
        self._requireYum([
            'php-cli',
            'php-fpm',
            'php-pecl-apcu',
            'php-pecl-imagick',
            'php-pecl-msgpack',
            'php-pecl-ssh2',
            'php-pecl-zendopcache',
        ])

        try:
            self._requireDeb([
                "php.*-mbstring",
                "php.*-opcache",
                "php.*-zip",
            ])
            self._requireYum([
                'php-pecl-sqlite',
            ])
        except:
            pass

        self._requireEmerge(['dev-lang/php'])
        self._requirePacman(['php'])

        self._requireApkCommunity()
        self._requireApk([
            'php7',
            'php7-xml',
            'php7-xmlreader',
            'php7-xmlrpc',
            'php7-zip',
            'php7-zlib',
            'php7-phar',
            'php7-posix',
            'php7-session',
            'php7-soap',
            'php7-sockets',
            'php7-json',
            'php7-mbstring',
            'php7-mcrypt',
            'php7-opcache',
            'php7-openssl',
            'php7-pdo',
            'php7-bz2',
            'php7-ctype',
            'php7-curl',
            'php7-dom',
            'php7-enchant',
            'php7-exif',
            'php7-gd',
            'php7-gettext',
            'php7-gmp',
            'php7-iconv',
            'php7-imap',
            'php7-intl',
            'php7-bcmath',
            'php7-fpm',
            'php7-pear',
            'php7-apcu',
        ])

    def tuneDefaults(self):
        return {
            'minMemory': '8M',
            'socketType': 'none',
            'scalable': False,
        }
