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

from .data import DataSlots

from ..subtool import SubTool
from ..runtimetool import RuntimeTool
from ..rmstool import RmsTool
from ..vcstool import VcsTool


class ToolMixIn(DataSlots):
    __slots__ = ()

    def __init__(self):
        super(ToolMixIn, self).__init__()
        self._tool_impl = {}

    def _checkKnownTool(self, tool):
        if tool not in self._tool_impl:
            self._errorExit(
                'Implementation for "{0}" was not found'.format(tool))

    def _forEachTool(self, cb, allow_failure=False, base=None):
        config = self._config
        tools = config['toolOrder']

        for t in tools:
            t = self._getTool(t)

            if base and not isinstance(t, base):
                continue

            try:
                cb(config, t)
            except RuntimeError as e:
                if not allow_failure:
                    raise e

    def _getTool(self, name):
        self._checkKnownTool(name)
        tool_impl = self._tool_impl
        timpl = tool_impl[name]

        if isinstance(timpl, SubTool):
            return timpl

        tool_mod_name = timpl
        tool_module = self._ext.importlib.import_module(tool_mod_name)
        timpl = getattr(tool_module, name + 'Tool')(name)

        try:
            getattr(timpl, '__dict__')
            self._errorExit(
                'Missing __slots__ in {0}'.format(tool_mod_name))
        except KeyError:
            tool_impl[name] = timpl

        return timpl

    def _getKnownTools(self):
        return self._tool_impl.keys()

    def _getVcsTool(self):
        config = self._config
        vcs = config.get('vcs', None)

        if not vcs:
            self._errorExit(
                'Unknown VCS. Please set through --vcsRepo or project manifest')

        vcstool = self._getTool(vcs)

        if not config.get('vcsRepo', None):  # also check it set
            try:
                config['vcsRepo'] = vcstool.vcsGetRepo(config)
            except self._ext.subprocess.CalledProcessError as e:
                self._warn(str(e))

            if not config.get('vcsRepo', None):
                self._errorExit(
                    'Unknown VCS repo. Please set through --vcsRepo or project manifest')

        # Make sure these are present event after config is re-read
        self._overrides['vcs'] = vcs
        self._overrides['vcsRepo'] = config['vcsRepo']

        return vcstool

    def _getRmsTool(self):
        config = self._config
        rms = config.get('rms', None)

        if not rms:
            self._errorExit(
                'Unknown RMS. Please set through --rmsRepo or project manifest')

        if not config.get('rmsRepo', None):  # also check it set
            self._errorExit(
                'Unknown RMS repo. Please set through --rmsRepo or project manifest')

        # Make sure these are present event after config is re-read
        self._overrides['rms'] = rms
        self._overrides['rmsRepo'] = config['rmsRepo']

        return self._getTool(rms)

    def _getTarTool(self, compressor=None, package_ext=None):
        env = self._env
        compress_flag = None

        tar_tool = self._getTool('tar')
        tar_tool.requireInstalled(env)

        # Find out type
        # ---
        if package_ext:
            if package_ext == '.txz':
                compressor = 'xz'
            elif package_ext == '.tbz2':
                compressor = 'bzip2'
            elif package_ext == '.tgz':
                compressor = 'gzip'
            elif package_ext == '.tar' or not package_ext:
                compressor = 'tar'
            else:
                self._errorExit(
                    'Not supported package format: {0}'.format(package_ext))
        elif not compressor:
            tool_tune = self._config.get('toolTune', {})
            compressor = tool_tune.get('tar', {}).get('compressor', 'gzip')

        # Install compressor
        # ---
        if compressor != 'tar':
            self._getTool(compressor).requireInstalled(env)

        # Configure based on type
        # ---
        if compressor == 'xz':
            package_ext = '.txz'
            compress_flag = 'J'
        elif compressor == 'bzip2':
            package_ext = '.tbz2'
            compress_flag = 'j'
        elif compressor == 'gzip':
            package_ext = '.tgz'
            compress_flag = 'z'
        elif compressor == 'tar':
            package_ext = '.tar'
            compress_flag = ''
        else:
            self._errorExit('Not supported compressor: {9}'.format(compressor))

        return tar_tool, compress_flag, package_ext

    def _initTools(self):
        config = self._config
        env = self._env
        os = self._os
        ospath = self._ospath
        importlib = self._ext.importlib

        if config is None:
            config = self._overrides.copy()
            config['env'] = env

        # ---
        config['projectRootSet'] = set(os.listdir('.'))

        # ---
        plugins = {}
        plugins.update(env.get('plugins', {}))
        plugins.update(config.get('plugins', {}))

        plugin_packs = []
        plugin_packs += env.get('pluginPacks', [])
        plugin_packs += config.get('pluginPacks', [])
        plugin_packs.append('futoin.cid.tool')

        for pack_mod_name in plugin_packs:
            m = importlib.import_module(pack_mod_name)
            pack_dir = ospath.dirname(m.__file__)
            tool_files = os.listdir(pack_dir)
            tool_files = self._ext.fnmatch.filter(tool_files, '*tool.py')

            for f in tool_files:
                tool = f.replace('tool.py', '')
                tool_mod_name = '{0}.{1}tool'.format(pack_mod_name, tool)
                plugins[tool] = tool_mod_name

        tool_impl = self._tool_impl

        for (tool, t) in tool_impl.items():
            if isinstance(t, SubTool):
                t.onConfigReset()

        for (tool, tool_mod_name) in plugins.items():
            if tool not in tool_impl:
                tool_impl[tool] = tool_mod_name

        # ---
        config_tools = config.get('tools', None)
        tools = []

        if config_tools:
            if not isinstance(config_tools, dict):
                self._errorExit(
                    'futoin.json:tools must be a map of tool=>version pairs')

            for (tool, v) in config_tools.items():
                self._checkKnownTool(tool)
                tools.append(tool)

                if v != '*' and v != True:
                    env[tool + 'Ver'] = v

        curr_tool = config.get('tool', None)

        if curr_tool:
            tools.append(curr_tool)
            tool_ver = config.get('toolVer', None)

            if tool_ver:
                env[curr_tool + 'Ver'] = tool_ver
        elif (not config_tools and
              self._project_config is not None and
              config.get('toolDetect', True)):
            for n in self._getKnownTools():
                t = self._getTool(n)
                if t.autoDetect(config):
                    tools.append(n)

        # Make sure deps & env are processed for cli-supplied tools
        # --
        for (item, base) in {'rms': RmsTool, 'vcs': VcsTool}.items():
            tool = config.get(item, None)

            if tool:
                tools.append(tool)

                if not isinstance(self._getTool(tool), base):
                    self._errorExit(
                        'Tool {0} does not suite {1} type'.format(tool, item))

        # Make sure tools defined in entryPoints are auto-detected
        # --
        for (ep, ed) in config.get('entryPoints', {}).items():
            tool = ed.get('tool', None)

            if tool:
                tools.append(tool)

                if not isinstance(self._getTool(tool), RuntimeTool):
                    self._errorExit(
                        'Tool {0} does not suite RuntimeTool type'.format(tool))

        # add all deps
        # --
        dep_generations = [set(tools)]
        tools = set(tools)
        postdeps = set()
        dep_length = 0
        last_index = 0
        while len(dep_generations) != dep_length:
            dep_length = len(dep_generations)
            curr_index = last_index
            last_index = len(dep_generations)

            for g in dep_generations[curr_index:]:
                for tn in g:
                    t = self._getTool(tn)
                    moredeps = set(t.getDeps())
                    if moredeps:
                        dep_generations.append(moredeps)
                        tools.update(moredeps)
                    postdeps.update(set(t.getPostDeps()) - tools)

            if len(dep_generations) == dep_length and postdeps:
                dep_generations.append(postdeps)
                tools.update(postdeps)
                postdeps = set()

        # ---
        if self._detect.isMacOS() and tools:
            # Make sure Homebrew is always implicit first tool
            dep_generations.append(set(['brew']))
            self._getTool('brew')

        # ---
        dep_generations.reverse()
        tools = []
        for d in dep_generations:
            tools.extend(d - set(tools))
        config['toolOrder'] = tools

        # --
        for tool in tools:
            t = tool_impl[tool]
            t.envDeps(env)

        # --
        if config.get('toolTest', False):
            for tool in tools:
                t = tool_impl[tool]
                t.sanitizeVersion(env)
                t.importEnv(env)
                if not t.isInstalled(env):
                    break
        else:
            # note, it may have some undesired effect on parallel execution,
            # but let's leave that for now
            self._globalLock()

            for tool in tools:
                t = tool_impl[tool]
                t.sanitizeVersion(env)
                t.requireInstalled(env)
                if tool != curr_tool:
                    t.loadConfig(config)

            self._globalUnlock()

        # Solves generic issues of ordering independent tools in
        # later execution with predictable results:
        # 1. sort by integer order
        # 2. sort by tool name
        tools.sort(key=lambda v: (tool_impl[v].getOrder(), v))
