
from citool.subtool import SubTool

class curlTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNENV
    
    def _installTool( self, env ):
        self.require_deb(['curl'])
