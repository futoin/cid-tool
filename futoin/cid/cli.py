#!/usr/bin/env python

#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""FutoIn Continuous Integration & Delivery Tool.

Usage:
    cid init [<project_name>] [--vcsRepo=<vcs_repo>] [--rmsRepo=<rms_repo>] [--permissive]
    cid tag <branch> [<next_version>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid prepare [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid build [--debug]
    cid package
    cid check [--permissive]
    cid promote <rms_pool> <packages>... [--rmsRepo=<rms_repo>]
    cid deploy setup [--deployDir=<deploy_dir>] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>] [--runtimeDir=<runtime_dir>] [--tmpDir=<tmp_dir>] [--user=<user>] [--group=<group>]
    cid deploy vcstag [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--redeploy] [--deployDir=<deploy_dir>] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>] [--runtimeDir=<runtime_dir>] [--tmpDir=<tmp_dir>] [--user=<user>] [--group=<group>]
    cid deploy vcsref <vcs_ref> [--vcsRepo=<vcs_repo>] [--redeploy] [--deployDir=<deploy_dir>] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>] [--runtimeDir=<runtime_dir>] [--tmpDir=<tmp_dir>] [--user=<user>] [--group=<group>]
    cid deploy rms <rms_pool> [<package>] [--rmsRepo=<rms_repo>] [--redeploy] [--deployDir=<deploy_dir>] [--build] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>] [--runtimeDir=<runtime_dir>] [--tmpDir=<tmp_dir>] [--user=<user>] [--group=<group>]
    cid deploy reset [<set_type>] [--deployDir=<deploy_dir>]
    cid deploy set tools <tools>... [--deployDir=<deploy_dir>]
    cid deploy set tooltune <tool> <tune>... [--deployDir=<deploy_dir>]
    cid deploy set action <name> <action>... [--deployDir=<deploy_dir>]
    cid deploy set persistent <path>... [--deployDir=<deploy_dir>]
    cid deploy set writable <path>... [--deployDir=<deploy_dir>]
    cid deploy set entrypoint <name> <tool> <entry_path> [<tune>...] [--deployDir=<deploy_dir>]
    cid deploy set env <variable> [<value>] [--deployDir=<deploy_dir>]
    cid deploy set webcfg <variable> [<value>] [--deployDir=<deploy_dir>]
    cid deploy set webmount <web_path> [<json>] [--deployDir=<deploy_dir>]
    cid migrate
    cid run
    cid run <command> [--] [<command_arg>...]
    cid ci_build <vcs_ref> [<rms_pool>] [--vcsRepo=<vcs_repo>] [--rmsRepo=<rms_repo>] [--permissive] [--debug] [--wcDir=<wc_dir>]
    cid tool exec <tool_name> [<tool_version>] [-- <tool_arg>...]
    cid tool envexec <tool_name> [<tool_version>] [-- <any_command>...]
    cid tool (install|uninstall|update|test|env) [<tool_name> [<tool_version>]]
    cid tool (prepare|build|check|package|migrate) <tool_name> [<tool_version>]
    cid tool list
    cid tool describe <tool_name>
    cid tool detect
    cid vcs checkout [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
    cid vcs commit <commit_msg> [<commit_files>...] [--wcDir=<wc_dir>]
    cid vcs merge <vcs_ref> [--no-cleanup] [--wcDir=<wc_dir>]
    cid vcs branch <vcs_ref> [--wcDir=<wc_dir>]
    cid vcs delete <vcs_ref> [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
    cid vcs export <vcs_ref> <dst_dir> [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
    cid vcs tags [<tag_pattern>] [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
    cid vcs branches [<branch_pattern>] [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
    cid vcs reset [--wcDir=<wc_dir>]
    cid vcs ismerged <vcs_ref> [--wcDir=<wc_dir>]
    cid vcs clean [--wcDir=<wc_dir>]
    cid rms list <rms_pool> [<package_pattern>] [--rmsRepo=<rms_repo>]
    cid rms retrieve <rms_pool> <packages>... [--rmsRepo=<rms_repo>]
    cid rms pool create <rms_pool> [--rmsRepo=<rms_repo>]
    cid rms pool list [--rmsRepo=<rms_repo>]
    cid devserve [--wcDir=<wc_dir>] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>]
    cid service master [--deployDir=<deploy_dir>] [--adapt] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>] [--user=<user>] [--group=<group>]
    cid service list [--deployDir=<deploy_dir>] [--adapt] [--limit-memory=<mem_limit>] [--limit-cpus=<cpu_count>] [--listen-addr=<address>] [--user=<user>] [--group=<group>]
    cid service exec <entry_point> <instance_id> [--deployDir=<deploy_dir>]
    cid service stop <entry_point> <instance_id> <pid> [--deployDir=<deploy_dir>]
    cid service reload <entry_point> <instance_id> <pid> [--deployDir=<deploy_dir>]
    cid sudoers [<sudo_entity>] [--skip-key-management]
    cid build-dep [<build_dep>...]
    

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
    --adapt                         Re-balance available resources before execution.
    --limit-memory=<mem_limit>|auto Limit allocated memory (B, K, M or G postfix is required).
    --limit-cpus=<cpu_count>|auto   Limit CPU cores (affects instance count).
    --listen-addr=<address>|auto    Address to bind services, all by default.
    --runtimeDir=<runtime_dir>|auto Directory for runtime data (sockets, configs, etc.).
    --tmpDir=<tmp_dir>|auto         Directory for temporary data.
    --user=<user>|auto              User name to use for service execution.
    --group=<group>|auto            Group name to use for service execution.
    --skip-key-management           Enforce better security forbidding signing key management.
    <rms_pool>                      Either "dst_pool" or  "src_pool:dst_pool" for promotion.
    <packages>                      Either "local/file" or "remote_file" or "<package>@<hash>".
    <sudo_entity>                   Username or group to be put in generated sudoers as is.
"""

from __future__ import print_function

from .cidtool import CIDTool
from .coloring import Coloring
from . import __version__ as version

try:
    from docopt import docopt
except ImportError:
    # fallback to "hardcoded"
    from futoin.cid.contrib.docopt import docopt

import os
import sys

if sys.version_info < (2, 7):
    print('Sorry, but only Python version >= 2.7 is supported!', file=sys.stderr)
    sys.exit(1)

__all__ = ['run']


def runInner():
    args = docopt(__doc__, version='FutoIn CID v{0}'.format(version))

    if type(args) == str:
        print(args)
    else:
        ospath = os.path

        if 'CID_COLOR' in os.environ:
            Coloring.enable(os.environ['CID_COLOR'] == 'yes')

        overrides = {}
        # ---
        vcsArg = args.get('--vcsRepo', None)

        if vcsArg:
            try:
                (overrides['vcs'],
                 overrides['vcsRepo']) = vcsArg.split(':', 1)
            except ValueError:
                raise RuntimeError('Invalid argument to --vcsRepo')
        # ---
        rmsArg = args.get('--rmsRepo', None)

        if rmsArg:
            try:
                (overrides['rms'],
                 overrides['rmsRepo']) = rmsArg.split(':', 1)
            except ValueError:
                raise RuntimeError('Invalid argument to --rmsRepo')
        overrides['rmsPool'] = args['<rms_pool>']

        # ---
        if args['ci_build']:
            if 'vcs' in overrides:
                def_wc_dir = 'ci_build'
            else:
                def_wc_dir = ospath.join('..', 'ci_builds',
                                         ospath.basename(ospath.realpath('.')))
            def_wc_dir += '_' + args['<vcs_ref>']
        else:
            def_wc_dir = '.'
        overrides['wcDir'] = ospath.realpath(args['--wcDir'] or def_wc_dir)
        # --
        deploy_dir = args['--deployDir']

        if deploy_dir:
            overrides['deployDir'] = ospath.realpath(deploy_dir)
        elif args['deploy'] or args['service']:
            overrides['deployDir'] = ospath.realpath('.')

        overrides['reDeploy'] = args['--redeploy'] and True or False

        if args['--build']:
            overrides['deployBuild'] = True

        if args['--debug']:
            overrides['debugBuild'] = True

        # enable vcsref & vcstag build by default
        if args['deploy'] and (args['vcsref'] or args['vcstag']):
            overrides['deployBuild'] = True

        # ---
        overrides['vcsRef'] = args['<vcs_ref>']

        # ---
        tool = args['<tool_name>']
        tool_ver = args['<tool_version>']
        overrides['tool'] = tool
        overrides['toolVer'] = tool_ver != '--' and tool_ver or None
        overrides['toolTest'] = (
            args['tool'] and (
                args['test'] or
                args['uninstall'] or
                args['describe'] or
                args['detect'] or
                args['env']
            ) or
            (args['deploy'] and args['set']) or
            args['tag']
        )

        overrides['toolDetect'] = not (args['service'] and args['master'])

        # ---
        if args['--permissive']:
            overrides['permissiveChecks'] = True

        # ---
        cache_dir = args['--cacheDir']

        if cache_dir:
            cache_dir = ospath.realpath(cache_dir)

        # ---
        deploy = overrides.setdefault('_deploy', {})
        deploy['maxTotalMemory'] = args['--limit-memory']
        deploy['maxCpuCount'] = args['--limit-cpus']
        deploy['listenAddress'] = args['--listen-addr']
        deploy['runtimeDir'] = args['--runtimeDir']
        deploy['tmpDir'] = args['--tmpDir']
        deploy['user'] = args['--user']
        deploy['group'] = args['--group']
        overrides['adaptDeploy'] = args['--adapt'] or args['devserve']

        if deploy['maxCpuCount']:
            try:
                deploy['maxCpuCount'] = int(deploy['maxCpuCount'])
            except ValueError:
                pass

        # ---
        cit = CIDTool(overrides=overrides)

        if args['tool']:
            if args['exec']:
                cit.tool_exec(tool, args['<tool_arg>'])
            if args['envexec']:
                cit.tool_envexec(tool, args['<any_command>'])
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
                        getattr(cit, 'tool_' + cmd)(tool)
                        break
                else:
                    raise RuntimeError("Unknown Command")
        elif args['vcs']:
            if args['checkout']:
                cit.vcs_checkout(args['<vcs_ref>'])
            elif args['commit']:
                cit.vcs_commit(args['<commit_msg>'], args['<commit_files>'])
            elif args['branch']:
                cit.vcs_branch(args['<vcs_ref>'])
            elif args['merge']:
                cit.vcs_merge(args['<vcs_ref>'], not args['--no-cleanup'])
            elif args['delete']:
                cit.vcs_delete(args['<vcs_ref>'], cache_dir)
            elif args['export']:
                dst_dir = ospath.realpath(args['<dst_dir>'])
                cit.vcs_export(args['<vcs_ref>'], dst_dir, cache_dir)
            elif args['tags']:
                cit.vcs_tags(args['<tag_pattern>'], cache_dir)
            elif args['branches']:
                cit.vcs_branches(args['<branch_pattern>'], cache_dir)
            elif args['reset']:
                cit.vcs_reset()
            elif args['ismerged']:
                cit.vcs_ismerged(args['<vcs_ref>'])
            elif args['clean']:
                cit.vcs_clean()
            else:
                raise RuntimeError("Not implemented yet.")
        elif args['rms'] and not args['deploy']:
            if args['pool']:
                if args['create']:
                    cit.rms_pool_create(args['<rms_pool>'])
                elif args['list']:
                    cit.rms_pool_list()
                else:
                    raise RuntimeError("Not implemented yet.")
            elif args['list']:
                cit.rms_list(args['<rms_pool>'], args['<package_pattern>'])
            elif args['retrieve']:
                cit.rms_retrieve(args['<rms_pool>'], args['<packages>'])
            else:
                raise RuntimeError("Not implemented yet.")
        elif args['deploy']:
            if args['rms']:
                cit.deploy('rms', args['<rms_pool>'], args['<package>'])
            elif args['vcsref']:
                cit.deploy('vcsref', args['<vcs_ref>'])
            elif args['vcstag']:
                cit.deploy('vcstag', args['<vcs_ref>'])
            elif args['setup']:
                cit.deploy('setup')
            elif args['set']:
                if args['action']:
                    cit.deploy_set('action', args['<name>'], args['<action>'])
                elif args['persistent']:
                    cit.deploy_set('persistent', args['<path>'])
                elif args['writable']:
                    cit.deploy_set('writable', args['<path>'])
                elif args['entrypoint']:
                    cit.deploy_set('entrypoint', args['<name>'], args['<tool>'],
                                   args['<entry_path>'], args['<tune>'])
                elif args['env']:
                    cit.deploy_set('env', args['<variable>'], args['<value>'])
                elif args['webcfg']:
                    cit.deploy_set(
                        'webcfg', args['<variable>'], args['<value>'])
                elif args['webmount']:
                    cit.deploy_set(
                        'webmount', args['<web_path>'], args['<json>'])
                elif args['tools']:
                    cit.deploy_set('tools', args['<tools>'])
                elif args['tooltune']:
                    cit.deploy_set('tooltune', args['<tool>'], args['<tune>'])
                else:
                    raise RuntimeError("Not implemented yet.")
            elif args['reset']:
                cit.deploy_reset(args['<set_type>'])
            else:
                raise RuntimeError("Not implemented yet.")
        elif args['service']:
            if args['master']:
                cit.service_master()
            elif args['list']:
                cit.service_list()
            elif args['exec']:
                cit.service_exec(args['<entry_point>'], args['<instance_id>'])
            elif args['stop']:
                cit.service_stop(args['<entry_point>'],
                                 args['<instance_id>'], args['<pid>'])
            elif args['reload']:
                cit.service_reload(args['<entry_point>'],
                                   args['<instance_id>'], args['<pid>'])
            else:
                raise RuntimeError("Not implemented yet.")
        elif args['init']:
            cit.init_project(args['<project_name>'])
        elif args['tag']:
            cit.tag(args['<branch>'], args['<next_version>'])
        elif args['prepare']:
            cit.prepare(args['<vcs_ref>'])
        elif args['build']:
            cit.build()
        elif args['package']:
            cit.package()
        elif args['check']:
            cit.check()
        elif args['promote']:
            cit.promote(args['<rms_pool>'], args['<packages>'])
        elif args['migrate']:
            cit.migrate()
        elif args['run']:
            cit.run(args['<command>'], args['<command_arg>'])
        elif args['ci_build']:
            cit.ci_build(args['<vcs_ref>'], args['<rms_pool>'])
        elif args['devserve']:
            cit.devserve()
        elif args['sudoers']:
            cit.sudoers(args['<sudo_entity>'], args['--skip-key-management'])
        elif args['build-dep']:
            cit.builddep(args['<build_dep>'])
        else:
            raise RuntimeError("Unknown Command")


def run():
    try:
        runInner()
    except Exception as e:
        print(file=sys.stderr)
        print(Coloring.error('ERROR: ' + str(e)), file=sys.stderr)
        print(file=sys.stderr)
        import traceback
        print(Coloring.warn(traceback.format_exc()), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt as e:
        print(file=sys.stderr)
        print(Coloring.error('Exit on user abort'), file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)
