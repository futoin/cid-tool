
import os
import subprocess
import importlib
import json
from collections import OrderedDict

class CITool :
    def __init__( self, overrides ) :
        self._tool_impl = {
            'futoin' : None,
            'nvm' : None,
            'rvm' : None,
            'php' : None,
            'python' : None,
            'node' : None,
            'ruby' : None,
            'svn' : None,
            'git' : None,
            'hg' : None,
            'composer' : None,
            'npm' : None,
            'grunt' : None,
            'gulp' : None,
            'bower' : None,
            'sftp' : None,
            'archiva' : None,
            'artifactory' : None,
            'nexus' : None,
        }
        self._overrides = overrides
        self._initConfig()
        
    def _forEachTool( self, cb ) :
        config = self._config
        tool_impl = self._tool_impl
        tools = config.get( 'tools' )

        for t in tools :
            t = tool_impl[t]
            cb( config, t )
        
    def tag( self, branch, next_version=None ):
        config = self._config
        vcstool = config['vcs']
        vcstool = self._tool_impl[vcstool]
        
        # make a clean checkout
        vcstool.vcsCheckout( config, branch )
        self._initConfig()
        config = self._config
        
        # Set new version
        if next_version is None:
            if 'version' in config :
                next_version = config['version']
            else :
                raise RuntimeError( 'current version is unknown' )

            next_version = next_version.split('.')
            next_version[-1] = str(int(next_version[-1]) + 1)
            next_version = '.'.join( next_version )
        config['version'] = next_version
        
        # Update files for release
        to_commit = []        
        self._forEachTool(
            lambda config, t: to_commit.extend(
                t.updateProjectConfig( config, { 'version' : next_version } )
            )
        )
        
        # Commit updated files
        message = "Updated for release %s %s" % ( config['name'], config['version'] )
        vcstool.vcsCommit( config, message, to_commit )
        
        # Craete a tag
        tag = "v%s" % next_version
        message = "Release %s %s" % ( config['name'], config['version'] )
        vcstool.vcsTag( config, tag, message )

        # Push changes for DVCS
        vcstool.vcsPush( config, [ branch, tag ] )
    
    def prepare( self, vcs_ref ):
        config = self._config

        if ( 'vcs' not in config and
             'vcsRepo' not in self._overrides ):
            os.chdir( config['wcDir'] )
            self._initConfig()
            config = self._config
        
        vcstool = config['vcs']
        vcstool = self._tool_impl[vcstool]
        
        # make a clean checkout
        vcstool.vcsCheckout( config, vcs_ref )
        self._initConfig()

        #--
        self._forEachTool(
            lambda config, t: t.onPrepare( config )
        )
   
    def build( self ):
        self._forEachTool(
            lambda config, t: t.onBuild( config )
        )
    
    def package( self ):
        self._forEachTool(
            lambda config, t: t.onPackage( config )
        )
    
    def promote( self, package, rms_pool ):
        pass
    
    def deploy( self, package, location ):
        pass
    
    def run( self, package=None ):
        pass
    
    def ci_build( self, vcs_ref, rms_pool ):
        pass
    
    def _initConfig( self ):
        self._global_config = gc = self._loadJSON( '/etc/futoin/futoin.json', {'env':{}} )
        self._user_config = uc = self._loadJSON( os.environ.get('HOME','/') + 'futoin.json', {'env':{}} )
        self._project_config = pc = self._loadJSON( 'futoin.json', {} )
        merged = OrderedDict( pc )
        
        if pc.has_key( 'env' ):
            raise RuntimeError( '.env node is set in project config' )
        
        if not uc.has_key( 'env' ) or len( uc ) != 1:
            raise RuntimeError( 'User config must have only .env node' )
        
        if not gc.has_key( 'env' ) or len( gc ) != 1:
            raise RuntimeError( 'Glboal config must have only .env node' )
        
        env = OrderedDict( uc['env'] )
        
        for ( k, v ) in gc.items():
            env.setdefault( k, v )
        
        self._initEnv( env )
        merged['env'] = env
        merged.update( self._overrides )
        self._config = merged
        
        self._initTools()
    
    def _loadJSON( self, file_name, defvalue ):
        try :
            with open(file_name, 'r') as content_file:
                content = content_file.read()
                object_pairs_hook = lambda pairs: OrderedDict( pairs )
                return json.loads( content, object_pairs_hook=object_pairs_hook )
        except IOError:
            return defvalue
        
    def _initEnv( self, env ) :
        env.setdefault( 'type', 'dev' )
        env.setdefault( 'init', 'cron' )
        env.setdefault( 'webServer', 'nginx' )
        env.setdefault( 'vars', {} )

        tool_impl = self._tool_impl
        
        for ( k, v ) in tool_impl.items() :
            if v is None :
                pkg = 'citool.tool.' + k + 'tool'
                m = importlib.import_module( pkg )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )
        
        if env.has_key( 'plugins' ) :
            for ( k, v ) in env['plugins'] :
                m = importlib.import_module( v )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )
            
        
        for t in tool_impl.values():
            t.initEnv( env )
            
    def _initTools( self ):
        config = self._config
        tools = config.get( 'tools', None )
        tool_impl = self._tool_impl
        
        if tools is None :
            tools = []
            
            for ( n, t ) in tool_impl.items():
                if t.autoDetect( config ) :
                    tools.append( n )

        # add all deps
        #--
        deps = set( tools )
        dep_generations = [ list( deps ) ]
        l = 0
        while len( deps ) != l :
            l = len( deps )
            moredeps = set()
            for t in deps :
                t = tool_impl[t]
                moredeps.update( set( t.getDeps() ) )
            dep_generations.append( list( moredeps - deps ) )
            deps.update( moredeps )
            
        tools.extend( deps )
        
        #---
        dep_generations.reverse()
        tools = []
        for d in dep_generations :
            tools.extend( d )
        config['tools'] = tools

        #--
        for t in tools :
            t = tool_impl[t]
            t.requireInstalled( config )
            t.loadConfig( config )
            
        
            
        
        
            
