
import os
import subprocess
import importlib
from collections import OrderedDict

class CITool :
    def __init__( self, overrides ) :
        self._tools = {
            'php' : None,
            'python' : None,
            'nodejs' : None,
            'svn' : None,
            'git' : None,
            'hg' : None,
            'composer' : None,
            'npm' : None,
            'grunt' : None,
            'gulp' : None
        }
        self._overrides = overrides
        self._initConfig()
        
    def tag( self, branch, next_version=None ):
        pass
    
    def prepare( self, vcs_ref ):
        pass
    
    def build( self ):
        pass
    
    def package( self ):
        pass
    
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
            raise InputError( '.env node is set in project config' )
        
        if not uc.has_key( 'env' ) or len( uc ) != 1:
            raise InputError( 'User config must have only .env node' )
        
        if not gc.has_key( 'env' ) or len( gc ) != 1:
            raise InputError( 'Glboal config must have only .env node' )
        
        env = OrderedDict( uc['env'] )
        
        for ( k, v ) in gc.items():
            env.setdefault( k, v )
        
        self._initEnv( env )
        merged['env'] = env
        self._config = merged
    
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

        tools = self._tools
        
        for ( k, v ) in tools.items() :
            if v is None :
                pkg = 'citool.tool.' + k + 'tool'
                m = importlib.import_module( pkg )
                tools[ k ] = getattr( m, k + 'Tool' )( k )
        
        if env.has_key( 'plugins' ) :
            for ( k, v ) in env['plugins'] :
                m = importlib.import_module( v )
                tools[ k ] = getattr( m, k + 'Tool' )( k )
            
        
        for t in tools.values():
            t.initEnv( env )
            
            
