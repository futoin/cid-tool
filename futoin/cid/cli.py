#!/usr/bin/env python
"""FutoIn Continuous Integration & Delivery Tool.

Usage:
    cid tag <branch> [<next_version>] [--vcsRepo vcs_url] [--wcDir wc_dir]
    cid prepare [<vcs_ref>] [--vcsRepo vcs_url] [--wcDir wc_dir]
    cid build
    cid package
    cid check [--permissive]
    cid promote <package> <rms_pool> [--rmsRepo rms_url] [--rmsHash type_value]
    cid deploy vcstag [<vcs_ref>] [--vcsRepo vcs_url] [--redeploy] [--deployDir deploy_dir]    
    cid deploy vcsref <vcs_ref> [--vcsRepo vcs_url] [--redeploy] [--deployDir deploy_dir]    
    cid deploy [rms] <rms_pool> [<package>] [--rmsRepo rms_url] [--rmsHash type_value] [--redeploy] [--deployDir deploy_dir] [--build]
    cid run [<command>]
    cid ci_build <vcs_ref> <rms_pool> [--vcsRepo vcs_url] [--rmsRepo rms_url] [--permissive]
    cid tool exec <tool_name> [-- <tool_arg>...]
    cid tool (install|uninstall|update|test|env) [<tool_name>]

Options:
    --vcsRepo vcs_type:vcs_url
    --rmsRepo rms_type:rms_url
    --wcDir wc_dir
    --rmsHash hash_type:value
"""

from __future__ import print_function, absolute_import

from .cidtool import CIDTool

try:
    from docopt import docopt
except ImportError:
    # fallback to "hardcoded"
    from futoin.cid.contrib.docopt import docopt

import os, sys

if sys.version_info < (2,7):
    print( 'Sorry, but only Python version >= 2.7 is supported!' )
    sys.exit( 1 )

from . import __version__ as version
__all__ = ['run']

def run():
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
        
        #---
        overrides['vcsRef'] = args['<vcs_ref>']

        #---
        tool = args['<tool_name>']
        overrides['tool'] = tool
        overrides['toolTest'] = args['test'] or args['uninstall']
        
        #---
        if args['--permissive']:
            overrides['permissiveChecks'] = True
        
        #---
        cit = CIDTool( overrides = overrides )
        
        if args['tag'] :
            cit.tag( args['<branch>'], args['<next_version>'] )
        elif args['prepare'] :
            cit.prepare( args['<vcs_ref>'] )
        elif args['build'] :
            cit.build()
        elif args['package'] :
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
            cit.run( args['<command>'] or 'start' )
        elif args['ci_build'] :
            cit.ci_build( args['<vcs_ref>'], args['<rms_pool>'] )
        elif args['tool'] :
            if args['exec']:
                cit.tool_exec( tool, args['<tool_arg>'] )
            elif args['install']:
                cit.tool_install( tool )
            elif args['uninstall']:
                cit.tool_uninstall( tool )
            elif args['update']:
                cit.tool_update( tool )
            elif args['test']:
                cit.tool_test( tool )
            elif args['env']:
                cit.tool_env( tool )
            else:
                print( "Unknown Command" )
                sys.exit( 1 )
        else:
            print( "Unknown Command" )
            sys.exit( 1 )
