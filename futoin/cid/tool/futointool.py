
from ..runenvtool import RunEnvTool

class futoinTool( RunEnvTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'futoin.json' )

    def initEnv( self, env ):
        self._have_tool = True

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( 'futoin.json', updater )
