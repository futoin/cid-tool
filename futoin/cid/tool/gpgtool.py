
from ..runenvtool import RunEnvTool

class gpgTool( RunEnvTool ):
    def _envNames( self ) :
        return ['gpgBin', 'gpgKeyServer']
   
    def _installTool( self, env ):
        self._requirePackages(['gnupg', 'gnupg2'])
        self._requireEmerge(['app-crypt/gnupg'])
        self._requirePacman(['gnupg'])
    
    def initEnv( self, env ):
        super(gpgTool, self).initEnv( env )
        env.setdefault('gpgKeyServer', 'hkp://keyserver.ubuntu.com:80')
        