#!/usr/bin/env python
"""FutoIn Continuous Integration & Delivery Tool.

Usage:
    cid init [<project_name>] [--vcsRepo=<vcs_repo>] [--rmsRepo=<rms_repo>] [--permissive]
    cid tag <branch> [<next_version>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid prepare [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid build [--debug]
    cid package
    cid check [--permissive]
    cid promote <package> <rms_pool> [--rmsRepo=<rms_repo>] [--rmsHash=<rms_hash>]
    cid deploy vcstag [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--redeploy] [--deployDir=<deploy_dir>]
    cid deploy vcsref <vcs_ref> [--vcsRepo=<vcs_repo>] [--redeploy] [--deployDir=<deploy_dir>]
    cid deploy [rms] <rms_pool> [<package>] [--rmsRepo=<rms_repo>] [--rmsHash=<rms_hash>] [--redeploy] [--deployDir=<deploy_dir>] [--build]
    cid migrate
    cid run
    cid run <command> [<command_arg>...]
    cid ci_build <vcs_ref> [<rms_pool>] [--vcsRepo=<vcs_repo>] [--rmsRepo=<rms_repo>] [--permissive] [--debug] [--wcDir=<wc_dir>]
    cid tool exec <tool_name> [<tool_version>] [-- <tool_arg>...]
    cid tool (install|uninstall|update|test|env) [<tool_name> [<tool_version>]]
    cid tool (prepare|build|check|package|migrate) <tool_name> [<tool_version>]
    cid tool list
    cid tool describe <tool_name>
    cid tool detect
    cid vcs checkout <vcs_ref> [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid vcs commit <commit_msg> [<commit_files>...]
    cid vcs merge <vcs_ref> [--no-cleanup]
    cid vcs branch <vcs_ref>
    cid vcs delete <vcs_ref> [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>]
    cid vcs export <vcs_ref> <dst_dir> [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>]
    cid vcs tags [<tag_pattern>] [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>]
    cid vcs branches [<branch_pattern>] [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>]
    cid vcs reset
    

Options:
    -h --help                       Show this screen.
    --vcsRepo=<vcs_repo>            VCS repository URL in vcs_type:vcs_url format.
    --rmsRepo=<rms_repo>            RMS repository URL in rms_type:rms_url format.
    --wcDir=<wc_dir>                Working copy directory (project root).
    --rmsHash=<rms_hash>            Package hash for validation in hash_type:value format.
    --deployDir=<deploy_dir>        Destination for deployment.
    --redeploy                      Force redeploy.
    --build                         Build during deploy.
    --permissive                    Ignore test failures.
    --debug                         Build in debug mode, if applicable.
    --cacheDir=<cache_dir>          Directory to hold VCS cache.
"""

from __future__ import print_function, absolute_import

from .cidtool import CIDTool
from .coloring import Coloring

try:
    from docopt import docopt
except ImportError:
    # fallback to "hardcoded"
    from futoin.cid.contrib.docopt import docopt

import os, sys, traceback

if sys.version_info < (2,7):
    print( 'Sorry, but only Python version >= 2.7 is supported!', file=sys.stderr )
    sys.exit( 1 )

from . import __version__ as version
__all__ = ['run']

def runInner():
    args = docopt( __doc__, version='FutoIn CID v{0}'.format(version) )

    if type(args) == str:
        print(args)
    else:
        if 'CID_COLOR' in os.environ:
            Coloring.enable(os.environ['CID_COLOR'] == 'yes')
        
        overrides = {}
        #---
        vcsArg = args.get('--vcsRepo', None)

        if vcsArg:
            try:
                (overrides['vcs'],
                overrides['vcsRepo']) = vcsArg.split(':', 1)
            except ValueError:
                raise RuntimeError('Invalid argument to --vcsRepo')
        #---
        rmsArg = args.get('--rmsRepo', None)

        if rmsArg:
            try:
                (overrides['rms'],
                overrides['rmsRepo']) = rmsArg.split(':', 1)
            except ValueError:
                raise RuntimeError('Invalid argument to --rmsRepo')
        overrides['rmsHash'] = args['--rmsHash']
        overrides['rmsPool'] = args['<rms_pool>']
        #---
        if args['ci_build'] :
            if 'vcs' in overrides:
                def_wc_dir = 'ci_build'
            else :
                def_wc_dir = os.path.join('..', 'ci_builds',
                                          os.path.basename(os.path.realpath('.')))
            def_wc_dir += '_' + args['<vcs_ref>']
        else :
            def_wc_dir = '.'
        overrides['wcDir'] = os.path.realpath(args['--wcDir'] or def_wc_dir)
        #--
        deploy_dir = args['--deployDir']
        overrides['deployDir'] = deploy_dir and os.path.realpath(deploy_dir) or None
        overrides['reDeploy'] = args['--redeploy'] and True or False

        if args['--build']:
            overrides['deployBuild'] = True

        if args['--debug']:
            overrides['debugBuild'] = True
        
        # enable vcsref & vcstag build by default
        if args['deploy'] and (args['vcsref'] or args['vcstag']):
            overrides['deployBuild'] = True

        #---
        overrides['vcsRef'] = args['<vcs_ref>']

        #---
        tool = args['<tool_name>']
        tool_ver = args['<tool_version>']
        overrides['tool'] = tool
        overrides['toolVer'] = tool_ver != '--' and tool_ver or None
        overrides['toolTest'] = (
            args['test'] or
            args['uninstall'] or
            args['describe'] or
            args['detect']
        )
        
        #---
        if args['--permissive']:
            overrides['permissiveChecks'] = True
        
        #---
        cit = CIDTool( overrides = overrides )
        
        if args['tool'] :
            if args['exec']:
                cit.tool_exec( tool, args['<tool_arg>'] )
            elif args['list']:
                cit.tool_list()
            elif args['detect']:
                cit.tool_detect()
            else:
                subcmds = [
                    'install',
                    'uninstall',
                    'update',
                    'test',
                    'env',
                    'prepare',
                    'build',
                    'check',
                    'package',
                    'migrate',
                    'describe',
                ]
                for cmd in subcmds:
                    if args[cmd]:
                        getattr( cit, 'tool_'+cmd )( tool )
                        break
                else:
                    raise RuntimeError( "Unknown Command" )
        elif args['vcs'] :
            if args['checkout']:
                cit.vcs_checkout( args['<vcs_ref>'] )
            elif args['commit']:
                cit.vcs_commit( args['<commit_msg>'], args['<commit_files>'] )
            elif args['branch']:
                cit.vcs_branch( args['<vcs_ref>'] )
            elif args['merge']:
                cit.vcs_merge( args['<vcs_ref>'], not args['--no-cleanup'] )
            elif args['delete']:
                cit.vcs_delete( args['<vcs_ref>'], args['--cacheDir'] )
            elif args['export']:
                cit.vcs_export( args['<vcs_ref>'], args['<dst_dir>'], args['--cacheDir'] )
            elif args['tags']:
                cit.vcs_tags( args['<tag_pattern>'], args['--cacheDir'] )
            elif args['branches']:
                cit.vcs_branches( args['<branch_pattern>'], args['--cacheDir'] )
            elif args['reset']:
                cit.vcs_reset()
            else:
                raise RuntimeError( "Not implemented yet." )
        elif args['init'] :
            cit.init_project( args['<project_name>'] )
        elif args['tag'] :
            cit.tag( args['<branch>'], args['<next_version>'] )
        elif args['prepare'] :
            cit.prepare( args['<vcs_ref>'] )
        elif args['build'] :
            cit.build()
        elif args['package']:
            cit.package()
        elif args['check'] :
            cit.check()
        elif args['promote'] :
            cit.promote( args['<package>'], args['<rms_pool>'] )
        elif args['deploy'] :
            if args['vcsref']:
                cit.deploy( 'vcsref', args['<vcs_ref>'] )
            elif args['vcstag']:
                cit.deploy( 'vcstag', args['<vcs_ref>'] )
            else :
                cit.deploy( 'rms', args['<rms_pool>'], args['<package>'] )
        elif args['migrate'] :
            cit.migrate()
        elif args['run'] :
            cit.run( args['<command>'], args['<command_arg>'] )
        elif args['ci_build'] :
            cit.ci_build( args['<vcs_ref>'], args['<rms_pool>'] )
        else:
            raise RuntimeError( "Unknown Command" )

def run():
    try:
        runInner()
    except Exception as e:
        print(file=sys.stderr)
        print(Coloring.error('ERROR: ' + str(e)), file=sys.stderr)
        print(file=sys.stderr)
        print(Coloring.warn(traceback.format_exc()), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt as e:
        print(file=sys.stderr)
        print(Coloring.error('Exit on user abort'), file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)
        