#!/usr/bin/env python
"""FutoIn Continuous Integration & Delivery Tool.

Usage:
    cid tag <branch> [<next_version>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid prepare [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid build [--debug]
    cid package
    cid check [--permissive]
    cid promote <package> <rms_pool> [--rmsRepo=<rms_repo>] [--rmsHash=<rms_hash>]
    cid deploy vcstag [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--redeploy] [--deployDir=<deploy_dir>]
    cid deploy vcsref <vcs_ref> [--vcsRepo=<vcs_repo>] [--redeploy] [--deployDir=<deploy_dir>]
    cid deploy [rms] <rms_pool> [<package>] [--rmsRepo=<rms_repo>] [--rmsHash=<rms_hash>] [--redeploy] [--deployDir=<deploy_dir>] [--build]
    cid run
    cid run <command> [<command_arg>...]
    cid ci_build <vcs_ref> <rms_pool> [--vcsRepo=<vcs_repo>] [--rmsRepo=<rms_repo>] [--permissive] [--debug]
    cid tool exec <tool_name> [-- <tool_arg>...]
    cid tool (install|uninstall|update|test|env) [<tool_name>]
    cid tool (prepare|build|check|package|migrate) <tool_name>
    cid tool list
    cid tool describe <tool_name>
    cid init [<project_name>] [--vcsRepo=<vcs_repo>] [--rmsRepo=<rms_repo>] [--permissive]

Options:
    -h --help                       Show this screen.
    --vcsRepo=<vcs_repo>              VCS repository URL in vcs_type:vcs_url format.
    --rmsRepo=<rms_repo>              RMS repository URL in rms_type:rms_url format.
    --wcDir=<wc_dir>                  Working copy directory (project root).
    --rmsHash=<rms_hash>              Package hash for validation in hash_type:value format.
    --deployDir=<deploy_dir>          Destination for deployment.
    --redeploy                      Force redeploy.
    --build                         Build during deploy.
    --permissive                    Ignore test failures.
    --debug                         Build in debug mode, if applicable.
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
    args = docopt( __doc__, version='FutoIn CIDTool v{0}'.format(version) )

    if type(args) == str:
        print(args)
    else:
        overrides = {}
        #---
        vcsArg = args.get('--vcsRepo', None)

        if vcsArg:
            (overrides['vcs'],
             overrides['vcsRepo']) = vcsArg.split(':', 1)
        #---
        rmsArg = args.get('--rmsRepo', None)

        if rmsArg:
            (overrides['rms'],
             overrides['rmsRepo']) = rmsArg.split(':', 1)
        overrides['rmsHash'] = args['--rmsHash']
        overrides['rmsPool'] = args['<rms_pool>']
        #---
        if args['ci_build'] :
            def_wc_dir = 'ci_build'
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
        
        #---
        overrides['vcsRef'] = args['<vcs_ref>']

        #---
        tool = args['<tool_name>']
        overrides['tool'] = tool
        overrides['toolTest'] = args['test'] or args['uninstall'] or args['describe']
        
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
                    print( "ERR: Unknown Command", file=sys.stderr )
                    sys.exit( 1 )
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
                overrides['deployBuild'] = True
                cit.deploy( 'vcsref', args['<vcs_ref>'] )
            elif args['vcstag']:
                overrides['deployBuild'] = True
                cit.deploy( 'vcstag', args['<vcs_ref>'] )
            else :
                cit.deploy( 'rms', args['<rms_pool>'], args['<package>'] )
        elif args['run'] :
            cit.run( args['<command>'], args['<command_arg>'] )
        elif args['ci_build'] :
            cit.ci_build( args['<vcs_ref>'], args['<rms_pool>'] )
        else:
            print( "ERR: Unknown Command", file=sys.stderr )
            sys.exit( 1 )

def run():
    try:
        runInner()
    except Exception as e:
        print(file=sys.stderr)
        print(Coloring.error('ERR: ' + str(e)), file=sys.stderr)
        print(file=sys.stderr)
        print(Coloring.warn(traceback.format_exc()), file=sys.stderr)