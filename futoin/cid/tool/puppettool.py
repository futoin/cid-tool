
import json
import os
from collections import OrderedDict

from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn


class puppetTool( GemToolMixIn, BuildTool ):
    METADATA_FILE = 'metadata.json'

    def _envNames( self ) :
        return ['puppetVer', 'puppetBin' ]
    
    def initEnv( self, env ):
        super(puppetTool, self).initEnv( env )
        puppet_ver = env.setdefault('puppetVer', None)
        
        if self._have_tool and puppet_ver:
            try:
                found_ver = self._callExternal( [ env['puppetBin'], '--version' ], verbose = False )
                self._have_tool = found_ver.find(puppet_ver) >= 0
            except:
                self._have_tool = False
                del env['puppetBin']

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, [
            self.METADATA_FILE,
            'manifests',
        ] )

    def loadConfig( self, config ) :
        with open(self.METADATA_FILE, 'r') as content_file:
            content = content_file.read()
            object_pairs_hook = lambda pairs: OrderedDict( pairs )
            content = json.loads( content, object_pairs_hook=object_pairs_hook )
        for f in ( 'name', 'version' ):
            if f in content and f not in config:
                config[f] = content[f]

        config['package'] = 'pkg'

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( self.METADATA_FILE, updater )

    def onBuild( self, config ):
        puppetBin = config['env']['puppetBin']
        self._callExternal( ['rm', 'pkg', '-rf'] )
        self._callExternal( [puppetBin, 'module', 'build'] )

    def onPackage( self, config ):
        package_file = 'pkg/{0}-{1}.tar.gz'.format(
                config['name'],
                config['version']
        )

        if not os.path.exists( package_file ) :
            raise RuntimeError( 'Puppet Module built package is missing: ' + package_file )

        config['package_file'] = package_file
