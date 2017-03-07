
from __future__ import print_function, absolute_import

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
import fcntl
from collections import OrderedDict

from .mixins.path import PathMixIn
from .mixins.util import UtilMixIn

from .vcstool import VcsTool
from .rmstool import RmsTool

__all__ = ['CIDTool']

def _call_cmd( cmd ):
    print( 'Call: ' + subprocess.list2cmdline( cmd ), file=sys.stderr )
    subprocess.call( cmd, stdin=subprocess.PIPE )    

def cid_action( f ):
    def custom_f( self, *args, **kwargs ) :
        config = self._config

        try:
            fn = f.func_name
        except AttributeError:
            fn = f.__name__

        if fn in config.get('actions', {}) :
            for a in config['actions'][fn] :
                if a == '<default>':
                    f( self, *args, **kwargs )
                else :
                    _call_cmd( ['sh', '-c', a] )
        else :
            f( self, *args, **kwargs )
    return custom_f

class CIDTool( PathMixIn, UtilMixIn ) :
    TO_GZIP = '\.(js|json|css|svg|txt)$'
    VCS_CACHE_DIR = 'vcs'
    
    DEPLOY_LOCK_FILE = '.futoin.lock'
    _deploy_lock = False

    def __init__( self, overrides ) :
        self._startup_env = dict(os.environ)
        self._tool_impl = None
        self._overrides = overrides
        self._initConfig()
        
    def _forEachTool( self, cb, allow_failure=False ) :
        config = self._config
        tool_impl = self._tool_impl
        tools = config['tools']

        for t in tools :
            t = tool_impl[t]
            try:
                cb( config, t )
            except RuntimeError as e:
                if not allow_failure:
                    raise e
            
    def _getVcsTool( self ):
        config = self._config
        vcstool = config.get('vcs', None)
        
        if not vcstool:
            print( 'Unknown VCS. Please set through --vcsRepo or project manifest' )
            sys.exit( 1 )
            
        vcstool = self._tool_impl[vcstool]
            
        if not config.get('vcsRepo', None): # also check it set
            config['vcsRepo'] = vcstool.vcsGetRepo( config )
            
            if not config['vcsRepo']:
                print( 'Unknown VCS repo. Please set through --vcsRepo or project manifest' )
                sys.exit( 1 )
        
        return vcstool

    def _getRmsTool( self ):
        config = self._config
        rmstool = config.get('rms', None)
        
        if not rmstool:
            print( 'Unknown RMS. Please set through --rmsRepo or project manifest' )
            sys.exit( 1 )
        
        if not config.get('rmsRepo', None): # also check it set
            print( 'Unknown RMS repo. Please set through --rmsRepo or project manifest' )
            sys.exit( 1 )
        
        return self._tool_impl[rmstool]

    def _processWcDir( self ):
        config = self._config
        wcDir = config['wcDir']
        
        if not os.path.exists(wcDir):
            os.makedirs(wcDir)
        
        if wcDir != os.getcwd():
            os.chdir( wcDir )
            self._overrides['wcDir'] = config['wcDir'] = '.'
            self._initConfig()

    @cid_action
    def tag( self, branch, next_version=None ):
        if next_version and not re.match('^[0-9]+\.[0-9]+\.[0-9]+$', next_version):
            print( 'Valid version format: x.y.z', file=sys.stderr )
            sys.exit( 1 )
            
        self._processWcDir()
            
        config = self._config
        vcstool = self._getVcsTool()
        
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
        self._processWcDir()
        
        config = self._config

        # make a clean checkout
        if vcs_ref:
            vcstool = self._getVcsTool()

            vcstool.vcsCheckout( config, vcs_ref )
            self._initConfig()

        #--
        self._forEachTool(
            lambda config, t: t.onPrepare( config )
        )

    @cid_action
    def build( self ):
        self._processWcDir()
        
        self._forEachTool(
            lambda config, t: t.onBuild( config )
        )

    @cid_action
    def package( self ):
        self._processWcDir()
        
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
            vcstool = self._getVcsTool()
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
    def check( self ):
        self._processWcDir()
        
        self._forEachTool(
            lambda config, t: t.onCheck( config ),
            allow_failure = self._config.get('permissiveChecks', False)
        )

    @cid_action
    def promote( self, package, rms_pool ):
        config = self._config
        rmstool = self._getRmsTool()
        rmstool.rmsPromote( config, package, rms_pool )
        
    @cid_action
    def migrate( self, location ):
        self._processWcDir()
        
        self._forEachTool(
            lambda config, t: t.onMigrate( config, location )
        )
        
    def _deployLock( self ):
        self._deploy_lock = open(self.DEPLOY_LOCK_FILE, 'w')
        try:
            fcntl.flock(self._deploy_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            print('FAILED to acquire deploy lock! ', file=sys.stderr)
            sys.exit( 1 )
    
    def _deployUnlock( self ):
        fcntl.flock(self._deploy_lock, fcntl.LOCK_UN)
        self._deploy_lock.close()
        self._deploy_lock = None
    
    @cid_action
    def deploy( self, mode, p1, p2=None ):
        # Get to deploy folder
        deploy_dir = self._config['deployDir']
        if deploy_dir:
            if not os.path.exists( deploy_dir ) :
                os.makedirs( deploy_dir )
            os.chdir( deploy_dir )

        self._deployLock()
        
        if mode == 'rms':
            self._rms_deploy(p1, p2)
        elif mode == 'vcsref':
            self._vcsref_deploy(p1)
        elif mode == 'vcstag':
            self._vcstag_deploy(p1)
        else:
            raise RuntimeError( 'Not supported deploy mode: ' + mode )
        
    def _rms_deploy( self, rms_pool, package=None ):
        config = self._config
        rmstool = self._getRmsTool()

        # Find out package to deploy
        package_list = rmstool.rmsGetList( config, rms_pool, package )

        if package:
            package_list = fnmatch.filter(package_list, package)
            
        if not package_list:
            print( "No package found", file = sys.stderr )
            sys.exit( 1 )
            
        package = self._getLatest(package_list)
            
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
        
        # Common processing
        self._deployCommon( package_noext_tmp, package_noext, [package] )
        
    def _vcsref_deploy( self, vcs_ref ):
        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        vcs_cache = self.VCS_CACHE_DIR
        rev = vcstool.vcsGetRefRevision( config, vcs_cache, vcs_ref )
            
        if not rev:
            print( "No VCS refs found", file = sys.stderr )
            sys.exit( 1 )
            
        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        target_dir += '__' + rev
            
        # cleanup first, in case of incomplete actions
        self._deployCleanup( [vcs_cache, target_dir] )
        
        # Check if already deployed:
        if os.path.exists( target_dir ) and not config['reDeploy']:
            print( "Package has been already deployed. Use --redeploy.")
            return
           
        # Retrieve tag
        target_tmp = target_dir + '.tmp'
        vcstool.vcsExport( config, vcs_cache, vcs_ref, target_tmp )

        # Common processing
        self._deployCommon( target_tmp, target_dir, [vcs_cache] )      

    def _vcstag_deploy( self, vcs_ref ):
        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        vcs_cache = self.VCS_CACHE_DIR
        tag_list = vcstool.vcsListTags( config, vcs_cache, vcs_ref )

        if vcs_ref:
            tag_list = fnmatch.filter(tag_list, vcs_ref)
            
        if not tag_list:
            print( "No tags found", file = sys.stderr )
            sys.exit( 1 )
            
        vcs_ref = self._getLatest(tag_list)
        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
            
        # cleanup first, in case of incomplete actions
        self._deployCleanup( [vcs_cache, target_dir] )
        
        # Check if already deployed:
        if os.path.exists( target_dir ) and not config['reDeploy']:
            print( "Package has been already deployed. Use --redeploy.")
            return
           
        # Retrieve tag
        vcs_ref_tmp = target_dir + '.tmp'
        vcstool.vcsExport( config, vcs_cache, vcs_ref, vcs_ref_tmp )

        # Common processing
        self._deployCommon( vcs_ref_tmp, target_dir, [vcs_cache] )        
        
    def _getLatest( self, verioned_list ):
        def castver(v):
            res = re.split(r'[\W_]+', v)
            for (i, vc) in enumerate(res):
                try: res[i] = int(vc, 10)
                except: pass
            return res
            
        verioned_list.sort(key=castver)
        return verioned_list[-1]

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
                self._rmTree( dd )
            
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
                
        # Build
        if config.get('deployBuild', False):
            cwd = os.getcwd()
            config['wcDir'] = tmp
            self.prepare(None)
            self.build()
            os.chdir(cwd)
            
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
        self._deployUnlock()
        
    def _deployCleanup( self, whitelist ):
        if os.path.exists('current'):
            whitelist.append( os.path.basename(os.readlink('current')) )
            
        whitelist += ['current', 'persistent', self.DEPLOY_LOCK_FILE]

        for f in os.listdir( '.' ):
            ( f_noext, f_ext ) = os.path.splitext( f )
            
            if f in whitelist:
                continue
            
            if os.path.isdir(f):
                self._rmTree(f)
            else:
                os.chmod( f, stat.S_IRWXU )
                os.remove( f )
            
            
    def _deployServices( self, subdir ):
        pass
    
    @cid_action
    def run( self, command ):
        self._processWcDir()
        
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
        wcDir = config['wcDir']

        if os.path.exists( wcDir ) and wcDir != os.getcwd():
            os.rename( wcDir, '{0}.bak{1}'.format(wcDir, int(time.time())) )
        
        self._lastPackage = None
        self.prepare( vcs_ref )
        self.build()
        self.package()
        self.check()
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
        
        if self._isExternalToolsSetup( env ):
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
        
        if self._isExternalToolsSetup( env ):
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
        
        if self._isExternalToolsSetup( env ):
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
        self._addBinPath( env['binDir'] )

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
            
            tool_files = os.listdir(default_tool_dir)
            tool_files = fnmatch.filter(tool_files, '*tool.py')

            for f in tool_files:
                k = f.replace('tool.py', '')
                pkg = 'futoin.cid.tool.' + k + 'tool'
                m = importlib.import_module( pkg )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

            self._tool_impl = tool_impl
            
        plugins = env['plugins'].copy()
        plugins.update( config.get( 'plugins', {} ) )
        
        for ( k, v ) in plugins.items() :
            if k not in tool_impl:
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
            for (item, base) in {'rms' : RmsTool, 'vcs' : VcsTool}.items():
                tool = config.get(item, None)

                if tool:
                    tools.append( tool )

                    if not isinstance(tool_impl[ tool ], base):
                        raise RuntimeError('Tool {0} does not suite {1} type'.format(tool, item))

        # add all deps
        #--
        dep_generations = [ set(tools) ]
        tools = set( tools )
        postdeps = set()
        dep_length = 0
        last_index = 0
        while len( dep_generations ) != dep_length :
            dep_length = len( dep_generations )
            curr_index = last_index
            last_index = len(dep_generations)

            for g in dep_generations[curr_index:]:
                for tn in g:
                    t = tool_impl[tn]
                    moredeps = set(t.getDeps())
                    if moredeps:
                        dep_generations.append( moredeps )
                        tools.update( moredeps )
                    postdeps.update( set(t.getPostDeps()) - tools )

            if len( dep_generations ) == dep_length and postdeps:
                dep_generations.append( postdeps )
                tools.update( postdeps )
                postdeps = set()
    
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

        # Solves generic issues of ordering independent tools in
        # later execution with predictable results:
        # 1. sort by integer order
        # 2. sort by tool name
        tools.sort( key=lambda v: ( tool_impl[v].getOrder(), v ) )
