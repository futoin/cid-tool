
from citool.subtool import SubTool

class gruntTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Gruntfile.json', 'Gruntfile.coffee' ]
        )
    
    def getDeps( self ) :
        return [ 'nodejs' ]
