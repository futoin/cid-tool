
import json
import os
from collections import OrderedDict

from citool.subtool import SubTool


class puppetTool( SubTool ):
    METADATA_FILE = 'metadata.json'

    def getType( self ):
        return self.TYPE_BUILD
    
    def getDeps( self ) :
        return [ 'ruby', 'gem' ]

    def _installTool( self, env ):
        puppet_ver = env['puppetVer']
        version_arg = []
        
        if puppet_ver:
            version_arg = ['--version', puppet_ver]
        
        self._callExternal( [ env['gemBin'], 'install', 'puppet', '--no-document' ] + version_arg )
        
    def updateTool( self, env ):
        if env['puppetVer'] :
            self._installTool( env )
        else :
            self._callExternal( [ env['gemBin'], 'update', 'puppet', '--no-document' ] )
    
    def initEnv( self, env ):
        SubTool.initEnv( self, env )
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
