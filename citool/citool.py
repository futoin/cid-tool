
from __future__ import print_function

import os
import sys
import subprocess
import importlib
import json
import datetime
import re
import gzip
import shutil
from collections import OrderedDict

def _call_cmd( cmd ):
    print( 'Call: ' + subprocess.list2cmdline( cmd ), file=sys.stderr )
    subprocess.call( cmd, stdin=subprocess.PIPE )    

def citool_action( f ):
    def custom_f( self, *args, **kwargs ) :
        config = self._config
        if 'actions' in config :
            for a in config['actions'] :
                if a == '<default>':
                    f( self, *args, **kwargs )
                else :
                    _call_cmd( ['bash', '-c', a] )
        else :
            f( self, *args, **kwargs )
    return custom_f

class CITool :
    TO_GZIP = '\.(js|json|css|svg|txt)$'

    DEPLOY_PATTERN = '^(([a-zA-Z][a-zA-Z0-9_]+:)([a-zA-Z][a-zA-Z0-9_]+@[a-zA-Z][a-zA-Z0-9_]+))(:(.+))?$'
    DEPLOY_GRP_DEPLOY_USER = 2
    DEPLOY_GRP_RUNUSER_HOST = 3
    DEPLOY_GRP_PATH = 5

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
            'ssh' : None,
            'scp' : None,
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

    @citool_action
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

    @citool_action
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

    @citool_action
    def build( self ):
        self._forEachTool(
            lambda config, t: t.onBuild( config )
        )

    @citool_action
    def package( self ):
        self._forEachTool(
            lambda config, t: t.onPackage( config )
        )
        
        #---
        config = self._config
        package_content = config.get( 'package', [ '.' ] )
        package_content.sort()
        package_content_cmd = subprocess.list2cmdline( package_content )
        
        # Note: It is assumed that web root is in the package content
        #---
        walk_list = os.walk( config.get( 'webcfg', {}).get( 'root', '.' ) )
        to_gzip_re = re.compile( self.TO_GZIP, re.I )
        for ( path, dirs, files ) in walk_list :
            for f in files :
                if to_gzip_re.search( f ):
                    f = os.path.join( path, f )
                    with open(f, 'rb') as f_in, gzip.open(f + '.gz', 'wb', 9) as f_out:
                        shutil.copyfileobj(f_in, f_out)
        
        #---
        checksums_file = '.package.checksums'
        package_content.append( checksums_file )
        cmd = 'find {0} -type f | sort | xargs sha512sum >{1}'.format(
                package_content_cmd, checksums_file )
        _call_cmd( ['bash', '-c', cmd] )
        
        #---
        buildTimestamp = datetime.datetime.utcnow().strftime( '%Y%m%d%H%M%S' )
        name = config['name'].replace( '/', '_' )
        version = config['version']
        vcs_ref = config.get( 'vcsRef', None )
        
        # Note: unless run in clean ci_build process,
        # all builds must be treated as snapshots/CI builds
        if vcs_ref == 'v' + version :
            package_file = '{0}-{1}-{2}'.format(
                    name, version, buildTimestamp )
        else :
            vcstool = config['vcs']
            vcstool = self._tool_impl[vcstool]
            vcs_ref = vcstool.vcsGetRevision( config )
            package_file = '{0}-CI-{1}-{2}-{3}'.format(
                    name, version, vcs_ref, buildTimestamp )

        if 'target' in config:
            package_file += '-{0}'.format( config['target'] )
            
        package_file += '.tar.xz'
        _call_cmd( ['tar', 'cJf', package_file,
                    '--exclude=' + package_file, '--exclude-vcs' ] + package_content )
        self._lastPackage = package_file
    
    @citool_action
    def promote( self, package, rms_pool ):
        config = self._config
        rmstool = config['rms']
        rmstool = self._tool_impl[rmstool]
        rmstool.rmsPromote( config, package, rms_pool )
        
    @citool_action
    def migrate( self, package, location ):
        self._forEachTool(
            lambda config, t: t.onMigrate( config )
        )
    
    @citool_action
    def deploy( self, package, location ):
        pass
    
    @citool_action
    def runDev( self, package=None ):
        raise NotImplementedError( "Development run has not been implemented yet" )
    
    @citool_action
    def run( self, package=None ):
        config = self._config
        if config.get('vcs', None) :
            self.runDev()
            return
    
    @citool_action
    def ci_build( self, vcs_ref, rms_pool ):
        config = self._config
        if os.path.exists( config['wcDir'] ) :
            os.rename( config['wcDir'], config['wcDir'] + '.bak' ) 
        
        self._lastPackage = None
        self.prepare( vcs_ref )
        self.build()
        self.package()
        self.promote( self._lastPackage, rms_pool )
    
    def _initConfig( self ):
        self._global_config = gc = self._loadJSON( '/etc/futoin/futoin.json', {'env':{}} )
        self._user_config = uc = self._loadJSON( os.path.join( os.environ.get('HOME','/'), 'futoin.json' ), {'env':{}} )
        self._project_config = pc = self._loadJSON( 'futoin.json', {} )

        deploy_dir = self._overrides.get( 'deployDir', None )
        dc = {'env':{}}
        if deploy_dir :
            dc = self._loadJSON( os.path.join( deploy_dir, 'futoin.json' ), dc )
        self._deploy_config = dc
        
        merged = OrderedDict( pc )
        
        if pc.has_key( 'env' ):
            raise RuntimeError( '.env node is set in project config' )

        if not dc.has_key( 'env' ) or len( dc ) != 1:
            raise RuntimeError( 'Deploy config must have only .env node' )
        
        if not uc.has_key( 'env' ) or len( uc ) != 1:
            raise RuntimeError( 'User config must have only .env node' )
        
        if not gc.has_key( 'env' ) or len( gc ) != 1:
            raise RuntimeError( 'Glboal config must have only .env node' )
        
        env = OrderedDict( dc['env'] )
        
        for ( k, v ) in uc.items():
            env.setdefault( k, v )
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
            
        
            
        
        
            
