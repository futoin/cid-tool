
from citool.subtool import SubTool
import os

class sshTool( SubTool ):
    def getType( self ):
        return self.TYPE_RMS
    
    def _installTool( self, env ):
        self.require_deb(['openssh-client'])
        self.require_rpm(['openssh'])
    
    