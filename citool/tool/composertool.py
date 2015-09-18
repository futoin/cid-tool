
from citool.subtool import SubTool

class composerTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'composer.json' )
    
    def getDeps( self ) :
        return [ 'php' ]
