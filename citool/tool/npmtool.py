
import json
from collections import OrderedDict

from citool.subtool import SubTool

class npmTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'package.json' )
    
    def getDeps( self ) :
        return [ 'node' ]
    
    def loadConfig( self, config ) :
        with open('package.json', 'r') as content_file:
            content = content_file.read()
            object_pairs_hook = lambda pairs: OrderedDict( pairs )
            content = json.loads( content, object_pairs_hook=object_pairs_hook )
        for f in ( 'name', 'version' ):
            if f in content and f not in config:
                config[f] = content[f]

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( 'package.json', updater )
    
    def onPrepare( self, config ):
        npmBin = config['env']['npmBin']
        self._callExternal( [ npmBin, 'install' ] )
        
    def onPackage( self, config ):
        npmBin = config['env']['npmBin']
        self._callExternal( [ npmBin, 'prune', '--production' ] )

