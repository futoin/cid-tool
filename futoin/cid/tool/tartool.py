
from ..runenvtool import RunEnvTool

class tarTool( RunEnvTool ):
    def _installTool( self, env ):
        self._requirePackages(['tar'])
    
