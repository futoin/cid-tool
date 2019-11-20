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


from __future__ import print_function

from collections import OrderedDict

from .mixins.data import DataSlots
from .mixins.tool import ToolMixIn
from .mixins.lock import LockMixIn
from .mixins.config import ConfigMixIn
from .mixins.deploy import DeployMixIn
from .mixins.service import ServiceMixIn
from .mixins.log import LogMixIn


from .coloring import Coloring

from .vcstool import VcsTool
from .rmstool import RmsTool
from .buildtool import BuildTool
from .testtool import TestTool
from .migrationtool import MigrationTool
from .runtimetool import RuntimeTool


__all__ = ['CIDTool']


def cid_action(f):
    def custom_f(self, *args, **kwargs):
        self._processWcDir()
        config = self._config

        try:
            fn = f.func_name
        except AttributeError:
            fn = f.__name__

        actions = config.get('actions', {})

        if fn in actions:
            self._call_actions(fn, actions, args, f)
        else:
            f(self, *args, **kwargs)
    return custom_f


# =============================================================================
class CIDTool(LogMixIn, ConfigMixIn, LockMixIn, ServiceMixIn, DeployMixIn, ToolMixIn, DataSlots):
    __slots__ = ()

    def __init__(self, overrides, init_conf=True):
        super(CIDTool, self).__init__()
        self._overrides = overrides
        if init_conf:
            self._initConfig(True)

    def _call_actions(self, name, actions, args, orig_action=False, filt_args=None):
        act = actions[name]
        act = self._configutil.listify(act)

        if filt_args is None:
            # replace possible None with empty strings
            filt_args = [x or '' for x in args]

            # trim only ending
            while len(filt_args) and not len(filt_args[-1]):
                filt_args.pop()

        for cmd in act:
            if cmd.startswith('@cid'):
                cmd = self._ext.shlex.split(cmd)
                self._executil.callExternal(
                    [self._sys.executable, '-mfutoin.cid'] + cmd[1:] + filt_args,
                    user_interaction=True)
            elif cmd.startswith('@cte'):
                cmd = self._ext.shlex.split(cmd)
                self._executil.callExternal(
                    [self._sys.executable, '-mfutoin.cid.cte'] +
                    cmd[1:] + filt_args,
                    user_interaction=True)
            elif cmd == '@default':
                if orig_action:
                    orig_action(self, *args)
                else:
                    self._errorExit(
                        '@default is not allowed for "[0}"'.format(name))
            elif cmd in actions:
                self._call_actions(cmd, actions, args, False, filt_args)
            else:
                if filt_args:
                    cmd = '{0} {1}'.format(
                        cmd, self._ext.subprocess.list2cmdline(filt_args))
                self._executil.callExternal(
                    ['sh', '-c', cmd], user_interaction=True)

    @cid_action
    def tag(self, branch, next_version=None):
        # implciit in @cid_action
        # self._processWcDir()

        mode = 'patch'

        if next_version in ['patch', 'minor', 'major']:
            mode = next_version
            next_version = None

        if next_version and not self._ext.re.match('^[0-9]+\.[0-9]+\.[0-9]+$', next_version):
            self._errorExit('Valid version format: x.y.z')

        config = self._config
        vcstool = self._getVcsTool()
        vcsrepo = config['vcsRepo']

        # ---
        self._info(
            'Getting source branch {0} from {1}'.format(branch, vcsrepo))
        vcstool.vcsCheckout(config, branch)
        self._initConfig()
        config = self._config

        if 'name' not in config:
            self._errorExit('Failed to detect project "name"')

        # Set new version
        if next_version is None:
            if 'version' in config:
                next_version = config['version']
            else:
                self._errorExit('current project version is unknown')

            next_version = next_version.split('.')
            next_version += ['0'] * 3
            del next_version[3:]

            if mode == 'patch':
                next_version[2] = str(int(next_version[2]) + 1)
            elif mode == 'minor':
                next_version[1] = str(int(next_version[1]) + 1)
                next_version[2] = '0'
            elif mode == 'major':
                next_version[0] = str(int(next_version[0]) + 1)
                next_version[1] = '0'
                next_version[2] = '0'

            next_version = '.'.join(next_version)

        config['version'] = next_version

        # ---
        self._info('Updating files for release')
        to_commit = []
        self._forEachTool(
            lambda config, t: to_commit.extend(
                t.updateProjectConfig(config, {'version': next_version})
            )
        )

        # ---
        if to_commit:
            self._info('Committing updated files')
            message = "Updated for release %s %s" % (
                config['name'], config['version'])
            vcstool.vcsCommit(config, message, to_commit)
        else:
            self._info('Nothing to commit')

        # ---
        tag = "v%s" % next_version
        self._info('Creating a tag {0}'.format(tag))
        message = "Release %s %s" % (config['name'], config['version'])
        vcstool.vcsTag(config, tag, message)

        # ---
        self._info('Pushing changes to {0}'.format(vcsrepo))
        vcstool.vcsPush(config, [branch, tag])

    @cid_action
    def prepare(self, vcs_ref=None):
        # implciit in @cid_action
        # self._processWcDir()

        config = self._config

        # make a clean checkout
        if vcs_ref:
            vcstool = self._getVcsTool()

            self._info('Getting source ref {0} from {1}'.format(
                vcs_ref, config['vcsRepo']))
            vcstool.vcsCheckout(config, vcs_ref)
            self._initConfig()
            self.prepare()
            return

        # --
        self._info('Running "prepare" in tools')
        self._forEachTool(
            lambda config, t: t.onPrepare(config),
            base=BuildTool
        )

    @cid_action
    def build(self):
        # implciit in @cid_action
        # self._processWcDir()

        self._info('Running "build" in tools')
        self._forEachTool(
            lambda config, t: t.onBuild(config),
            base=BuildTool
        )

    @cid_action
    def package(self):
        # implciit in @cid_action
        # self._processWcDir()

        # ---
        self._info('Running "package" in tools')
        self._forEachTool(
            lambda config, t: t.onPackage(config),
            base=BuildTool
        )

        # ---
        os = self._os
        ospath = self._ospath
        pathutil = self._pathutil
        fnmatch = self._ext.fnmatch
        config = self._config
        package_files = config.get('packageFiles', None)

        if package_files is not None:
            self._info(
                'Found binary artifacts from tools: {0}'.format(package_files))
            self._lastPackages = package_files
            return

        # ---
        try:
            package_content = config['package']
            try:
                package_content.index(self._FUTOIN_JSON)
            except ValueError:
                package_content.append(self._FUTOIN_JSON)

        except KeyError:
            package_content = set(os.listdir('.'))
            # TODO: make it more extensible
            package_content -= set(
                fnmatch.filter(package_content, '.git*') +
                fnmatch.filter(package_content, '.hg*') +
                ['.svn']
            )
            package_content = list(package_content)

        if type(package_content) != list:
            package_content = [package_content]

        package_content.sort()

        self._info('Generating package from {0}'.format(package_content))

        # ---
        if config.get('packageChecksums', True):
            self._info('Generating checksums')
            checksums_file = '.package.checksums'

            checksums = []
            cs_files = []

            for pkg_item in package_content:
                if ospath.isfile(pkg_item):
                    cs_files.append(pkg_item)

                if ospath.isdir(pkg_item):
                    for (path, dirs, files) in os.walk(pkg_item):
                        for f in sorted(files):
                            f = pathutil.safeJoin(path, f)
                            cs_files.append(f)

            hashlib = self._ext.hashlib

            for cf in cs_files:
                hasher = hashlib.sha512()

                with open(cf, 'rb') as f_in:
                    for chunk in iter(lambda: f_in.read(65536), b""):
                        hasher.update(chunk)

                checksums.append("{0}  {1}".format(hasher.hexdigest(), cf))

            checksums.append('')

            with open(checksums_file, 'w') as f_out:
                f_out.write("\n".join(checksums))

            try:
                package_content.index('.')
            except ValueError:
                package_content.append(checksums_file)

        # ---
        buildTimestamp = self._ext.datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
        name = config.get('name', 'UNKNOWN').split('/')[-1]
        version = config.get('version', 'UNKNOWN')
        vcs_ref = config.get('vcsRef', None)

        # Note: unless run in clean ci_build process,
        # all builds must be treated as snapshots/CI builds
        if vcs_ref == 'v' + version:
            package_name = '{0}-{1}-{2}'.format(
                name, version, buildTimestamp)
        else:
            vcs_ref = 'UNKNOWN'

            if config.get('vcs', None):
                try:
                    vcstool = self._getVcsTool()
                    vcs_ref = vcstool.vcsGetRevision(config)
                except self._ext.subprocess.CalledProcessError as e:
                    if config.get('vcsRepo', None):
                        raise e

            package_name = '{0}-CI-{1}-{2}-{3}'.format(
                name, version, buildTimestamp, vcs_ref)

        if 'target' in config:
            package_name += '-{0}'.format(config['target'])

        tar_tool, compress_flag, package_ext = self._getTarTool()

        package_file = package_name + package_ext
        self._info('Creating package {0}'.format(package_file))

        tar_args = ['c{0}f'.format(compress_flag),
                    package_file,
                    '--transform=s,^,{0}/,'.format(package_name),
                    '--exclude=' + package_file,
                    '--exclude=.git*',
                    '--exclude=.hg*',
                    '--exclude=.svn'] + package_content
        tar_tool.onExec(config['env'], tar_args, False)
        # note, no --exclude-vcs
        self._lastPackages = [package_file]

    @cid_action
    def check(self):
        # implciit in @cid_action
        # self._processWcDir()

        self._info('Running "check" in tools')
        self._forEachTool(
            lambda config, t: t.onCheck(config),
            allow_failure=self._config.get('permissiveChecks', False),
            base=TestTool
        )

    @cid_action
    def promote(self, rms_pool, packages):
        # implciit in @cid_action
        # self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        pools = rms_pool.split(':', 1)

        if len(pools) == 2:
            self._info('Promoting from {0} to {1} pool: {2}'.format(
                pools[0], pools[1], ', '.join(packages)))
            packages = rmstool.rmsProcessChecksums(config, pools[0], packages)
            rmstool.rmsPromote(config, pools[0], pools[1], packages)
        else:
            self._info('Promoting to {0} pool: {1}'.format(
                rms_pool, ', '.join(packages)))
            rmstool.rmsUpload(config, rms_pool, packages)

    @cid_action
    def migrate(self):
        # implciit in @cid_action
        # self._processWcDir()

        self._info('Running "migrate" in tools')
        self._forEachTool(
            lambda config, t: t.onMigrate(config),
            base=MigrationTool
        )

    def deploy(self, mode, p1=None, p2=None):
        self._processDeployDir()

        self._deployLock()

        try:
            if mode == 'rms':
                self._rms_deploy(p1, p2)
            elif mode == 'vcsref':
                self._vcsref_deploy(p1)
            elif mode == 'vcstag':
                self._vcstag_deploy(p1)
            elif mode == 'setup':
                self._deploy_setup()
            else:
                self._errorExit('Not supported deploy mode: ' + mode)
        finally:
            self._deployUnlock()

    def deploy_set(self, action, *args):
        self._processDeployDir()

        member = '_deploy_set_{0}'.format(action)
        getattr(self, member)(*args)

        self._deployLock()

        try:
            self._writeDeployConfig()
        finally:
            self._deployUnlock()

    def deploy_reset(self, action):
        self._processDeployDir()

        if action:
            actions = [action]
        else:
            actions = [
                'tools',
                'tooltune',
                'action',
                'persistent',
                'writable',
                'entrypoint',
                'env',
                'webcfg',
                # 'webmount',
            ]

        for action in actions:
            member = '_deploy_reset_{0}'.format(action)
            getattr(self, member)()

        self._deployLock()

        try:
            self._writeDeployConfig()
        finally:
            self._deployUnlock()

    def run(self, command, args):
        self._processWcDir()

        os = self._os
        config = self._config
        entry_points = config.get('entryPoints', {})
        actions = config.get('actions', {})
        args = args or []

        if command:
            if command in entry_points:
                ep = entry_points[command]

                # Do stuff required to get the tool ready
                tool = ep['tool']
                self._overrides['tool'] = tool
                self._initConfig()

                #
                config = self._config
                t = self._getTool(tool)

                if isinstance(t, RuntimeTool):
                    svc = self._ext.copy.deepcopy(ep)
                    svc['name'] = command
                    svc['instanceId'] = 0
                    svc.setdefault('tune', {})

                    runtime_dir = self._ext.tempfile.mkdtemp(
                        prefix='futoin-cid-run')

                    t.onPreConfigure(config, runtime_dir, svc, svc['tune'])
                    t.onRun(config, svc, args)
                else:
                    self._errorExit(
                        'Tool "{0}" for "{1}" does not support "run" command'.format(tool, command))

            elif command in actions:
                self._call_actions(command, actions, args)
            else:
                self._errorExit(
                    'Unknown "{0}" action or entry point'.format(command))
        else:
            for cmd in entry_points:
                pid = os.fork()

                if not pid:
                    os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
                    self.run(cmd, None)

            i = len(entry_points)

            while i > 0:
                os.wait()
                i -= 1

    def ci_build(self, vcs_ref, rms_pool):
        self._initConfig()

        os = self._os
        config = self._config
        wcDir = config['wcDir']

        if self._ospath.exists(wcDir) and wcDir != os.getcwd():
            try:
                dst = '{0}.bak{1}'.format(wcDir, int(self._ext.time.time()))
                self._infoLabel('Renaming: ', '{0} to {1}'.format(wcDir, dst))
                os.rename(wcDir, dst)
            except OSError:
                self._pathutil.rmTree(wcDir)

        # Make sure to keep VCS info when switch to another location
        # for checkout.
        # ---
        if 'vcs' in config:
            self._getVcsTool()

            for cv in ['vcs', 'vcsRepo']:
                self._overrides[cv] = config[cv]
        # ---

        self._processWcDir()

        self._lastPackages = None
        self.prepare(vcs_ref)
        self.build()
        self.package()
        self.check()

        if rms_pool and self._lastPackages:
            self.promote(rms_pool, self._lastPackages)

    def tool_exec(self, tool, args):
        self._processWcDir()
        t = self._getTool(tool)
        t.onExec(self._env, args)

    def tool_envexec(self, tool, command):
        self._processWcDir()
        self._executil.callInteractive(command, search_path=True)

    def tool_install(self, tool):
        self._processWcDir()

        if self._detect.isDisabledToolsSetup(self._env):
            self._errorExit(
                'environment requires external installation of tools')

        if tool:
            tools = [tool]
        else:
            tools = self._config['toolOrder']

        env = self._env

        self._globalLock()

        for tool in tools:
            t = self._getTool(tool)
            t.requireInstalled(env)

        self._globalUnlock()

    def tool_uninstall(self, tool):
        self._processWcDir()

        if self._detect.isDisabledToolsSetup(self._env):
            self._errorExit(
                'environment requires external management of tools')

        if tool:
            tools = [tool]
        else:
            tools = reversed(self._config['toolOrder'])

        env = self._env

        self._globalLock()

        for tool in tools:
            t = self._getTool(tool)
            if t.isInstalled(env):
                t.uninstallTool(env)

        self._globalUnlock()

    def tool_update(self, tool):
        self._processWcDir()

        if self._detect.isDisabledToolsSetup(self._env):
            self._errorExit(
                'environment requires external management of tools')

        if tool:
            tools = [tool]
        else:
            tools = self._config['toolOrder']

        env = self._env

        self._globalLock()

        for tool in tools:
            t = self._getTool(tool)
            t.updateTool(env)

        self._globalUnlock()

    def tool_test(self, tool):
        self._processWcDir()

        if tool:
            tools = [tool]
        else:
            tools = self._config['toolOrder']

        env = self._env

        for tool in tools:
            t = self._getTool(tool)

            if not t.isInstalled(env):
                ver = env.get(tool + 'Ver', None)

                if ver:
                    self._errorExit(
                        "Tool '{0}' version '{1}' is missing".format(tool, ver))
                else:
                    self._errorExit("Tool '{0}' is missing".format(tool))

    def tool_env(self, tool):
        self.tool_test(tool)

        if tool:
            tools = [tool]
        else:
            tools = self._config['toolOrder']

        res = dict(self._environ)
        env = self._env

        # remove unchanged vars
        for k, v in self._origEnv().items():
            if res.get(k, None) == v:
                del res[k]

        for tool in tools:
            self._getTool(tool).exportEnv(env, res)

        for k, v in sorted(res.items()):
            if type(v) == type(''):
                v = v.replace("'", "\\'").replace('\\', '\\\\')
            elif not v:
                v = ''
            print("{0}='{1}'".format(k, v))

    def _tool_cmd(self, tool, base, method):
        self._processWcDir()

        config = self._config
        t = self._getTool(tool)

        if isinstance(t, base):
            t.loadConfig(config)  # see self._initTools()
            getattr(t, method)(config)
        else:
            self._errorExit(
                '{0} tool does not support {1}'.format(tool, method))

    def tool_prepare(self, tool):
        self._tool_cmd(tool, BuildTool, 'onPrepare')

    def tool_build(self, tool):
        self._tool_cmd(tool, BuildTool, 'onBuild')

    def tool_check(self, tool):
        self._tool_cmd(tool, TestTool, 'onCheck')

    def tool_package(self, tool):
        self._tool_cmd(tool, BuildTool, 'onPackage')

        package_files = self._config.get('packageFiles', None)

        if package_files is not None:
            self._info('Package files: {0}'.format(package_files))

    def tool_migrate(self, tool):
        self._tool_cmd(tool, MigrationTool, 'onMigrate')

    def tool_list(self):
        print("List of tools supported by CID:")
        for k in sorted(self._getKnownTools()):
            t = self._getTool(k)
            doc = t.__doc__.strip() or Coloring.warn('!! Missing documentation.')
            doc = doc.split("\n")[0]
            print(Coloring.infoLabel("  * " + k + ': ') + Coloring.info(doc))
        print('End.')

    def tool_describe(self, tool):
        t = self._getTool(tool)

        print(Coloring.infoLabel('* Tool: ') + Coloring.warn(tool))

        auto_detect = t.autoDetectFiles()
        if auto_detect:
            auto_detect = self._configutil.listify(auto_detect)
            print(Coloring.infoLabel('* Auto-detection (files): ') +
                  ', '.join(auto_detect))

        if isinstance(t, VcsTool):
            print(Coloring.infoLabel('* Auto-detected, if set as VCS '))

        if isinstance(t, RmsTool):
            print(Coloring.infoLabel('* Auto-detected, if set as RMS '))

        env_vars = t.envNames()
        if env_vars:
            print(Coloring.infoLabel(
                '* Environment variables: ') + ', '.join(env_vars))

        deps = t.getDeps()
        if deps:
            print(Coloring.infoLabel('* Dependencies: ') + ', '.join(deps))

        rdeps = t.getPostDeps()
        if rdeps:
            print(Coloring.infoLabel('* Reverse dependencies: ') + ', '.join(rdeps))

        order = t.getOrder()
        if order:
            print(Coloring.infoLabel('* Order shift: ') + str(order))

        print()
        doc = t.__doc__.strip() or Coloring.warn('!! Missing documentation.')
        print(Coloring.info(doc))
        print()

    def tool_detect(self):
        self._processWcDir()

        config = self._config
        env = config['env']

        for t in config['toolOrder']:
            ver = env.get(t + 'Ver', None)

            if ver:
                print("{0}={1}".format(t, ver))
            else:
                print(t)

    def init_project(self, project_name):
        self._processWcDir()
        ospath = self._ospath

        if ospath.exists(self._FUTOIN_JSON):
            self._errorExit('futoin.json already exists in project root')

        config = self._config
        new_config = self._exportConfig(config)

        if project_name:
            new_config['name'] = project_name
        elif 'name' not in config:
            new_config['name'] = ospath.basename(config['wcDir'])

        self._pathutil.writeJSONConfig(self._FUTOIN_JSON, new_config)

    def vcs_checkout(self, vcs_ref):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Getting source ref {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsCheckout(config, vcs_ref)

    def vcs_commit(self, msg, files):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        if files:
            self._info('Committing: ' + ', '.join(files))
        else:
            self._info('Committing updated files')
        vcstool.vcsCommit(config, msg, files)

        self._info('Pushing changes to {0}'.format(config['vcsRepo']))
        vcstool.vcsPush(config, None)

    def vcs_branch(self, vcs_ref):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Creating new branch {0} in {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsBranch(config, vcs_ref)

    def vcs_merge(self, vcs_ref, cleanup=True):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Merging branch {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsMerge(config, vcs_ref, cleanup)

    def vcs_delete(self, vcs_ref, vcs_cache_dir):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Deleting branch {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsDelete(config, vcs_cache_dir, vcs_ref)

    def vcs_export(self, vcs_ref, dst_path, vcs_cache_dir):
        os = self._os

        if self._ospath.exists(dst_path):
            if os.listdir(dst_path):
                self._errorExit(
                    'Destination directory {0} exists and is not empty'.format(dst_path))
        else:
            os.makedirs(dst_path)

        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Export ref {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsExport(config, vcs_cache_dir, vcs_ref, dst_path)

    def vcs_tags(self, tag_hint, vcs_cache_dir):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        tag_list = vcstool.vcsListTags(config, vcs_cache_dir, tag_hint)

        if tag_hint:
            tag_list = self._ext.fnmatch.filter(tag_list, tag_hint)

        self._versionutil.sort(tag_list)

        print("\n".join(tag_list))

    def vcs_branches(self, branch_hint, vcs_cache_dir):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        branch_list = vcstool.vcsListBranches(
            config, vcs_cache_dir, branch_hint)

        if branch_hint:
            branch_list = self._ext.fnmatch.filter(branch_list, branch_hint)

        self._versionutil.sort(branch_list)

        print("\n".join(branch_list))

    def vcs_reset(self):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Reverting all local changes')
        vcstool.vcsRevert(config)

    def vcs_ismerged(self, vcs_ref):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        if vcstool.vcsIsMerged(config, vcs_ref):
            self._info('Branch {0} is merged'.format(vcs_ref))
        else:
            self._info('Branch {0} is NOT merged'.format(vcs_ref))
            self._sys.exit(1)

    def vcs_clean(self):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Removing all unversioned items.')
        vcstool.vcsClean(config)

    def rms_list(self, rms_pool, package_pattern):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        package_list = rmstool.rmsGetList(config, rms_pool, package_pattern)

        if package_pattern:
            package_list = self._ext.fnmatch.filter(
                package_list, package_pattern)

        self._versionutil.sort(package_list)

        print("\n".join(package_list))

    def rms_retrieve(self, rms_pool, package_list):
        self._processWcDir()

        ospath = self._ospath
        config = self._config
        rmstool = self._getRmsTool()

        self._info('Retrieving packages from RMS...')

        for p in package_list:
            p = ospath.basename(p).split('@', 1)[0]

            if ospath.exists(p):
                self._errorExit('File already exists: {0}'.format(p))

        package_list = rmstool.rmsProcessChecksums(
            config, rms_pool, package_list)
        rmstool.rmsRetrieve(config, rms_pool, package_list)

    def rms_pool_create(self, rms_pool):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        self._info('Creating RMS pool...')

        rmstool.rmsPoolCreate(config, rms_pool)

    def rms_pool_list(self):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        pool_list = rmstool.rmsPoolList(config)

        pool_list = sorted(pool_list)

        print("\n".join(pool_list))

    def service_master(self):
        self._processDeployDir()
        self._serviceAdapt()
        self._serviceMaster()

    def service_list(self):
        self._processDeployDir()
        self._serviceAdapt()
        self._serviceListPrint()

    def service_exec(self, entry_point, instance_id):
        self._processDeployDir()

        config = self._config
        svc = self._serviceCommon(entry_point, instance_id)

        tool = svc['tool']
        t = self._getTool(tool)

        if isinstance(t, RuntimeTool):
            self._os.chdir(config['wcDir'])
            t.onRun(config, svc, [])
        else:
            self._errorExit(
                'Tool "{0}" for "{1}" does not support "service exec" command'.format(tool, entry_point))

    def service_stop(self, entry_point, instance_id, pid):
        self._processDeployDir()

        svc = self._serviceCommon(entry_point, instance_id)

        tool = svc['tool']
        t = self._getTool(tool)

        if isinstance(t, RuntimeTool):
            self._serviceStop(svc, t, int(pid))
        else:
            self._errorExit(
                'Tool "{0}" for "{1}" does not support "service stop" command'.format(tool, entry_point))

    def service_reload(self, entry_point, instance_id, pid):
        self._processDeployDir()

        config = self._config
        svc = self._serviceCommon(entry_point, instance_id)

        tool = svc['tool']
        t = self._getTool(tool)

        if isinstance(t, RuntimeTool):
            t.onReload(config, int(pid), svc['tune'])
        else:
            self._errorExit(
                'Tool "{0}" for "{1}" does not support "service reload" command'.format(tool, entry_point))

    def devserve(self):
        self._devserve_mode = True

        ospath = self._ospath
        pathutil = self._pathutil
        os = self._os

        deploy_dir = self._ext.tempfile.mkdtemp(prefix='futoin-cid-devserve')

        try:
            wc_dir = ospath.realpath(self._overrides['wcDir'])
            deploy_dir = ospath.realpath(deploy_dir)
            os.symlink(wc_dir, pathutil.safeJoin(deploy_dir, 'current'))

            self._overrides['devWcDir'] = wc_dir
            self._overrides['deployDir'] = deploy_dir

            self._deployLock()
            self._deployUnlock()

            self._processDeployDir()
            self._env['type'] = 'dev'
            self._serviceAdapt()
            self._serviceListPrint()
            self._serviceMaster()
            pathutil.rmTree(deploy_dir)
            deploy_dir = None
        finally:
            if deploy_dir:
                self._warn(
                    'Left "{0}" for inspection of error'.format(deploy_dir))

    def sudoers(self, entity, skip_key_mgmt):
        ospath = self._ospath
        detect = self._detect

        if not entity:
            entity = self._ext.pwd.getpwuid(self._os.geteuid())[0]

        lines = ['']
        commands = []

        if detect.isDebian() or detect.isUbuntu():
            lines += [
                '# env whitelist',
                'Defaults  env_keep += "DEBIAN_FRONTEND"',
            ]
            commands += [
                '# package installation only',
                '/usr/bin/apt-get install *',
                '/usr/bin/apt-get update',
                '/usr/bin/apt-add-repository *',
                '/usr/bin/dpkg -i *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/usr/bin/apt-key add *',
                ]

        elif detect.isFedora():
            commands += [
                '# package installation only',
                '/usr/bin/dnf install *',
                '/usr/bin/dnf config-manager --add-repo *',
                '/usr/bin/dnf config-manager --enable *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/usr/bin/rpm --import *',
                ]

        elif detect.isCentOS() or detect.isOracleLinux() or detect.isRHEL():
            commands += [
                '# package installation only',
                '/usr/bin/yum install *',
                '/usr/bin/yum-config-manager --add-repo *',
                '/usr/bin/yum-config-manager --enable *',
            ]

            if detect.isRHEL():
                commands += [
                    '# RHEL-specific',
                    '/sbin/subscription-manager repos --enable *',
                ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/usr/bin/rpm --import *',
                ]

        elif detect.isOpenSUSE() or detect.isSLES():
            commands += [
                '# package installation only',
                '/usr/bin/zypper --non-interactive install *',
                '/usr/bin/zypper --non-interactive addrepo *',
                '/usr/bin/zypper --non-interactive refresh *',
            ]

            if detect.isSLES():
                commands += [
                    '# package installation only',
                    '/usr/bin/SUSEConnect --product *',
                ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/bin/rpm --import *',
                ]

        elif detect.isArchLinux():
            commands += [
                '# package installation only',
                '/usr/bin/pacman *',
            ]

        elif detect.isGentoo():
            commands += [
                '# package installation only',
                '/usr/bin/emerge *',
            ]

        elif detect.isAlpineLinux():
            commands += [
                '# package installation only',
                '/sbin/apk add *',
                '/sbin/apk update',
                '/usr/bin/npm *',
                '/usr/bin/tee -a /etc/apk/repositories',
            ]

        elif detect.isMacOS():
            lines += [
                '# env whitelist',
                'Defaults  env_keep += "HOMEBREW_NO_GITHUB_API"',
            ]

            commands += [
                '# case for global brew install',
                '/usr/local/bin/brew install *',
                '/usr/local/bin/brew cask install *',
                '/usr/local/bin/brew search *',
                '/usr/local/bin/brew cask search *',
                '# note: security problem, if optional URL paremeter is used',
                '/usr/local/bin/brew tap homebrew/*',
                '/usr/local/bin/brew tap caskroom/*',
                '# lesser problem',
                '/usr/local/bin/brew unlink *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# insecure, but required for local brew cask',
                    'SETENV: /usr/sbin/installer *',
                    'SETENV: /usr/sbin/pkgutil *',
                    'SETENV: /usr/libexec/PlistBuddy *',
                    'SETENV: /usr/bin/xargs -0 -- /bin/rm *',
                    'SETENV: /bin/mv *',
                    'SETENV: /bin/ln *',
                    'SETENV: /bin/chmod *',
                    'SETENV: /bin/chown *',
                    'SETENV: /bin/rm *',
                    'SETENV: /bin/rmdir *',
                ]

        else:
            self._errorExit('Unfortunately this OS is not fully supported yet')

        if ospath.exists('/bin/systemctl'):
            commands += [
                '',
                '# start of services',
                '/bin/systemctl start *',
            ]

        if ospath.exists('/sbin/rc-service'):
            commands += [
                '',
                '# start of services',
                '/sbin/rc-service * start',
            ]

        if detect.isLinux():
            commands += [
                '',
                '# allow access to Docker (may have no sense)',
                '/usr/bin/docker *',
            ]

        commands += [
            '',
            '# virtual env bootstrap',
            '/usr/bin/pip install *',
            '/usr/local/bin/pip install *',
        ]

        lines.append('')

        for c in commands:

            if c and c[0] != '#':
                lines.append('{0} ALL=(ALL) NOPASSWD: {1}'.format(entity, c))
            else:
                lines.append(c)

        lines.append('')
        lines = "\n".join(lines)
        print(lines)

    def builddep(self, deps):
        if not deps:
            res = self._builddep.available()
            print("\n".join(res))
            return

        deps_set = set(deps)
        tools = set(self._getKnownTools()) & deps_set
        self._config = {
            'tools': dict([(t, True) for t in tools])
        }
        self._initTools()

        env = self._env

        if self._detect.isExternalToolsSetup(env):
            self._executil.externalSetup(env, ['build-dep'] + deps)
        else:
            self._builddep.require(env, list(deps_set - tools))

    def cte(self, tool, args):
        if tool == 'list':
            self.tool_list()
            return

        is_tool = tool in self._getKnownTools()

        if is_tool:
            self._overrides['tool'] = tool

        self._initConfig(True)
        self._processWcDir()

        if is_tool:
            self.tool_exec(tool, args)
        else:
            self.run(tool, args)
