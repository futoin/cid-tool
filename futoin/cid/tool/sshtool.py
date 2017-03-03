
import os

from ..runenvtool import RunEnvTool

class sshTool( RunEnvTool ):
    def _installTool( self, env ):
        self.requireDeb(['openssh-client'])
        self.requireRpm(['openssh'])
    
    