
from citool.subtool import SubTool

class artifactoryTool( SubTool ):
    def getType( self ):
        return self.TYPE_RMS

    def autoDetect( self, config ) :
        return self._autoDetectRMS( config )
