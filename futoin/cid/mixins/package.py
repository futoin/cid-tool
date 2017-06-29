
from __future__ import print_function, absolute_import

import os
import subprocess
import platform
import glob

try:
    import urllib.request as urllib
except ImportError:
    import urllib2 as urllib


class PackageMixIn(object):
    SYSTEM_VER = 'system'

    def _isCentOS(self):
        return platform.linux_distribution()[0].startswith('CentOS')

    def _isFedora(self):
        return os.path.exists('/etc/fedora-release')

    def _isGentoo(self):
        return os.path.exists('/etc/gentoo-release')

    def _isArchLinux(self):
        # There are cases when platform.linux_distribution() is empty on Arch
        return (os.path.exists('/etc/arch-release') or
                platform.linux_distribution()[0].startswith('arch'))

    def _isDebian(self):
        return platform.linux_distribution()[0].startswith('debian')

    def _isUbuntu(self):
        return platform.linux_distribution()[0].startswith('Ubuntu')

    def _isOracleLinux(self):
        return platform.linux_distribution()[0].startswith('Oracle Linux')

    def _isRHEL(self):
        return platform.linux_distribution()[0].startswith('Red Hat Enterprise Linux')

    def _isOpenSUSE(self):
        return platform.linux_distribution()[0].startswith('openSUSE')

    def _isSLES(self):
        return platform.linux_distribution()[0].startswith('SUSE Linux Enterprise')

    def _isAlpineLinux(self):
        return os.path.exists('/etc/alpine-release')

    def _isLinux(self):
        return platform.system() == 'Linux'

    def _isMacOS(self):
        return platform.system() == 'Darwin'

    def _isAMD64(self):
        return platform.machine() == 'x86_64'

    def _osCodeName(self):
        codename = subprocess.check_output(['lsb_release', '-cs'])

        try:
            codename = str(codename, 'utf8')
        except:
            pass

        return codename.strip()

    def _requireDeb(self, packages):
        apt_get = self._which('apt-get')

        if apt_get:
            if not isinstance(packages, list):
                packages = [packages]

            os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
            self._trySudoCall(
                [apt_get, 'install', '-y',
                 '--no-install-recommends',
                 '-o', 'Dpkg::Options::=--force-confdef',
                 '-o', 'Dpkg::Options::=--force-confold'] + packages,
                errmsg='you may need to install the packages manually !'
            )

    def _requireYum(self, packages):
        yum = self._which('dnf')

        if not yum:
            yum = self._which('yum')

        if yum:
            if not isinstance(packages, list):
                packages = [packages]

            self._trySudoCall(
                [yum, 'install', '-y'] + packages,
                errmsg='you may need to install the packages manually !'
            )

    def _requireZypper(self, packages):
        zypper = self._which('zypper')

        if zypper:
            if not isinstance(packages, list):
                packages = [packages]

            self._trySudoCall(
                [zypper, 'install', '-y'] + packages,
                errmsg='you may need to install the packages manually !'
            )

    def _requireRpm(self, packages):
        self._requireYum(packages)
        self._requireZypper(packages)

    def _requirePackages(self, packages):
        self._requireDeb(packages)
        self._requireRpm(packages)

    def _requireEmerge(self, packages):
        emerge = self._which('emerge')

        if emerge:
            if not isinstance(packages, list):
                packages = [packages]

            self._trySudoCall(
                [emerge] + packages,
                errmsg='you may need to install the build deps manually !'
            )

    def _requireEmergeDepsOnly(self, packages):
        if not isinstance(packages, list):
            packages = [packages]

        self._requireEmerge(['--onlydeps'] + packages)

    def _requirePacman(self, packages):
        pacman = self._which('pacman')

        if pacman:
            if not isinstance(packages, list):
                packages = [packages]

            self._trySudoCall(
                [pacman, '-S', '--noconfirm', '--needed'] + packages,
                errmsg='you may need to install the build deps manually !'
            )

    def _requireApk(self, packages):
        if self._isAlpineLinux():
            if not isinstance(packages, list):
                packages = [packages]

            apk = '/sbin/apk'

            self._trySudoCall(
                [apk, 'add'] + packages,
                errmsg='you may need to install the build deps manually !'
            )

    def _addAptRepo(self, name, entry, gpg_key=None, codename_map=None, repo_base=None):
        self._requireDeb([
            'software-properties-common',
            'apt-transport-https',
            'ca-certificates',
            'lsb-release',
        ])
        apt_add_repository = self._which('apt-add-repository')

        if not apt_add_repository:
            return

        if gpg_key:
            try:
                gpg_key = gpg_key.encode(encoding='UTF-8')
            except:
                pass

            tmp_dir = self._tmpCacheDir(prefix='cidgpg')
            tf = os.path.join(tmp_dir, 'key.gpg')
            self._writeBinaryFile(tf, gpg_key)

            self._trySudoCall(
                ['apt-key', 'add', tf],
                errmsg='you may need to import the PGP key manually!'
            )

            os.remove(tf)

        codename = self._osCodeName()

        if codename_map:
            try:
                repo_info = urllib.urlopen(
                    '{0}/{1}'.format(repo_base, codename)).read()
            except:
                fallback_codename = codename_map.get(codename, codename)
                self._warn('Fallback to codename: {0}'.format(
                    fallback_codename))
                codename = fallback_codename

        entry = entry.replace('$codename$', codename)

        self._trySudoCall(
            [apt_add_repository, '--yes', entry],
            errmsg='you may need to add the repo manually!'
        )

        self._trySudoCall(
            ['apt-get', 'update'],
            errmsg='you may need to update APT cache manually!'
        )

    def _addRpmKey(self, gpg_key):
        if not gpg_key:
            return

        rpm = self._which('rpm')

        if not rpm:
            return

        tmp_dir = self._tmpCacheDir(prefix='cidgpg')
        tf = os.path.join(tmp_dir, 'key.gpg')
        self._writeBinaryFile(tf, gpg_key)

        self._trySudoCall(
            [rpm, '--import', tf],
            errmsg='you may need to import the PGP key manually!'
        )

        os.remove(tf)

    def _addYumRepo(self, name, url, gpg_key=None, releasevermax=None, repo_url=False):
        self._addRpmKey(gpg_key)

        dnf = self._which('dnf')
        yum = self._which('yum')

        if repo_url:
            tmp_dir = self._tmpCacheDir(prefix='cidrepo')
            repo_file = '{0}.repo'.format(name)
            repo_file = os.path.join(tmp_dir, repo_file)

            with open(repo_file, 'w') as f:
                f.write("\n".join([
                    '[nginx]',
                    'name={0} repo'.format(name),
                    'baseurl={0}'.format(url),
                    'gpgcheck=1',
                    'enabled=1',
                    ''
                ]))

            url = repo_file

        if dnf:
            self._requireYum(['dnf-plugins-core'])
            repo_file = None

            if releasevermax is not None:
                dump = self._callExternal(
                    [dnf, 'config-manager', '--dump'], verbose=False)
                for l in dump.split("\n"):
                    l = l.split(' = ')

                    if l[0] == 'releasever':
                        if int(l[1]) > releasevermax:
                            repo_info = urllib.urlopen(url).read()

                            try:
                                repo_info = str(repo_info, 'utf8')
                            except:
                                pass

                            repo_info = repo_info.replace(
                                '$releasever', str(releasevermax))

                            tmp_dir = self._tmpCacheDir(prefix='cidrepo')
                            repo_file = url.split('/')[-1]
                            repo_file = os.path.join(tmp_dir, repo_file)

                            with open(repo_file, 'w') as f:
                                f.write(repo_info)

                            url = repo_file
                        break

            self._trySudoCall(
                [dnf, 'config-manager', '--add-repo', url],
                errmsg='you may need to add the repo manually!'
            )

            if repo_file:
                os.remove(repo_file)

        elif yum:
            self._requireYum(['yum-utils'])
            yumcfgmgr = self._which('yum-config-manager')
            self._trySudoCall(
                [yumcfgmgr, '--add-repo', url],
                errmsg='you may need to add the repo manually!'
            )

    def _addZypperRepo(self, name, url, gpg_key=None, yum=False):
        self._addRpmKey(gpg_key)

        zypper = self._which('zypper')

        if zypper:
            if yum:
                cmd = [zypper, 'addrepo', '-t', 'YUM', url, name]
            else:
                cmd = [zypper, 'addrepo', url, name]

            self._trySudoCall(
                cmd,
                errmsg='you may need to add the repo manually!'
            )

    def _addApkRepo(self, url, tag=None):
        if not self._isAlpineLinux():
            return

        apk = '/sbin/apk'
        repo_file = '/etc/apk/repositories'

        # version
        releasever = self._readTextFile('/etc/alpine-release')
        releasever = releasever.strip().split('.')
        releasever = '.'.join(releasever[:2])
        repoline = url.replace('$releasever', releasever)

        # tag
        if tag:
            repoline = '@{0} {1}'.format(tag, repoline)

        repos = self._readTextFile(repo_file).split("\n")
        repos = [r.strip() for r in repos]

        if repoline not in repos:
            self._trySudoCall(
                ['/usr/bin/tee', '-a', repo_file],
                errmsg='you may need to add the repo manually!',
                input=repoline
            )
            self._trySudoCall(
                [apk, 'update'],
                errmsg='you may need to update manually!'
            )

    def _requireApkCommunity(self):
        self._addApkRepo(
            'http://dl-cdn.alpinelinux.org/alpine/v$releasever/community')

    def _requireYumEPEL(self):
        if self._isOracleLinux() or self._isRHEL():
            ver = platform.linux_distribution()[1].split('.')[0]
            self._requireYum(
                ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-{0}.noarch.rpm'.format(ver)])
        else:
            self._requireYum(['epel-release'])

    def _yumEnable(self, repo):
        self._requireYum(['yum-utils'])

        yumcfgmgr = self._which('yum-config-manager')

        self._trySudoCall(
            [yumcfgmgr, '--enable', repo],
            errmsg='You may need to enable the repo manually'
        )

    def _isSCLSupported(self):
        "Check if Software Collections are supported"
        return (
            self._isCentOS() or
            self._isRHEL() or
            self._isOracleLinux()
        )

    def _requireSCL(self):
        if self._isRHEL():
            self._yumEnable('rhel-server-rhscl-7-rpms')
        elif self._isCentOS():
            self._requireYum('centos-release-scl-rh')
        elif self._isOracleLinux():
            self._addYumRepo('public-yum-o17',
                             'http://yum.oracle.com/public-yum-ol7.repo')
            self._yumEnable('ol7_software_collections')
            self._yumEnable('ol7_latest')
            self._yumEnable('ol7_optional_latest')

        self._requireYum('scl-utils')

    def _requireBrewTap(self, tap):
        if not self._isMacOS():
            return

        brew = self._which('brew')
        brew_sudo = os.environ.get('brewSudo', '').split()
        self._callExternal(brew_sudo + [brew, 'tap', tap])

    def _requireBrewUnlink(self, formula=None, search=None):
        if not self._isMacOS():
            return

        brew = self._which('brew')
        brew_sudo = os.environ.get('brewSudo', '').split()

        flist = []

        if formula is not None:
            if isinstance(formula, list):
                flist += formula
            else:
                flist.append(formula)

        if search:
            flist += self._callExternal([brew, 'search', search]).split()

        for f in flist:
            try:
                self._callExternal(brew_sudo + [brew, 'unlink', f])
            except subprocess.CalledProcessError:
                self._warn('You may need to unlink the formula manually!')

    def _requireBrew(self, packages, cask=False):
        if not self._isMacOS():
            return

        if not isinstance(packages, list):
            packages = [packages]

        brew = self._which('brew')
        brew_sudo = os.environ.get('brewSudo', '').split()

        for package in packages:
            try:
                if cask:
                    self._callInteractive(
                        brew_sudo + [brew, 'cask', 'install', package], False)
                elif brew == '/usr/local/bin/brew':
                    self._callExternal(
                        brew_sudo + [brew, 'install', '--force-bottle', package])
                else:
                    self._callExternal(
                        brew_sudo + [brew, 'install', package])
            except subprocess.CalledProcessError:
                self._warn('You may need to enable the package manually')

    def _requireDmg(self, packages):
        if not self._isMacOS():
            return

        if not isinstance(packages, list):
            packages = [packages]

        curl = self._which('curl')
        hdiutil = self._which('hdiutil')
        installer = self._which('installer')
        volumes_dir = '/Volumes'

        for package in packages:
            base_name = package.split('/')[-1]
            local_name = os.path.join(os.environ['HOME'])

            # TODO: change to use env timeouts
            self._callExternal([
                curl,
                '-fsSL',
                '--connect-timeout', '10',
                '--max-time', '300',
                '-o', base_name,
                package
            ])

            volumes = set(os.listdir(volumes_dir))
            self._trySudoCall([hdiutil, 'attach', local_name])
            volume = (set(os.listdir(volumes_dir)) - volumes)[0]

            pkg = glob.glob(os.path.join(volumes_dir, volume, '*.pkg'))
            self._trySudoCall([installer, '-package', pkg, '-target', '/'])

            self._trySudoCall([hdiutil, 'dettach', local_name])

    def _requireBuildEssential(self):
        self._requireDeb([
            'build-essential',
        ])
        self._requireRpm([
            'binutils',
            'gcc',
            'gcc-c++',
            'glibc-devel',
            'libtool',
            'make',
            'patch'
        ])

        self._requireYum('redhat-rpm-config')

        self._requireApk([
            'build-base',
            'linux-headers',
        ])

    def _startService(self, name):
        openrc = '/sbin/rc-service'
        systemctl = '/bin/systemctl'

        if os.path.exists(systemctl):
            self._trySudoCall(
                [systemctl, 'start', name],
                errmsg='you may need to start the service manually')
        elif os.path.exists(openrc):
            self._trySudoCall(
                [openrc, name, 'start'],
                errmsg='you may need to start the service manually')

    def _requireBuildDep(self, env, dep):
        if not isinstance(dep, list):
            dep = [dep]

        self._requireBuildEssential()

        for d in dep:
            getattr(self, '_PackageMixIn__requireBuildDep_' +
                    d.replace('-', ''))(env)

    def __requireBuildDep_ruby(self, env):
        if env['rubyVer'] == self.SYSTEM_VER:
            self._requireDeb(['ruby-dev'])
            self._requireRpm(['ruby-devel'])
            self._requireApk(['ruby-dev'])
        elif self._isSCLSupported():
            devver = env['rubyVer'].replace('.', '')

            if devver == '19':
                sclname = 'ruby193-ruby-devel'
            elif devver == '20':
                sclname = 'ruby200-ruby-devel'
            else:
                sclname = 'rh-ruby{0}-ruby-devel'.format(devver)

            self._requireRpm(sclname)

    def __requireBuildDep_python(self, env):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._requireDeb(['python3-dev'])
            self._requireZypper(['python3-devel'])
            self._requireYum(['python3-devel'])
            self._requireYum(['python34-devel'])
            self._requireApk(['python3-dev'])
        else:
            self._requireDeb(['python-dev'])
            self._requireRpm(['python-devel'])
            self._requireApk(['python2-dev'])

    def __requireBuildDep_ssl(self, env):
        self._requireDeb('libssl-dev')
        self._requireRpm('openssl-devel')
        self._requireApk('ressl-dev')
        self._requirePacman('openssl')
        self._requireBrew('openssl')

    def __requireBuildDep_mysqlclient(self, env):
        self._requireDeb('libmysqlclient-dev')
        self._requireDeb('default-libmysqlclient-dev')

        if self._isOracleLinux():
            self._requireYum(['mariadb-devel', 'mariadb-libs'])
        else:
            self._requireYum('mysql-devel')

        self._requireZypper('libmysqlclient-devel')
        self._requireApk('mariadb-dev')
        self._requireBrew('mysql')

    def __requireBuildDep_postgresql(self, env):
        self._requireDeb('libpq-dev')
        self._requireRpm(['postgresql-devel', 'postgresql-libs'])
        self._requirePacman('postgresql')
        self._requireApk('postgresql-dev')
        self._requireBrew('postgresql')

    def __requireBuildDep_imagemagick(self, env):
        self._requireDeb('libmagick-dev')
        self._requireRpm(['imagemagick', 'imagemagick-devel'])
        self._requirePacman('imagemagick')
        self._requireApk('imagemagick-dev')
        self._requireBrew('imagemagick')

    def __requireBuildDep_tzdata(self, env):
        self._requireDeb('tzdata')
        self._requireRpm('tzdata')
        self._requirePacman('tzdata')
        self._requireApk('tzdata')

    def __requireBuildDep_libxml2(self, env):
        self._requireDeb('libxml2-dev')
        self._requireRpm('libxml2-devel')
        self._requirePacman('libxml2')
        self._requireApk('libxml2')
        self._requireBrew('libxml2')
