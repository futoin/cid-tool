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

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class phpTool(BashToolMixIn, CurlToolMixIn, RuntimeTool):
    """PHP is a popular general-purpose scripting language that is especially suited to web development.

Home: http://php.net/


By default the latest available PHP binary is used for the following OSes:
* Debian & Ubuntu - uses Sury (https://deb.sury.org/) builds 5.6 & 7.x.
* CentOS, RHEL & Oracle Linux - uses SCL 5.6 & 7.x.
* macos uses Homebrew builds 5.6 & 7.x.

You can forbid source builds by setting phpBinOnly to non-empty string.

However, if phpVer is set then we use php-build which make consume a lot of time and
resources due to lack of trusted binary builds.

You can control installed extensions by setting space separated environment:
* phpExtRequire - required extensions to be installed or fail
* phpExtTry - nice to have extensions

The same can be done by setting project-specific .toolTune options as array:
* extRequire = []
* extTry = []
"""
    __slots__ = ()

    def getDeps(self):
        deps = BashToolMixIn.getDeps(self) + CurlToolMixIn.getDeps(self)
        # TODO: need to disable for binary only installs
        deps += ['phpbuild']
        return deps

    def _installTool(self, env):
        ospath = self._ospath
        environ = self._environ
        php_ver = env['phpVer']

        if not env['phpSourceBuild']:
            self._installBinaries(env)
            return

        php_dir = env['phpDir']

        try:
            self._os.makedirs(php_dir)
        except:
            pass

        self._buildDeps(env)

        old_tmpdir = environ.get('TMPDIR', '/tmp')
        environ['TMPDIR'] = ospath.join(php_dir, '..')
        self._executil.callExternal(
            [env['phpbuildBin'], env['phpSourceVer'], env['phpDir']])
        environ['TMPDIR'] = old_tmpdir

    def _installBinaries(self, env):
        detect = self._detect
        phputil = self._phputil
        install = self._install

        ver = env['phpVer']
        php_pkg = phputil.basePackage(ver)

        if detect.isDebian():
            repo = env.get('phpSuryRepo', 'https://packages.sury.org/php')
            gpg = self._callCurl(env, [repo + '/apt.gpg'], binary_output=True)

            install.aptRepo(
                'sury', "deb {0} $codename$ main".format(repo), gpg)
            install.deb(php_pkg)

        elif detect.isUbuntu():
            install.aptRepo('sury', 'ppa:ondrej/php', None)
            install.deb(php_pkg)

        elif detect.isSCLSupported():
            if phputil.isIUSVer(ver):
                install.yumIUS()
                install.yum(php_pkg + '-cli')
            else:
                install.yumSCL()
                install.yum(php_pkg)

        elif detect.isMacOS():
            install.brew(php_pkg)

        elif detect.isAlpineLinux():
            install.apkCommunity()
            install.apk(php_pkg)

        elif detect.isSLES():
            self._install.SUSEConnectVerArch('sle-module-web-scripting')
            install.zypper(php_pkg)

        else:
            install.zypper(php_pkg)
            install.yum('{0}-cli'.format(php_pkg))
            install.emerge('dev-lang/php')
            install.pacman(php_pkg)

        env['phpJustInstalled'] = True

    def _updateTool(self, env):
        pass

    def uninstallTool(self, env):
        if env['phpVer'] == self.SYSTEM_VER or env['phpBinOnly']:
            return super(phpTool, self).uninstallTool(env)

        php_dir = env['phpDir']
        self._pathutil.rmTree(php_dir)
        self._have_tool = False

    def envNames(self):
        return ['phpDir', 'phpBin', 'phpVer', 'phpfpmVer', 'phpBinOnly', 'phpSuryRepo',
                'phpExtRequire', 'phpExtTry', 'phpForceBuild', 'phpSourceVer']

    def initEnv(self, env):
        ospath = self._ospath
        os = self._os
        detect = self._detect
        phputil = self._phputil
        environ = self._environ

        # ---
        if 'phpfpmVer' in env:
            php_ver = env.setdefault('phpVer', env['phpfpmVer'])

        # ---
        phpForceBuild = env.setdefault('phpForceBuild', False)
        phpBinOnly = env.setdefault('phpBinOnly', not phpForceBuild)
        env['phpSourceBuild'] = False

        if phpBinOnly and phpForceBuild:
            self._warn('"phpBinOnly" and "phpForceBuild" do not make sense'
                       ' when set together!')

        php_required_ext = env.get('phpExtRequire', '')
        php_try_ext = env.get('phpExtTry', '')
        environ['phpExtRequire'] = php_required_ext
        environ['phpExtTry'] = php_try_ext
        php_required_ext = php_required_ext.split()
        php_try_ext = php_try_ext.split()

        # ---
        php_binaries = phputil.binaryVersions()

        if php_binaries:
            php_latest = php_binaries[-1]
            php_ver = env.setdefault('phpVer', php_latest)
            foundBinary = True

            if php_ver.split('.')[0] == '5' and php_ver != '5.6':
                php_ver = '5.6'
                self._warn('Forcing PHP 5.6 for PHP 5.x requirement')
            elif php_ver == '7' and php_latest.split('.')[0] == '7':
                php_ver = php_latest
            elif php_ver.split('.') > php_latest.split('.'):
                foundBinary = False
                self._warn(
                    'Binary builds are supported only for: {0}'.format(', '.join(php_binaries)))

            env['phpVer'] = php_ver
        else:
            foundBinary = False
            php_ver = env.setdefault('phpVer', self.SYSTEM_VER)

        # ---
        if php_ver == self.SYSTEM_VER:
            super(phpTool, self).initEnv(env)
        elif foundBinary and not phpForceBuild:
            if detect.isDebian() or detect.isUbuntu():
                bin_name = 'php' + php_ver
                bin_src = ospath.join('/usr/bin', bin_name)
                self._have_tool = phputil.createBinDir(env, bin_src)

            elif detect.isSCLSupported():
                if phputil.isIUSVer(php_ver):
                    # IUS allows only one version installed as default
                    super(phpTool, self).initEnv(env)
                else:
                    try:
                        ver = php_ver.replace('.', '')
                        sclname = 'rh-php{0}'.format(ver)
                        env_to_set = self._executil.callExternal(
                            ['scl', 'enable', sclname, 'env'], verbose=False)
                        self._pathutil.updateEnvFromOutput(env_to_set)
                        super(phpTool, self).initEnv(env)

                        if self._have_tool:
                            self._have_tool = env['phpBin'].startswith('/opt')
                    except self._ext.subprocess.CalledProcessError:
                        return
                    except OSError:
                        return

            elif detect.isArchLinux():
                if phputil.isArchLatest(php_ver):
                    bin_name = 'php'
                else:
                    bin_name = 'php' + php_ver.replace('.', '')

                bin_src = ospath.join('/usr/bin', bin_name)
                self._have_tool = phputil.createBinDir(env, bin_src)

            elif detect.isAlpineLinux():
                if phputil.isAlpineSplit():
                    bin_name = 'php' + php_ver[0]
                else:
                    bin_name = 'php'

                bin_src = ospath.join('/usr/bin', bin_name)
                self._have_tool = phputil.createBinDir(env, bin_src)

            elif detect.isMacOS():
                brew_prefix = env['brewDir']
                formula = phputil.basePackage(php_ver)
                php_dir = ospath.join(brew_prefix, 'opt', formula, 'bin')

                if ospath.exists(php_dir):
                    self._pathutil.addBinPath(php_dir, True)
                    super(phpTool, self).initEnv(env)

        elif not phpBinOnly:
            def_dir = ospath.join(
                env['phpbuildDir'], 'share', 'php-build', 'definitions')

            if not ospath.exists(def_dir):
                return

            php_ver = env.setdefault('phpSourceVer', php_ver)
            defs = os.listdir(def_dir)
            defs = self._ext.fnmatch.filter(defs, php_ver + '*')

            if not defs:
                self._errorExit('PHP version "{0}" not found'.format(php_ver))

            php_ver = self._versionutil.latest(defs)

            env['phpSourceVer'] = php_ver
            env['phpForceBuild'] = True
            env['phpSourceBuild'] = True

            php_dir = ospath.join(os.environ['HOME'], '.php', php_ver)
            php_dir = env.setdefault('phpDir', php_dir)
            php_bin_dir = ospath.join(php_dir, 'bin')
            php_bin = ospath.join(php_bin_dir, 'php')

            if ospath.exists(php_bin):
                self._have_tool = True
                self._pathutil.addBinPath(php_bin_dir, True)
                env.setdefault('phpBin', php_bin)

        # ---
        if self._have_tool:
            if env.get('phpJustInstalled', False):
                self._phputil.installExtensions(env, [
                    'apcu',
                    'curl',
                ], True)

            phputil.installExtensions(env, php_required_ext, False)
            phputil.installExtensions(env, php_try_ext, True)

    def loadConfig(self, config):
        env = config['env']
        phputil = self._phputil

        php_required_ext = self._getTune(config, 'extRequire', [])
        php_try_ext = self._getTune(config, 'extTry', [])

        phputil.installExtensions(env, php_required_ext, False)
        phputil.installExtensions(env, php_try_ext, True)

    def _buildDeps(self, env):
        ospath = self._ospath
        os = self._os
        environ = self._environ

        if self._detect.isSLES():
            self._errorExit(
                'PHP source builds are not supported for SLES yet!')
            return

        self._builddep.require(env, [
            'ssl',
            'mysqlclient',
            'postgresql',
        ])
        # APT
        # ---
        self._install.deb([
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
        # ---
        self._install.yumEPEL()

        self._install.rpm([
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

        self._install.yum('bzip2-devel')
        self._install.zypper('libbz2-devel')

        self._install.emergeDepsOnly(['dev-lang/php'])
        self._install.pacman([
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

        # ---
        systemctl = self._pathutil.which('systemctl')

        if systemctl:
            self._install.deb(['libsystemd-dev'])
            self._install.rpm(['systemd-devel'])
            with_systemd = ' --with-fpm-systemd'
        else:
            with_systemd = ' --without-fpm-systemd'

        multiarch = None
        dpkgarch = self._pathutil.which('dpkg-architecture')

        if dpkgarch:
            multiarch = self._executil.callExternal(
                [dpkgarch, '-qDEB_HOST_MULTIARCH']).strip()

        if multiarch:
            if ospath.exists(ospath.join('/usr/include', multiarch, 'curl')):
                curl_dir = ospath.join(env['phpDir'], '..', 'curl')

                try:
                    os.mkdir(curl_dir)
                    os.symlink(ospath.join('/usr/include', multiarch),
                               ospath.join(curl_dir, 'include'))
                    os.symlink(ospath.join('/usr/lib', multiarch),
                               ospath.join(curl_dir, 'lib'))
                except Exception as e:
                    # print(e)
                    pass
            else:
                curl_dir = '/usr/include'

            with_libdir = ' --with-libdir={0} --with-curl={1}'.format(
                ospath.join('lib', multiarch),
                curl_dir,
            )
        else:
            with_libdir = ''
        # ---
        from ..details.resourcealgo import ResourceAlgo
        cpu_count = ResourceAlgo().cpuLimit({})

        environ['PHP_BUILD_EXTRA_MAKE_ARGUMENTS'] = '-j{0}'.format(
            cpu_count)

        environ['PHP_BUILD_CONFIGURE_OPTS'] = ' \
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

    def tuneDefaults(self, env):
        return {
            'minMemory': '8M',
            'socketType': 'none',
            'scalable': False,
            'reloadable': False,
            'multiCore': False,
        }
