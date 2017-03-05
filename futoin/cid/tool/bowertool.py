
import json
from collections import OrderedDict

from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn

class bowerTool( NpmToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'bower.json' )

    def loadConfig( self, config ) :
        with open('bower.json', 'r') as content_file:
            content = content_file.read()
            object_pairs_hook = lambda pairs: OrderedDict( pairs )
            content = json.loads( content, object_pairs_hook=object_pairs_hook )
        f = 'name'
        if f in content and f not in config:
            config[f] = content[f]

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            f = 'name'
            if f in updates :
                    json[f] = updates[f]
                    
            # version is deprecated
            if 'version' in json:
                del json['version']

        return self._updateJSONConfig( 'bower.json', updater )
    
    def onPrepare( self, config ):
        bowerBin = config['env']['bowerBin']
        self._callExternal( [ bowerBin, 'install' ] )

    def onPackage( self, config ):
        bowerBin = config['env']['bowerBin']
        # TODO: not sure
        self._callExternal( [ bowerBin, 'install', '--production' ] )
    
