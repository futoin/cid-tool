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
from ..rmstool import RmsTool


class svnTool(VcsTool, RmsTool):
    """Apache Subversion: Enterprise-class centralized version control for the masses.

Home: https://subversion.apache.org/
"""
    __slots__ = ()

    def _installTool(self, env):
        if self._detect.isSLES():
            self._install.zypperRepo(
                None,
                'http://download.opensuse.org/repositories/devel:tools:scm:svn'
                '/SLE_12_SP2/devel:tools:scm:svn.repo')

        self._install.debrpm(['subversion'])
        self._install.emerge(['dev-vcs/subversion'])
        self._install.pacman(['subversion'])
        self._install.apk(['subversion'])
        self._install.brew('subversion')

    def autoDetectFiles(self):
        return '.svn'

    def autoDetect(self, config):
        return (VcsTool.autoDetect(self, config) or
                RmsTool.autoDetect(self, config))

    def getDeps(self):
        return ['ssh']

    def vcsGetRepo(self, config, wc_dir=None):
        wc_dir = wc_dir or self._os.getcwd()

        svn_info = self._executil.callExternal([
            config['env']['svnBin'], 'info', '--xml', wc_dir
        ], verbose=False)

        svn_info = self._ext.minidom.parseString(svn_info)
        svn_info = svn_info.getElementsByTagName('url')
        url = svn_info[0].firstChild.nodeValue

        url = self._ext.re.sub('/(trunk|branches|tags).*$', '', url)
        return url

    def _detectSVNPath(self, config, vcs_ref):
        env = config['env']
        vcsRepo = config['vcsRepo']
        branch_path = '{0}/branches/{1}'.format(vcsRepo, vcs_ref)
        tag_path = '{0}/tags/{1}'.format(vcsRepo, vcs_ref)

        if vcs_ref == 'trunk':
            svn_repo_path = '{0}/trunk'.format(vcsRepo)
        elif self._callVCSSVN(config, ['info', branch_path], suppress_fail=True):
            svn_repo_path = branch_path
        elif self._callVCSSVN(config, ['info', tag_path], suppress_fail=True):
            svn_repo_path = tag_path
        else:
            self._errorExit("VCS ref was not found: " + vcs_ref)

        return svn_repo_path

    def vcsCheckout(self, config, vcs_ref):
        env = config['env']
        wc_dir = self._os.getcwd()
        vcs_ref = vcs_ref or 'trunk'

        svn_repo_path = self._detectSVNPath(config, vcs_ref)

        if self._ospath.isdir('.svn'):
            self._callVCSSVN(config, ['switch', svn_repo_path])
        else:
            self._callVCSSVN(config, [
                'checkout',
                svn_repo_path,
                wc_dir]
            )

    def vcsCommit(self, config, message, files):
        if files:
            commit_files = files
        else:
            commit_files = []
            files = ['--depth=infinity', '.']

        self._callVCSSVN(config, ['add', '--force', ] + files)
        self._callVCSSVN(config, ['commit', '-m', message] + commit_files)

    def vcsTag(self, config, tag, message):
        env = config['env']

        svn_info = self._callVCSSVN(config, ['info', '--xml'], verbose=False)
        svn_info = self._ext.minidom.parseString(svn_info)
        svn_info = svn_info.getElementsByTagName('url')
        svn_url = svn_info[0].firstChild.nodeValue

        self._callVCSSVN(config, [
            'copy',
            '-m', message,
            '--parents',
            svn_url,
            '%s/tags/%s' % (config['vcsRepo'], tag)
        ])

    def vcsPush(self, config, refs):
        pass

    def vcsGetRevision(self, config):
        svn_info = self._callVCSSVN(config, ['info',  '--xml'], verbose=False)

        svn_info = self._ext.minidom.parseString(svn_info)
        svn_info = svn_info.getElementsByTagName('commit')

        if len(svn_info):
            return svn_info[0].getAttribute('revision')

        return 'local'

    def vcsGetRefRevision(self, config, vcs_cache_dir, branch):
        svn_repo_path = self._detectSVNPath(config, branch)

        res = self._callVCSSVN(
            config, ['info', svn_repo_path, '--xml'], verbose=False)

        res = self._ext.minidom.parseString(res)
        return res.getElementsByTagName('commit')[0].getAttribute('revision')

    def vcsListTags(self, config, vcs_cache_dir, tag_hint):
        return self._svnListCommon(config, 'vcsRepo', vcs_cache_dir, 'tags')

    def vcsListBranches(self, config, vcs_cache_dir, branch_hint):
        return self._svnListCommon(config, 'vcsRepo', vcs_cache_dir, 'branches')

    def _svnListCommon(self, config, repo_key, vcs_cache_dir, sub_path):
        repo = config[repo_key]
        svn_repo_path = '{0}/{1}'.format(repo, sub_path)

        if svn_repo_path[-1] != '/':
            svn_repo_path += '/'

        res = self._callSVN(
            config, repo_key, ['ls', svn_repo_path],
            verbose=False
        )

        res = res.strip().split("\n")

        res = [v and v.replace('/', '') or '' for v in res]
        res = list(filter(None, res))
        return res

    def vcsExport(self, config, vcs_cache_dir, vcs_ref, dst_path):
        ospath = self._ospath
        svn_repo_path = self._detectSVNPath(config, vcs_ref)

        self._pathutil.rmTree(dst_path)

        if vcs_cache_dir is None:
            self._callVCSSVN(config, ['export', svn_repo_path, dst_path])
            return

        if ospath.isdir(vcs_cache_dir):
            cnd = 'switch'
        else:
            cnd = 'checkout'

        self._callVCSSVN(config, [cnd, svn_repo_path, vcs_cache_dir])
        self._callVCSSVN(config, ['export', vcs_cache_dir, dst_path])

    def vcsBranch(self, config, vcs_ref):
        vcsRepo = config['vcsRepo']
        svn_dst_path = '{0}/branches/{1}'.format(vcsRepo, vcs_ref)

        svn_info = self._callVCSSVN(config, ['info', '--xml'], verbose=False)
        svn_info = self._ext.minidom.parseString(svn_info)
        svn_info = svn_info.getElementsByTagName('url')
        svn_src_path = svn_info[0].firstChild.nodeValue

        if self._callVCSSVN(config, ['info', svn_dst_path], suppress_fail=True):
            self._errorExit('VCS branch {0} already exists!'.format(vcs_ref))

        self._callVCSSVN(config, [
            'copy', '--parents',
            '-m', 'CID branch ' + vcs_ref,
            svn_src_path, svn_dst_path,
        ])
        self.vcsCheckout(config, vcs_ref)

    def vcsMerge(self, config, vcs_ref, cleanup):
        svn_repo_path = self._detectSVNPath(config, vcs_ref)

        self._callVCSSVN(config, ['update'])
        self._callVCSSVN(
            config, ['merge', '--accept', 'postpone', svn_repo_path])

        try:
            self._callVCSSVN(config, ['commit', '-m', 'CID merged ' + vcs_ref])
        except self._ext.subprocess.CalledProcessError:
            if cleanup:
                self.vcsRevert(config)
                self._errorExit('Merge failed, aborted.')
            self._errorExit('Merge failed, left as-is.')

    def vcsDelete(self, config, vcs_cache_dir, vcs_ref):
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/branches/{1}'.format(vcsRepo, vcs_ref)
        self._callVCSSVN(
            config, ['remove', '-m', 'CID delete ' + vcs_ref, svn_repo_path])

    def vcsRevert(self, config):
        self._callVCSSVN(config, ['revert', '-R', '.'])

    def vcsIsMerged(self, config, vcs_ref):
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/branches/{1}'.format(vcsRepo, vcs_ref)

        res = self._callVCSSVN(config, [
            'mergeinfo', '--show-revs',
            'eligible',
            svn_repo_path
        ], verbose=False).strip()

        return res == ''

    def vcsClean(self, config):
        svn_info = self._executil.callExternal([
            config['env']['svnBin'], 'status', '--no-ignore', '--xml'
        ], verbose=False)

        svn_info = self._ext.minidom.parseString(svn_info)
        entries = svn_info.getElementsByTagName('entry')
        pathutil = self._pathutil

        for entry in entries:
            p = entry.getAttribute('path')
            wcstatus = entry.getElementsByTagName('wc-status')

            if wcstatus[0].getAttribute('item') in ('unversioned', 'ignored'):
                pathutil.rmTree(p)

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath
        rms_repo = config['rmsRepo']

        for package in package_list:
            package_basename = ospath.basename(package)

            dst = '{0}/{1}/{2}'.format(rms_repo, rms_pool, package_basename)

            self._callRMSSVN(config, [
                'import',
                '-m', 'FutoIn CID upload',
                package, dst,
            ])

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        ospath = self._ospath
        rms_repo = config['rmsRepo']

        args = []

        if '/' in dst_pool:
            args += ['--parents']

        for package in package_list:
            package_basename = ospath.basename(package)

            src = '{0}/{1}/{2}'.format(rms_repo, src_pool, package_basename)
            dst = '{0}/{1}/{2}'.format(rms_repo, dst_pool, package_basename)

            self._callRMSSVN(config, [
                'copy',
                '-m', 'FutoIn CID promotion',
                src, dst,
            ] + args)

    def rmsGetList(self, config, rms_pool, package_hint):
        return self._svnListCommon(config, 'rmsRepo', None, rms_pool)

    def rmsRetrieve(self, config, rms_pool, package_list):
        self._rmsRetrieve(config, rms_pool, package_list)

    def _rmsRetrieve(self, config, rms_pool, package_list, dst_dir=None):
        ospath = self._ospath
        rms_repo = config['rmsRepo']

        for package in package_list:
            package_basename = ospath.basename(package)

            src = '{0}/{1}/{2}'.format(rms_repo, rms_pool, package_basename)

            if dst_dir:
                dst = ospath.join(dst_dir, package_basename)
            else:
                dst = package_basename

            self._callRMSSVN(config, [
                'export',
                src, package_basename,
            ])

    def rmsPoolCreate(self, config, rms_pool):
        rms_repo = config['rmsRepo']

        dst = '{0}/{1}'.format(rms_repo, rms_pool)

        try:
            self._callRMSSVN(config, [
                'mkdir', '--parents',
                '-m', 'FutoIn CID pool creation',
                dst,
            ])
        except self._ext.subprocess.CalledProcessError:
            # make sure it exists
            self._callRMSSVN(config, ['info', dst])

    def rmsPoolList(self, config):
        return self._svnListCommon(config, 'rmsRepo', None, '')

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        rms_repo = config['rmsRepo']

        src = '{0}/{1}/{2}'.format(rms_repo, rms_pool, package)

        hf = self._ext.hashlib.new(hash_type)

        self._callRMSSVN(config, ['cat', src],
                         output_handler=lambda chunk: hf.update(chunk))

        return hf.hexdigest()

    def _callVCSSVN(self, config, args, **kwargs):
        return self._callSVN(config, 'vcsRepo', args, **kwargs)

    def _callRMSSVN(self, config, args, **kwargs):
        return self._callSVN(config, 'rmsRepo', args, **kwargs)

    def _callSVN(self, config, repo_key, args, **kwargs):
        env = config['env']
        svnBin = env['svnBin']
        rms_repo = config[repo_key]
        opts = []

        if rms_repo.startswith('svn+ssh://'):
            sshm = self._ext.re.match('svn\\+ssh://[^/]+(:([0-9]+))', rms_repo)
            ssh_port = sshm.group(2) or '22'
            ssh_opts = '-o BatchMode=yes -o StrictHostKeyChecking={0}'.format(
                env['sshStrictHostKeyChecking'])
            opts += [
                '--config-option',
                'config:tunnels:ssh=$SVN_SSH ssh -q -p {0} {1}'.format(
                    ssh_port, ssh_opts)
            ]

            # Dirty workaround
            if sshm.group(1):
                for i in range(len(args)):
                    a = args[i]

                    if a.startswith(sshm.group(0)):
                        args[i] = a.replace(sshm.group(1), '', 1)

        return self._executil.callExternal([svnBin] + args + opts, **kwargs)
