
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
import time
import fnmatch
from collections import OrderedDict

from .subtool import SubTool

def _call_cmd( cmd ):
    print( 'Call: ' + subprocess.list2cmdline( cmd ), file=sys.stderr )
    subprocess.call( cmd, stdin=subprocess.PIPE )    

def cid_action( f ):
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

class CIDTool :
    TO_GZIP = '\.(js|json|css|svg|txt)$'

    DEPLOY_PATTERN = '^(([a-zA-Z][a-zA-Z0-9_]+:)([a-zA-Z][a-zA-Z0-9_]+@[a-zA-Z][a-zA-Z0-9_]+))(:(.+))?$'
    DEPLOY_GRP_DEPLOY_USER = 2
    DEPLOY_GRP_RUNUSER_HOST = 3
    DEPLOY_GRP_PATH = 5

    def __init__( self, overrides ) :
        self._startup_env = dict(os.environ)
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

    @cid_action
    def tag( self, branch, next_version=None ):
        if next_version and not re.match('^[0-9]+\.[0-9]+\.[0-9]+$', next_version):
            print( 'Valid version format: x.y.z', file=sys.stderr )
            sys.exit( 1 )
            
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

    @cid_action
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

    @cid_action
    def build( self ):
        self._forEachTool(
            lambda config, t: t.onBuild( config )
        )

    @cid_action
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
    
    @cid_action
    def promote( self, package, rms_pool ):
        config = self._config
        rmstool = config['rms']
        rmstool = self._tool_impl[rmstool]
        rmstool.rmsPromote( config, package, rms_pool )
        
    @cid_action
    def migrate( self, location ):
        self._forEachTool(
            lambda config, t: t.onMigrate( config, location )
        )
    
    @cid_action
    def deploy( self, rms_pool, package=None ):
        config = self._config
        rmstool = config['rms']
        rmstool = self._tool_impl[rmstool]
        
        # Get to deploy folder
        deploy_dir = config['deployDir']
        if deploy_dir:
            os.chdir( deploy_dir )

        # Find out package to deploy
        package_list = rmstool.rmsGetList( config, rms_pool, package )

        if package:
            package_list = fnmatch.filter(package_list, package)
            
        if not package_list:
            print( "No package found", file = sys.stderr )
            sys.exit( 1 )
            
        def castver(v):
            res = re.split('\W+', 'Words, words, words.')
            for (i, vc) in enumerate(v):
                try: res[i] = int(vc, 10)
                except: pass
            return res
            
        package_list.sort(key=castver)
        package = package_list[-1]
            
        # cleanup first, in case of incomplete actions
        self._deployCleanup( [package] )

        # Prepare package name components
        package_basename = os.path.basename( package )
        ( package_noext, package_ext ) = os.path.splitext( package_basename )
        
        # Check if already deployed:
        if os.path.exists( package_noext ) and not config['reDeploy']:
            print( "Package has been already deployed. Use --redeploy.")
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
        
        self._deployCommon( package_noext_tmp, package_noext, [package] )
        
    def vcsref_deploy( self, vcs_ref ):
        config = self._config

    def vcstag_deploy( self, vcs_ref ):
        config = self._config

    def _deployCommon( self, tmp, dst, cleanup_whitelist ):
        config = self._config
        
        # Setup persistent folders
        persistent_dir = os.path.abspath( config['env'].get('persistentDir', 'persistent') )
        wdir_wperm = stat.S_IRUSR | stat.S_IXUSR | \
                    stat.S_IRGRP | stat.S_IXGRP | \
                    stat.S_IWUSR | stat.S_IWGRP
        
        for d in config.get('persistent', []) :
            pd = os.path.join( persistent_dir, d )
            dd = os.path.join( tmp, d )

            if not os.path.isdir( pd ) :
                os.makedirs( pd, wdir_wperm )
                
            if os.path.exists( dd ):
                shutil.copytree( dd, pd )
                shutil.rmtree( dd )
            
            os.symlink( pd, dd )
            
        # Setup read-only permissions
        dir_perm = stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP
        file_perm = stat.S_IRUSR | stat.S_IRGRP
        walk_list = os.walk( tmp )
        os.chmod( tmp, dir_perm )
        
        for ( path, dirs, files ) in walk_list :
            for d in dirs :
                os.chmod( os.path.join( path, d ), dir_perm )
            for f in files :
                os.chmod( os.path.join( path, f ), file_perm )
            
        # Complete migration
        self.migrate( tmp )
        
        # Setup per-user services
        self._deployServices( tmp )
        
        # Move in place
        if os.path.exists( dst ):
            # re-deploy case
            os.rename( dst, dst + '.tmprm' )
        os.rename( tmp, dst )
        os.symlink( dst, 'current.tmp' )
        os.rename( 'current.tmp', 'current' )
        
        # Re-run
        self.run( 'reload' )
        
        # Cleanup old packages and deploy dirs
        self._deployCleanup( cleanup_whitelist )
        
    def _deployCleanup( self, whitelist ):
        if os.path.exists('current'):
            whitelist.append( os.path.basename(os.readlink('current')) )
            
        whitelist += ['current', 'persistent']

        for f in os.listdir( '.' ):
            ( f_noext, f_ext ) = os.path.splitext( f )
            
            if f in whitelist:
                continue
            
            if os.path.isdir(f):
                os.chmod( f, stat.S_IRWXU )

                for ( path, dirs, files ) in os.walk( f ) :
                    for id in dirs + files :
                        os.chmod( os.path.join( path, id ), stat.S_IRWXU )

                shutil.rmtree(f)
            else:
                os.chmod( f, stat.S_IRWXU )
                os.remove( f )
            
            
    def _deployServices( self, subdir ):
        pass
    
    @cid_action
    def run( self, command ):
        config = self._config
        if config.get('vcs', None) :
            self.runDev( command )
            return

    @cid_action
    def runDev( self, command ):
        pass
    
    @cid_action
    def ci_build( self, vcs_ref, rms_pool ):
        config = self._config

        if os.path.exists( config['wcDir'] ) :
            os.rename( config['wcDir'], '{0}.bak{1}'.format(config['wcDir'], int(time.time())) )
        
        self._lastPackage = None
        self.prepare( vcs_ref )
        self.build()
        self.package()
        self.promote( self._lastPackage, rms_pool )

    @cid_action
    def tool_exec( self, tool, args ):
        t = self._tool_impl[tool]
        bin = self._config['env'].get(tool + 'Bin')

        if bin :
            _call_cmd([bin] + args)
        else :
            raise NotImplementedError( "Tool exec has not been implemented for %s" % tool )
    
    @cid_action
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

    @cid_action
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

    @cid_action
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

    @cid_action
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

    @cid_action
    def tool_env( self, tool ):
        config = self._config
        env = config['env']

        if tool :
            tools = [tool]
        else :
            tools = config['tools']
            
        res = dict(os.environ)
        
        # remove unchanged vars
        for k, v in self._startup_env.items():
            if res.get(k, None) == v:
                del res[k]

        for tool in tools:
            self._tool_impl[tool].exportEnv(env, res)
            
        for k, v in res.items():
            print("{0}='{1}'".format(k, v.replace("'", "\\'").replace('\\', '\\\\')))

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
                pkg = 'futoin.cid.tool.' + k + 'tool'
                m = importlib.import_module( pkg )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

            self._tool_impl = tool_impl
        
        for ( k, v ) in env['plugins'] :
            if not tool_impl.has_key(k):
                m = importlib.import_module( v )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

        #---
        curr_tool = config.get('tool', None)
        
        if curr_tool:
            tools = [ curr_tool ]
        else :
            tools = config.get('tools', [])
            
            if not tools:
                for ( n, t ) in tool_impl.items():
                    if t.autoDetect( config ) :
                        tools.append( n )

            # Make sure deps & env are processed for cli-supplied tools
            #--
            for item in ['rms', 'vcs']:
                tool = config.get(item, None)

                if tool:
                    tools.append( tool )

                    if tool_impl[ tool ].getType() != item:
                        raise RuntimeError('Tool {0} does not suite {1} type'.format(tool, item))

        # add all deps
        #--
        dep_generations = [ set(tools) ]
        tools = set( tools )
        tools_length = 0
        last_index = 0
        while len( tools ) != tools_length :
            tools_length = len( tools )
            curr_index = last_index
            last_index = len(dep_generations)

            for g in dep_generations[curr_index:] :
                for tn in g:
                    t = tool_impl[tn]
                    moredeps = set(t.getDeps())
                    if moredeps:
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
