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

from ..vcstool import VcsTool
from .bashtoolmixin import BashToolMixIn


class hgTool(BashToolMixIn, VcsTool):
    """Mercurial SCM.

Home: https://www.mercurial-scm.org/
"""
    __slots__ = ()

    def getDeps(self):
        return ['bash']

    def _installTool(self, env):
        self._install.debrpm(['mercurial'])
        self._install.emerge(['dev-vcs/mercurial'])
        self._install.pacman(['mercurial'])
        self._install.apk(['mercurial'])
        self._install.brew('mercurial')

    def autoDetectFiles(self):
        return '.hg'

    def _getCurrentBranch(self, config):
        return self._executil.callExternal([
            config['env']['hgBin'], 'branch'
        ]).strip()

    def vcsGetRepo(self, config, wc_dir=None):
        wc_dir = wc_dir or self._os.getcwd()
        return self._executil.callExternal([
            config['env']['hgBin'], '--repository', wc_dir, 'paths', 'default'
        ], verbose=False).strip()

    def _hgCheckoutTool(self, config):
        hgBin = config['env']['hgBin']
        help_res = self._executil.callExternal(
            [hgBin, 'checkout', '--help'], verbose=False)
        tool_args = []

        if help_res.find('--tool') > 0:
            tool_args += ['--tool', 'internal:merge']

        return tool_args

    def vcsCheckout(self, config, vcs_ref):
        ospath = self._ospath
        hgBin = config['env']['hgBin']
        wc_dir = self._os.getcwd()

        if ospath.isdir('.hg'):
            if 'vcsRepo' in config:
                remote_info = self.vcsGetRepo(config, '.')
                if remote_info != config['vcsRepo']:
                    self._errorExit("Hg remote mismatch: " + remote_info)

            self._executil.callExternal([hgBin, 'pull'])
        else:
            self._executil.callExternal(
                [hgBin, 'clone', config['vcsRepo'], wc_dir])

        if not vcs_ref:
            # skip default branch
            return

        for v in self._executil.callExternal([hgBin, 'branches'], verbose=False).strip().split("\n"):
            if v and v.split()[0] == vcs_ref:
                break
        else:
            for v in self._executil.callExternal([hgBin, 'tags'], verbose=False).strip().split("\n"):
                if v and v.split()[0] == vcs_ref:
                    break
            else:
                self._errorExit(
                    'Unknown VCS ref {0}. Hint: closed branches are ignored!'.format(vcs_ref))

        self._executil.callExternal([hgBin, 'checkout', '--check',
                                     vcs_ref] + self._hgCheckoutTool(config))

    def vcsCommit(self, config, message, files):
        hgBin = config['env']['hgBin']
        files = files or ['-A']
        self._executil.callExternal(
            [hgBin, 'commit', '-A', '-m', message] + files)

    def vcsTag(self, config, tag, message):
        hgBin = config['env']['hgBin']
        self._executil.callExternal([hgBin, 'tag', '-m', message, tag])

    def vcsPush(self, config, refs):
        refs = refs or []
        env = config['env']
        hgBin = env['hgBin']
        opts = []

        tags = self.vcsListTags(config, '.', '')

        for r in refs:
            if r in tags:
                continue
            if r == '--new-branch':
                opts.append(r)
                continue

            opts.append('-b')
            opts.append(r)
        self._executil.callExternal([hgBin, 'push'] + opts)

    def vcsGetRevision(self, config):
        hgBin = config['env']['hgBin']
        return self._executil.callExternal([hgBin, 'identify', '--id'], verbose=False).strip()

    def _hgCache(self, config, vcs_cache_dir):
        ospath = self._ospath
        hgBin = config['env']['hgBin']
        vcsrepo = config['vcsRepo']

        if vcs_cache_dir is None:
            # Hg does not allow remote repository listing
            if ospath.exists('.hg') and self.vcsGetRepo(config, vcs_cache_dir) == vcsrepo:
                vcs_cache_dir = '.'
            else:
                vcs_cache_dir = self._pathutil.cacheDir('hg')
                vcs_cache_dir = ospath.join(
                    vcs_cache_dir,
                    vcsrepo.replace('/', '_').replace(':', '_')
                )
            vcs_cache_dir = ospath.realpath(vcs_cache_dir)

        if ospath.isdir(vcs_cache_dir):
            remote_info = self.vcsGetRepo(config, vcs_cache_dir)

            if remote_info != vcsrepo:
                self._warn('removing Hg cache on remote URL mismatch: {0} != {1}'
                           .format(remote_info, vcsrepo))
                self._pathutil.rmTree(vcs_cache_dir)
            else:
                self._executil.callExternal(
                    [hgBin, '--cwd', vcs_cache_dir, 'pull'])

        if not ospath.isdir(vcs_cache_dir):
            self._executil.callExternal(
                [hgBin, 'clone', vcsrepo, vcs_cache_dir])

        return vcs_cache_dir

    def vcsGetRefRevision(self, config, vcs_cache_dir, branch):
        vcs_cache_dir = self._hgCache(config, vcs_cache_dir)

        hgBin = config['env']['hgBin']

        res = self._executil.callExternal([
            hgBin, '--repository', vcs_cache_dir, 'branches'
        ], verbose=False).strip().split("\n")

        for r in res:
            r = r.split()

            if r and r[0] == branch:
                return r[1]

        self._errorExit("Uknown Hg ref: {0}".format(branch))

    def vcsListTags(self, config, vcs_cache_dir, tag_hint):
        vcs_cache_dir = self._hgCache(config, vcs_cache_dir)

        hgBin = config['env']['hgBin']

        res = self._executil.callExternal([
            hgBin, '--repository', vcs_cache_dir, 'tags'
        ], verbose=False).strip().split("\n")

        res = [v and v.split()[0] or '' for v in res]
        res = list(filter(None, res))
        del res[res.index('tip')]
        return res

    def vcsListBranches(self, config, vcs_cache_dir, branch_hint):
        vcs_cache_dir = self._hgCache(config, vcs_cache_dir)

        hgBin = config['env']['hgBin']

        res = self._executil.callExternal([
            hgBin, '--repository', vcs_cache_dir, 'branches'
        ], verbose=False).strip().split("\n")

        res = [v and v.split()[0] or '' for v in res]
        res = list(filter(None, res))
        return res

    def vcsExport(self, config, vcs_cache_dir, vcs_ref, dst_path):
        ospath = self._ospath
        os = self._os
        vcs_cache_dir = self._hgCache(config, vcs_cache_dir)

        self._executil.callExternal([
            config['env']['hgBin'],
            '--repository', vcs_cache_dir,
            'archive',
            '--rev', vcs_ref,
            '--type', 'files',
            #'--exclude', '.hg*',
            dst_path
        ])

        for f in ['.hgtags', '.hgignore', '.hg_archival.txt']:
            f = ospath.join(dst_path, f)

            if ospath.exists(f):
                os.remove(f)

    def vcsBranch(self, config, vcs_ref):
        hgBin = config['env']['hgBin']
        self._executil.callExternal([hgBin, 'branch', vcs_ref])
        # We do not use bookmarks, so the only way to actually create the
        # branch.
        self.vcsCommit(config, "CID new branch " + vcs_ref, [])
        self.vcsPush(config, ['--new-branch', vcs_ref])

    def vcsMerge(self, config, vcs_ref, cleanup):
        curr_ref = self._getCurrentBranch(config)

        hgBin = config['env']['hgBin']

        try:
            self._executil.callExternal(
                [hgBin, 'merge', '--tool', 'internal:merge', vcs_ref])
        except self._ext.subprocess.CalledProcessError:
            if cleanup:
                self.vcsRevert(config)
                self._errorExit('Merge failed, aborted.')
            self._errorExit('Merge failed, left as-is.')

        self.vcsCommit(config, "CID merged " + vcs_ref, [])
        self.vcsPush(config, [curr_ref])

    def vcsDelete(self, config, vcs_cache_dir, vcs_ref):
        os = self._os
        vcs_cache_dir = self._hgCache(config, vcs_cache_dir)
        hgBin = config['env']['hgBin']

        old_cwd = os.getcwd()
        os.chdir(vcs_cache_dir)

        self._executil.callExternal([hgBin, 'checkout', '--check',
                                     vcs_ref] + self._hgCheckoutTool(config))
        self.vcsCommit(config, "CID branch delete", ['--close-branch'])
        self.vcsPush(config, [vcs_ref])
        os.chdir(old_cwd)

    def vcsRevert(self, config):
        hgBin = config['env']['hgBin']
        self._executil.callExternal([
            hgBin,
            'update', '--clean',
        ] + self._hgCheckoutTool(config))
        self._executil.callExternal([
            hgBin,
            '--config', 'extensions.purge=',
            'purge', '-I', '*.orig', '-I', '**/*.orig', '--all'
        ])

    def vcsIsMerged(self, config, vcs_ref):
        res = self._executil.callExternal([
            config['env']['hgBin'],
            'merge', '--preview',
            '--tool=internal:merge',
            vcs_ref
        ], verbose=False).strip()
        return res == ''

    def vcsClean(self, config):
        hgBin = config['env']['hgBin']
        self._executil.callExternal([
            hgBin,
            '--config', 'extensions.purge=',
            'purge', '--all',
        ])
