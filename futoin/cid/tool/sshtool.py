
import os

from ..runenvtool import RunEnvTool

class sshTool( RunEnvTool ):
    """Secure Shell client.
    
Home: https://www.openssh.com/
"""    
    def _installTool( self, env ):
        self._requireDeb(['openssh-client'])
        self._requireRpm(['openssh'])
        self._requireEmerge(['virtual/ssh'])
        self._requirePacman(['openssh'])
    
    