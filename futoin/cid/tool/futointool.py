
from ..runenvtool import RunEnvTool

class futoinTool( RunEnvTool ):
    """futoin.json updater as defined in FTN16.
    
Home: https://github.com/futoin/specs/blob/master/draft/ftn16_cid_tool.md

Auto-detected based on futoin.json

futoin.json is the only file read by FutoIn CID itself.
"""
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, self._FUTOIN_JSON )

    def initEnv( self, env ):
        self._have_tool = True

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( self._FUTOIN_JSON, updater )
