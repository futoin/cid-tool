
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
import stat
from collections import OrderedDict

from .subtool import SubTool

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
                    _call_cmd( ['sh', '-c', a] )
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
        self._tool_impl = None
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

        # make a clean checkout
        if vcs_ref:
            vcstool = config['vcs']
            vcstool = self._tool_impl[vcstool]

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
        package_file = config.get( 'package_file', None )

        if package_file:
            self._lastPackage = package_file
            return

        #---
        package_content = config.get( 'package', [ '.' ] )
        if type(package_content) != type([]):
            package_content = [ package_content ] 
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
                    with open(f, 'rb') as f_in:
                        with gzip.open(f + '.gz', 'wb', 9) as f_out:
                            shutil.copyfileobj(f_in, f_out)
        
        #---
        checksums_file = '.package.checksums'
        try:
            package_content.index( '.' )
        except ValueError:
            package_content.append( checksums_file )
        cmd = 'find {0} -type f | sort | xargs sha512sum >{1}'.format(
                package_content_cmd, checksums_file )
        _call_cmd( ['sh', '-c', cmd] )
        
        #---
        buildTimestamp = datetime.datetime.utcnow().strftime( '%Y%m%d%H%M%S' )
        name = config['name'].split('/')[-1]
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
            
        package_file += '.txz'
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
    def migrate( self, location ):
        self._forEachTool(
            lambda config, t: t.onMigrate( config, location )
        )
    
    @citool_action
    def deploy( self, rms_pool, package=None ):
        config = self._config
        rmstool = config['rms']
        rmstool = self._tool_impl[rmstool]
        
        # Get to deploy folder
        deploy_dir = config['deployDir']
        if deploy_dir:
            os.chdir( deploy_dir )

        # cleanup first, in case of incomplete actions
        self._deployCleanup()

        # Find out package to deploy
        if not package:
            package = rmstool.rmsGetLatest( config, rms_pool )
            
        # Prepare package name components
        package_basename = os.path.basename( package )
        ( package_noext, package_ext ) = os.path.splitext( package_basename )
        
        # Check if already deployed:
        if os.path.exists( package_noext ) and not config['reDeploy']:
            return
        
        # Retrieve package, if not available
        if not os.path.exists( package_basename ) :
            rmstool.rmsRetrieve( config, rms_pool, package )
            
        package_noext_tmp = package_noext + '.tmp'
        
        # Prepare temporary folder
        if os.path.exists( package_noext_tmp ) :
            shutil.rmtree( package_noext_tmp )
        os.mkdir( package_noext_tmp )
        
        # Unpack package to temporary folder
        if package_ext == '.txz':
            _call_cmd( ['tar', 'xJf', package_basename, '-C', package_noext_tmp ] )
        elif package_ext == '.tbz2':
            _call_cmd( ['tar', 'xjf', package_basename, '-C', package_noext_tmp ] )
        elif package_ext == '.tgz':
            _call_cmd( ['tar', 'xzf', package_basename, '-C', package_noext_tmp ] )
        elif package_ext == '.tar':
            _call_cmd( ['tar', 'xf', package_basename, '-C', package_noext_tmp ] )
        else:
            raise RuntimeError( 'Not supported package format: ' + package_ext )
        
        # Setup read-only permissions
        dir_perm = stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP
        file_perm = stat.S_IRUSR | stat.S_IRGRP
        walk_list = os.walk( package_noext_tmp )
        os.chmod( package_noext_tmp, dir_perm )
        
        for ( path, dirs, files ) in walk_list :
            for d in dirs :
                os.chmod( os.path.join( path, d ), dir_perm )
            for f in files :
                os.chmod( os.path.join( path, f ), file_perm )

        # Setup writable permission
        persistent_dir = os.path.abspath( 'persistent' )
        dir_wperm = dir_perm | stat.S_IWUSR | stat.S_IWGRP
        
        for d in config.get('writable', []) :
            pd = os.path.join( persistent_dir, d )
            if not os.path.isdir( pd ) :
                os.makedirs( pd, dir_wperm )
                
            os.symlink( pd, os.path.join( package_noext_tmp, d ) )
            
        # Complete migrate
        self.migrate( package_noext_tmp )
        
        # Setup per-user services
        self._deployServices( package_noext_tmp )
        
        # Move in place
        if os.path.exists( package_noext ):
            # re-deploy case
            os.rename( package_noext, package_noext + '.tmprm' )
        os.rename( package_noext_tmp, package_noext )
        
        # Re-run
        self.run( 'reload' )
        
        # Cleanup old packages and deploy dirs
        self._deployCleanup()
        
    def _deployCleanup( self ):
        pass
            
    def _deployServices( self, subdir ):
        pass
    
    @citool_action
    def run( self, command ):
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

    @citool_action
    def tool_exec( self, tool, args ):
        t = self._tool_impl[tool]
        bin = self._config['env'].get(tool + 'Bin')

        if bin :
            _call_cmd([bin] + args)
        else :
            raise NotImplementedError( "Tool exec has not been implemented for %s" % tool )
    
    @citool_action
    def tool_install( self, tool ):
        config = self._config
        env = config['env']
        
        if SubTool.isExternalToolsSetup( env ):
            raise RuntimeError( "Tools must be installed externally (env config)" )

        if tool :
            tools = [tool]
        else :
            tools = config['tools']

        for tool in tools:
            t = self._tool_impl[tool]
            t.requireInstalled( env )

    @citool_action
    def tool_uninstall( self, tool ):
        config = self._config
        env = config['env']
        
        if SubTool.isExternalToolsSetup( env ):
            raise RuntimeError( "Tools must be uninstalled externally (env config)" )

        if tool :
            tools = [tool]
        else :
            tools = reversed(config['tools'])

        for tool in tools:
            t = self._tool_impl[tool]
            if t.isInstalled( env ):
                t.uninstallTool( env )

    @citool_action
    def tool_update( self, tool ):
        config = self._config
        env = config['env']
        
        if SubTool.isExternalToolsSetup( env ):
            raise RuntimeError( "Tools must be updated externally (env config)" )

        if tool :
            tools = [tool]
        else :
            tools = config['tools']

        for tool in tools:
            t = self._tool_impl[tool]
            t.updateTool( env )

    @citool_action
    def tool_test( self, tool ):
        config = self._config
        env = config['env']

        if tool :
            tools = [tool]
        else :
            tools = config['tools']

        for tool in tools:
            t = self._tool_impl[tool]
            
            if not t.isInstalled( env ) :
                print( "Tool '%s' is missing" % tool )
                sys.exit( 1 )
    
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
        
        if 'env' in pc:
            raise RuntimeError( '.env node is set in project config' )

        if 'env' not in dc or len( dc ) != 1:
            raise RuntimeError( 'Deploy config must have only .env node' )
        
        if 'env' not in uc or len( uc ) != 1:
            raise RuntimeError( 'User config must have only .env node' )
        
        if 'env' not in gc or len( gc ) != 1:
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
        env.setdefault( 'startup', 'cron' )
        env.setdefault( 'webServer', 'nginx' )
        env.setdefault( 'vars', {} )
        env.setdefault( 'mainConfig', {} )
        env.setdefault( 'plugins', {} )

        env.setdefault( 'externalSetup', {} )
        externalSetup = env['externalSetup']
        externalSetup.setdefault( 'runCmd', None )
        externalSetup.setdefault( 'webServer', False )
        externalSetup.setdefault( 'startup', False )
        externalSetup.setdefault( 'installTools', False )

        env.setdefault( 'binDir', os.path.join(os.environ['HOME'], 'bin') )
        SubTool.addBinPath( env['binDir'] )

    def _initTools( self ):
        config = self._config
        env = config['env']

        #---
        tool_impl = self._tool_impl
        
        if tool_impl is None:
            tool_impl = {}
            default_tool_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'tool'
            )

            for f in os.listdir(default_tool_dir):
                splitext = os.path.splitext(f)
                if splitext[1] != '.py' or splitext[0] in ['__init__']:
                    continue

                k = f.replace('tool.py', '')
                pkg = 'citool.tool.' + k + 'tool'
                m = importlib.import_module( pkg )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

            self._tool_impl = tool_impl
        
        for ( k, v ) in env['plugins'] :
            if not tool_impl.has_key(k):
                m = importlib.import_module( v )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

        #---
        tools = []
        curr_tool = config.get('tool', None)
        
        if curr_tool:
            tools.append( curr_tool )
        else :
            for ( n, t ) in tool_impl.items():
                if t.autoDetect( config ) :
                    tools.append( n )

            # Make sure deps & env are processed for RMS tool
            #--
            rmstool = config.get('rms', None)

            if rmstool:
                tools.append( rmstool )

        # add all deps
        #--
        dep_generations = [ set(tools) ]
        tools = set( tools )
        l = 0
        while len( tools ) != l :
            l = len( tools )
            moredeps = set()
            for t in dep_generations[-1] :
                t = tool_impl[t]
                moredeps.update( set( t.getDeps() ) )
            dep_generations.append( moredeps )
            tools.update( moredeps )
        
        #---
        dep_generations.reverse()
        tools = []
        for d in dep_generations :
            tools.extend( d - set(tools) )
        config['tools'] = tools

        #--
        if config['toolTest']:
            for tool in tools :
                t = tool_impl[tool]
                t.importEnv( env )
                t.initEnv( env )
        else :
            for tool in tools :
                t = tool_impl[tool]
                t.requireInstalled( env )
                if tool != curr_tool:
                    t.loadConfig( config )
