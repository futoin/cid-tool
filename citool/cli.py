#!/usr/bin/env python
"""FutoIn Continuous Integration Tool.

Usage:
    citool tag <branch> [<next_version>] [--vcsRepo vcs_url] [--wcDir wc_dir]
    citool prepare [<vcs_ref>] [--vcsRepo vcs_url] [--wcDir wc_dir]
    citool build
    citool package
    citool promote <package> <rms_pool> [--rmsRepo rms_url] [--rmsHash type_value]
    citool deploy <rms_pool> [<package>] [--rmsRepo rms_url] [--rmsHash type_value] [--redeploy] [--deployDir deploy_dir]
    citool run [<command>]
    citool ci_build <vcs_ref> <rms_pool> [--vcsRepo vcs_url] [--rmsRepo rms_url]
    citool tool exec <tool_name> [-- <tool_arg>...]
    citool tool (install|uninstall|update|test|env) [<tool_name>]

Options:
    --vcsRepo vcs_type:vcs_url
    --rmsRepo rms_type:rms_url
    --wcDir wc_dir
    --rmsHash hash_type:value
"""

from .citool import CITool
    
from docopt import docopt
import sys

def run():
    args = docopt( __doc__, version='FutoIn CITool v0.1' )

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
        #---
        overrides['wcDir'] = args['--wcDir'] or 'build'
        overrides['deployDir'] = args['--deployDir'] or None
        overrides['reDeploy'] = args['--redeploy'] and True or False
        
        #---
        overrides['vcsRef'] = args['<vcs_ref>']

        #---
        tool = args['<tool_name>']
        overrides['tool'] = tool
        overrides['toolTest'] = args['test'] or args['uninstall']
        
        #---
        cit = CITool( overrides = overrides )
        
        if args['tag'] :
            cit.tag( args['<branch>'], args['<next_version>'] )
        elif args['prepare'] :
            cit.prepare( args['<vcs_ref>'] )
        elif args['build'] :
            cit.build()
        elif args['package'] :
            cit.package()
        elif args['promote'] :
            cit.promote( args['<package>'], args['<rms_pool>'] )
        elif args['deploy'] :
            cit.deploy( args['<rms_pool>'], args['<package>'] )
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
