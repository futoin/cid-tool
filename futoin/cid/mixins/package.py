
from __future__ import print_function, absolute_import

import os, tempfile, subprocess, platform

class PackageMixIn( object ):
    def _isCentOS( self ):
        return os.path.exists('/etc/centos-release')
    
    def _isFedora( self ):
        return os.path.exists('/etc/fedora-release')
    
    def _isGentoo( self ):
        return os.path.exists('/etc/gentoo-release')

    def _isArchLinux( self ):
        return os.path.exists('/etc/arch-release')
    
    def _isDebian( self ):
        return platform.linux_distribution()[0] == 'debian'

    def _isUbuntu( self ):
        return platform.linux_distribution()[0] == 'Ubuntu'
    
    def _requireDeb(self, packages):
        apt_get = self._which('apt-get')
        
        if apt_get:
            self._trySudoCall(
                [apt_get, 'install', '-y'] + packages,
                errmsg = 'WARNING: you may need to install build deps manually !'
            )

    def _requireYum(self, packages):
        yum = self._which('dnf')
        
        if not yum:
            yum = self._which('yum')
        
        if yum:
            self._trySudoCall(
                [yum, 'install', '-y'] + packages,
                errmsg = 'WARNING: you may need to install build deps manually !'
            )

    def _requireZypper(self, packages):        
        zypper = self._which('zypper')

        if zypper:
            self._trySudoCall(
                [zypper, 'install', '-y'] + packages,
                errmsg='WARNING: you may need to install build deps manually !'
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
            self._trySudoCall(
                [emerge] + packages,
                errmsg='WARNING: you may need to install build deps manually !'
            )

    def _requireEmergeDepsOnly(self, packages):
        self._requireEmerge(['--onlydeps'] + packages)
        
    def _requirePacman(self, packages):
        pacman = self._which('pacman')

        if pacman:
            self._trySudoCall(
                [pacman, '-S', '--noconfirm', '--needed'] + packages,
                errmsg='WARNING: you may need to install build deps manually !'
            )
        
    def _addAptRepo(self, name, entry, gpg_key):
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
            os.write(fd, gpg_key.encode(encoding='UTF-8'))
            os.close(fd)

            self._trySudoCall(
                ['apt-key', 'add', tf],
                errmsg = 'WARNING: you may need to import GPG key manually!'
            )
            
            os.remove(tf)
            
        codename = subprocess.check_output( ['lsb_release', '-cs'] )
        
        try:
            codename = str(codename, 'utf8')
        except:
            pass
        
        entry = entry.replace('$codename$', codename)
            
        self._trySudoCall(
            [apt_add_repository, '--yes', entry],
            errmsg = 'WARNING: you may need to add repo manually!'
        )
        
        self._trySudoCall(
            ['apt-get', 'update'],
            errmsg = 'WARNING: you may need to update cache APT manually!'
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
            errmsg = 'WARNING: you may need to import GPG key manually!'
        )
        
        os.remove(tf)
            
    
    def _addYumRepo(self, name, url, gpg_key=None):
        self._addRpmKey(gpg_key)

        dnf = self._which('dnf')
        yum = self._which('yum')
        
        if dnf:
            self._requireYum(['dnf-plugins-core'])
            self._trySudoCall(
                [dnf, 'config-manager', '--add-repo', url],
                errmsg = 'WARNING: you may need to import GPG key manually!'
            )
        elif yum:
            self._requireYum(['yum-utils'])
            yumcfgmgr = self._which('yum-config-manager')
            self._trySudoCall(
                [yumcfgmgr, '--add-repo', url],
                errmsg = 'WARNING: you may need to import GPG key manually!'
            )

    def _addZypperRepo(self, name, url, gpg_key=None):
        self._addRpmKey(gpg_key)
        
        zypper = self._which('zypper')
        
        if zypper:
            self._trySudoCall(
                [zypper, 'addrepo', url, name],
                errmsg = 'WARNING: you may need to zypper repo manually!'
            )
        
