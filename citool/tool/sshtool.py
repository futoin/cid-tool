
from citool.subtool import SubTool
import os

class sshTool( SubTool ):
    def getType( self ):
        return self.TYPE_RMS
    
    def _installTool( self, env ):
        self.requireDeb(['openssh-client'])
        self.requireRpm(['openssh'])
    
    