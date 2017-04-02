
from ..buildtool import BuildTool
from ..runenvtool import RunEnvTool

class dockerTool( BuildTool, RunEnvTool ):
    """Docker - Build, Ship, and Run Any App, Anywhere.
    
Home: https://www.docker.com/

Experimental support.

Docker CE support is added for CentOS, Fedora, Debian and Ubuntu.
For other systems, "docker" or "docker-engine" packages is tried to be installed.

Docker EE or other installation methods are out of scope for now.
"""
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Dockerfile' ]
        )
    
    def getDeps( self ):
        return ['curl']

    def getOrder( self ):
        return 10
    
    def envDeps(self, env):
        return ['dockerBin', 'dockerVer', 'dockerRepos']
    
    def _installTool( self, env ):
        repo = env.get('dockerRepos', 'https://download.docker.com')
        
        if self._isCentOS():
            self._addYumRepo('docker', repo + '/linux/centos/docker-ce.repo')
            
        elif self._isFedora():
            self._addYumRepo('docker', repo + '/linux/fedora/docker-ce.repo')
            
        elif self._isDebian():
            gpg = self._callExternal([ env['curlBin'], '-fsSL', repo+'/linux/debian/gpg'])
            self._addAptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/debian $codename$ stable'.format(repo),
                gpg
            )

        elif self._isUbuntu():
            gpg = self._callExternal([ env['curlBin'], '-fsSL', repo+'/linux/ubuntu/gpg'])
            self._addAptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/ubuntu $codename$ stable'.format(repo),
                gpg
            )
            
        else:
            self._requireYumEPEL()
            self._requirePackages(['docker'])
            self._requirePackages(['docker-engine'])
            self._requireEmerge(['app-emulation/docker'])
            self._requirePacman(['docker'])
            
            self._trySudoCall(
                ['/bin/systemctl', 'start', 'docker'],
                errmsg = 'WARNING: you may need to start Docker manually !'
            )
            
            return
            
        ver = env.get('dockerVer', None)
        
        if ver:
            self._requirePackages(['docker-ce-'+ver])
        else :
            self._requirePackages(['docker-ce'])
            
        self._trySudoCall(
            ['/bin/systemctl', 'start', 'docker'],
            errmsg = 'WARNING: you may need to start Docker manually !'
        )

    def onBuild( self, config ):
        cmd = [ config['env']['dockerBin'], 'build', '.' ]

        if self._haveGroup('docker'):
            self._callExternal( cmd )
        else:
            self._callExternal( ['sudo'] + cmd )

