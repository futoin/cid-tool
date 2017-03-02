
from ..subtool import SubTool

class futoinTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNENV

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'futoin.json' )
    
    def getDeps( self ) :
        return [ 'python' ]

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( 'futoin.json', updater )
