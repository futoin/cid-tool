#!/usr/bin/python
"""FutoIn Continuous Integration Tool.

Usage:
    citool tag <branch> [<next_version>] [--vcsRepo vcs_url]
    citool prepare [<vcs_ref>] [--vcsRepo vcs_url]
    citool build
    citool package
    citool promote <package> <rms_pool> [--rmsRepo rms_url] [--hash type_value]
    citool deploy <package> <location> [--rmsRepo rms_url] [--hash type_value]
    citool run [<package>]
    citool ci_build <vcs_ref> <rms_pool> [--vcsRepo vcs_url] [--rmsRepo rms_url]

Options:
    --vcsRepo vcs_type:vcs_url
    --rmsRepo rms_type:rms_url
    --hash has_type:value
"""

from citool import CITool
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
            cit.deploy( args['<package>'], args['<location>'] )
        elif args['run'] :
            cit.run( args['<package>'] )
        elif args['ci_build'] :
            cit.ci_build( args['<vcs_ref>'], args['<rms_pool>'] )
        else:
            print "Unknown Command"
            sys.exit( 1 )
