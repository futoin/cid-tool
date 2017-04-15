
from __future__ import print_function, absolute_import

import os, tempfile, subprocess, platform, glob

try:
    import urllib.request as urllib
except ImportError:
    import urllib2 as urllib

class PackageMixIn( object ):
    def _isCentOS( self ):
        return platform.linux_distribution()[0].startswith('CentOS')
    
    def _isFedora( self ):
        return os.path.exists('/etc/fedora-release')
    
    def _isGentoo( self ):
        return os.path.exists('/etc/gentoo-release')

    def _isArchLinux( self ):
        # There are cases when platform.linux_distribution() is empty on Arch
        return (os.path.exists('/etc/arch-release') or
                platform.linux_distribution()[0].startswith('arch'))
    
    def _isDebian( self ):
        return platform.linux_distribution()[0].startswith('debian')

    def _isUbuntu( self ):
        return platform.linux_distribution()[0].startswith('Ubuntu')
    
    def _isOracleLinux( self ):
        return platform.linux_distribution()[0].startswith('Oracle Linux')

    def _isRHEL( self ):
        return platform.linux_distribution()[0].startswith('Red Hat Enterprise Linux')
    
    def isOpenSUSE( self ):
        return platform.linux_distribution()[0].startswith('openSUSE')

    def isSLES( self ):
        return platform.linux_distribution()[0].startswith('SUSE Linux Enterprise')
    
    def _isMacOS( self ):
        return platform.system() == 'Darwin'

    def _requireDeb(self, packages):
        apt_get = self._which('apt-get')
        
        if apt_get:
            if not isinstance(packages, list):
                packages = [packages]
            
            self._trySudoCall(
                [apt_get, 'install', '-y'] + packages,
                errmsg = 'you may need to install the packages manually !'
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
                errmsg = 'you may need to install the packages manually !'
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
            (fd, tf) = tempfile.mkstemp('cidgpg', text=True)
            try:
                os.write(fd, gpg_key.encode(encoding='UTF-8'))
            except:
                os.write(fd, gpg_key)
            os.close(fd)

            self._trySudoCall(
                ['apt-key', 'add', tf],
                errmsg = 'you may need to import the PGP key manually!'
            )
            
            os.remove(tf)
            
        codename = subprocess.check_output( ['lsb_release', '-cs'] )
        try: codename = str(codename, 'utf8')
        except: pass
        codename = codename.strip()
        
        if codename_map:
            try:
                repo_info = urllib.urlopen('{0}/{1}'.format(repo_base, codename)).read()
            except:
                fallback_codename = codename_map.get(codename, codename)
                self._warn('Fallback to codename: {0}'.format(fallback_codename))
                codename = fallback_codename

        entry = entry.replace('$codename$', codename)
            
        self._trySudoCall(
            [apt_add_repository, '--yes', entry],
            errmsg = 'you may need to add the repo manually!'
        )
        
        self._trySudoCall(
            ['apt-get', 'update'],
            errmsg = 'you may need to update APT cache manually!'
        )
            
    def _addRpmKey(self, gpg_key):
        if not gpg_key:
            return
        
        rpm = self._which('rpm')
        
        if not rpm:
            return
            
        (fd, tf) = tempfile.mkstemp('cidgpg', text=True)
        os.write(fd, gpg_key.encode(encoding='UTF-8'))
        os.close(fd)
            
        self._trySudoCall(
            [rpm, '--import', tf],
            errmsg = 'you may need to import the PGP key manually!'
        )
        
        os.remove(tf)
            
    
    def _addYumRepo(self, name, url, gpg_key=None, releasevermax=None):
        self._addRpmKey(gpg_key)

        dnf = self._which('dnf')
        yum = self._which('yum')
        
        if dnf:
            self._requireYum(['dnf-plugins-core'])
            repo_file = None
            
            if releasevermax is not None:
                dump = self._callExternal([dnf, 'config-manager', '--dump'], verbose=False)
                for l in dump.split("\n"):
                    l = l.split(' = ')
                    
                    if l[0] == 'releasever':
                        if int(l[1]) > releasevermax:
                            repo_info = urllib.urlopen(url).read()
                            
                            try: repo_info = str(repo_info, 'utf8')
                            except: pass
                        
                            repo_info = repo_info.replace('$releasever', str(releasevermax))
                        
                            tmp_dir = tempfile.mkdtemp('cidrepo')
                            repo_file = url.split('/')[-1]
                            repo_file = os.path.join(tmp_dir, repo_file)
                            
                            with open(repo_file, 'w') as f:
                                f.write(repo_info)
                            
                            url = repo_file
                        break

            self._trySudoCall(
                [dnf, 'config-manager', '--add-repo', url],
                errmsg = 'you may need to add the repo manually!'
            )
            
            if repo_file:
                os.remove(repo_file)
            
            
        elif yum:
            self._requireYum(['yum-utils'])
            yumcfgmgr = self._which('yum-config-manager')
            self._trySudoCall(
                [yumcfgmgr, '--add-repo', url],
                errmsg = 'you may need to add the repo manually!'
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
                errmsg = 'you may need to add the repo manually!'
            )
            
    def _requireYumEPEL(self):
        if self._isOracleLinux() or self._isRHEL():
            ver = platform.linux_distribution()[1].split('.')[0]
            self._requireYum(['https://dl.fedoraproject.org/pub/epel/epel-release-latest-{0}.noarch.rpm'.format(ver)])
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
            self._addYumRepo('public-yum-o17', 'http://yum.oracle.com/public-yum-ol7.repo')
            self._yumEnable('ol7_software_collections')
            self._yumEnable('ol7_latest')
            self._yumEnable('ol7_optional_latest')

        self._requireYum('scl-utils')

    def _requireHomebrew(self, packages):
        if not self._isMacOS():
            return
        
        if not isinstance(packages, list):
            packages = [packages]
        
        brew = self._which('brew')
        
        if not brew:
            self._callExternal(['bash', '-c', '/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'])
            brew = self._which('brew')
            
        for package in packages:
            self._callExternal([brew, 'install', package])
            
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
            self._callExternal([curl, '-o', base_name, package])
            
            volumes = set(os.listdir(volumes_dir))
            self._trySudoCall([hdiutil, 'attach', local_name])
            volume = (set(os.listdir(volumes_dir)) - volumes)[0]
            
            pkg = glob.glob(os.path.join(volumes_dir, volume, '*.pkg'))
            self._trySudoCall([installer, '-package', pkg, '-target', '/'])
            
            self._trySudoCall([hdiutil, 'dettach', local_name])
