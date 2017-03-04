
from ..runenvtool import RunEnvTool

class gpgTool( RunEnvTool ):
    def _envNames( self ) :
        return ['gpgBin', 'gpgKeyServer']
   
    def _installTool( self, env ):
        self._requirePackages(['gnupg', 'gnupg2'])
    
    def initEnv( self, env ):
        super(gpgTool, self).initEnv( env )
        env.setdefault('gpgKeyServer', 'hkp://keyserver.ubuntu.com:80')
        