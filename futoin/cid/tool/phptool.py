
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
    __slots__ = ()

    def getDeps(self):
        return (
            ['phpbuild'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        ospath = self._ospath
        environ = self._environ
        php_ver = env['phpVer']

        if php_ver == self.SYSTEM_VER:
            self._systemDeps()
            return

        if env['phpBinOnly']:
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
            [env['phpbuildBin'], env['phpSrcVer'], env['phpDir']])
        environ['TMPDIR'] = old_tmpdir

    def _installBinaries(self, env):
        detect = self._detect

        ver = env['phpVer']

        if detect.isDebian():
            repo = env.get('phpSuryRepo', 'https://packages.sury.org/php')
            gpg = self._callCurl(env, [repo + '/apt.gpg'], binary_output=True)

            self._install.aptRepo(
                'sury', "deb {0} $codename$ main".format(repo), gpg)
            self._install.deb('php' + ver)

        elif detect.isUbuntu():
            self._install.aptRepo('sury', 'ppa:ondrej/php', None)
            self._install.deb('php' + ver)

        elif detect.isSCLSupported():
            if self._isPHPSCL(env):
                ver = ver.replace('.', '')

                self._install.yumSCL()

                self._install.yum([
                    'rh-php{0}'.format(ver),
                    'rh-php{0}-php-devel'.format(ver),
                ])
            else:
                self._errorExit('Only SCL packages are supported so far')

        elif detect.isMacOS():
            self._install.brewTap('homebrew/homebrew-php')
            ver = ver.replace('.', '')
            base_formula = 'homebrew/php/php{0}'.format(ver)

            self._install.brewUnlink(search='/homebrew\/php\/php[0-9]{2}$/')
            self._install.brew(base_formula)

            formulas = [
                'apcu',
                'opcache',
            ]

            self._install.brew(['{0}-{1}'.format(base_formula, f)
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
        self._pathutil.rmTree(php_dir)
        self._have_tool = False

    def envNames(self):
        return ['phpDir', 'phpBin', 'phpVer', 'phpfpmVer', 'phpBinOnly', 'phpSuryRepo']

    def initEnv(self, env):
        ospath = self._ospath
        os = self._os
        detect = self._detect

        #---
        # TODO: rewrite similar to ruby, and add dynamic detection
        if detect.isDebian() or detect.isUbuntu():
            php_latest = '7.1'
        elif detect.isSCLSupported():
            php_latest = '7.0'
        elif detect.isAlpineLinux():
            php_latest = '7.0'
        elif detect.isMacOS():
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
            elif detect.isMacOS():
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
            if detect.isDebian() or detect.isUbuntu():
                bin_name = 'php' + php_ver
                super(phpTool, self).initEnv(env, bin_name)

            elif detect.isSCLSupported():
                if self._isPHPSCL(env):
                    ver = env['phpVer'].replace('.', '')
                    try:
                        env_to_set = self._callBash(
                            env, 'scl enable rh-php{0} env'.format(ver), verbose=False)
                    except self._ext.subprocess.CalledProcessError:
                        return

                    self._pathutil.updateEnvFromOutput(env_to_set)
                    super(phpTool, self).initEnv(env)
                else:
                    pass

            elif detect.isAlpineLinux():
                bin_name = 'php' + php_ver[0]
                super(phpTool, self).initEnv(env, bin_name)

            elif detect.isMacOS():
                brew_prefix = env['brewDir']
                formula = 'php' + php_ver.replace('.', '')
                php_dir = ospath.join(brew_prefix, 'opt', formula, 'bin')

                if ospath.exists(php_dir):
                    self._pathutil.addBinPath(php_dir, True)
                    super(phpTool, self).initEnv(env)

            return
        else:
            def_dir = ospath.join(
                env['phpbuildDir'], 'share', 'php-build', 'definitions')

            if not ospath.exists(def_dir):
                return

            defs = os.listdir(def_dir)
            defs = self._ext.fnmatch.filter(defs, php_ver + '*')

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

        php_dir = ospath.join(os.environ['HOME'], '.php', php_ver)
        php_dir = env.setdefault('phpDir', php_dir)
        php_bin_dir = ospath.join(php_dir, 'bin')
        php_bin = ospath.join(php_bin_dir, 'php')

        if ospath.exists(php_bin):
            self._have_tool = True
            self._pathutil.addBinPath(php_bin_dir, True)
            env.setdefault('phpBin', php_bin)

    def _buildDeps(self, env):
        ospath = self._ospath
        os = self._os
        environ = self._environ

        self._builddep.require(env, [
            'ssl',
            'mysqlclient',
            'postgresql',
        ])
        # APT
        #---
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
        #---
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

        #---
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
        #---
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

    def _systemDeps(self):
        self._install.deb([
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
        self._install.zypper([
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
        self._install.yum([
            'php-cli',
            'php-fpm',
            'php-pecl-apcu',
            'php-pecl-imagick',
            'php-pecl-msgpack',
            'php-pecl-ssh2',
            'php-pecl-zendopcache',
        ])

        try:
            self._install.deb([
                "php.*-mbstring",
                "php.*-opcache",
                "php.*-zip",
            ])
            self._install.yum([
                'php-pecl-sqlite',
            ])
        except:
            pass

        self._install.emerge(['dev-lang/php'])
        self._install.pacman(['php'])

        self._install.apkCommunity()
        self._install.apk([
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
