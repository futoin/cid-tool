
import json
import os

from collections import OrderedDict

from citool.subtool import SubTool

class composerTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def _installTool( self, env ):
        composer_dir = env['composerDir']
        php_bin = env['phpBin']
        curl_bin = env['curlBin']
        composer_get = env.get('composerGet', 'https://getcomposer.org/installer')

        self._callExternal(
            [ 'bash', '-c',
              'mkdir -p {2} &&  {3} -s {0} | {1} -- --install-dir={2} --filename=composer'
              .format(composer_get, php_bin, composer_dir, curl_bin) ] )

    def _initEnv( self, env ) :
        bin_dir = env['binDir']
        composer_dir = env.setdefault('composerDir', bin_dir)

        if (bin_dir != composer_dir and
            composer_dir not in os.environ['PATH'].split(os.pathsep)):
                os.environ['PATH'] += os.pathsep + composer_dir

        SubTool._initEnv( self, env )

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'composer.json' )
    
    def getDeps( self ) :
        return [ 'php', 'curl' ]

    def loadConfig( self, config ) :
        with open('composer.json', 'r') as content_file:
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

        return self._updateJSONConfig( 'composer.json', updater, indent=4 )
    
    def onPrepare( self, config ):
        composerBin = config['env']['composerBin']
        self._callExternal( [ composerBin, 'install' ] )
        
    def onPackage( self, config ):
        composerBin = config['env']['composerBin']
        self._callExternal( [ composerBin, 'install', '--no-dev' ] )

