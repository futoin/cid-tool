
from citool.subtool import SubTool

class npmTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'package.json' )
    
    def getDeps( self ) :
        return [ 'nodejs' ]
