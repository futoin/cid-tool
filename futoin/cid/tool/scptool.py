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


from ..rmstool import RmsTool


class scpTool(RmsTool):
    """secure copy.

RMS repo formats:

ssh://user@host/port:root/path - full remote, note the port
user@host:root/path - short remote
user@host - shortest remote
/some/path - local path
../some/other/path - another local path

More details:
* Packages are set read-only
* SSH shell access is required to remote as well (restricted shell is not suitable)
* SCP itself is used only for upload & retrieval. The rest is done through SSH.
* {hash_type}sum utilities must be present on remote for hash calculation support.
"""
    __slots__ = ()

    REMOTE_PATTERN = '^(ssh://)?([a-zA-Z][a-zA-Z0-9_]+@[a-zA-Z0-9_.]+)(/([0-9]{1,5}))(:(.+))?$'
    REMOTE_GRP_USER_HOST = 2
    REMOTE_GRP_PORT = 4
    REMOTE_GRP_PATH = 6

    def getDeps(self):
        return ['ssh']

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath
        re = self._ext.re
        scpBin = config['env']['scpBin']
        rms_repo = config['rmsRepo']

        remote = re.match(self.REMOTE_PATTERN, rms_repo)
        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = remote.group(self.REMOTE_GRP_PATH)

        for package in package_list:
            package_basename = ospath.basename(package)

            if remote:
                dst = "{0}:{1}".format(
                    user_host,
                    ospath.join(path, rms_pool, package_basename)
                )

                if '/' in rms_pool:
                    cmd = "mkdir -p {0}".format(ospath.join(path, rms_pool))
                    self._callSSH(config, user_host, port, cmd)

                self._callRemoteSCP(config, port, package, dst)

                cmd = "chmod ugo-wx {0}".format(
                    ospath.join(path, rms_pool, package_basename))
                self._callSSH(config, user_host, port, cmd)
            else:
                dst = ospath.join(rms_repo, rms_pool, package_basename)

                if '/' in rms_pool:
                    self._executil.callExternal(
                        ['mkdir', '-p', ospath.join(rms_repo, rms_pool)])

                self._executil.callExternal([scpBin, '-Bq', package, dst])
                self._executil.callExternal(['chmod', 'ugo-wx', dst])

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        ospath = self._ospath
        re = self._ext.re
        scpBin = config['env']['scpBin']
        rms_repo = config['rmsRepo']

        remote = re.match(self.REMOTE_PATTERN, rms_repo)
        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = remote.group(self.REMOTE_GRP_PATH)

        for package in package_list:
            package_basename = ospath.basename(package)

            if remote:
                if '/' in dst_pool:
                    cmd = "mkdir -p {0}".format(ospath.join(path, dst_pool))
                    self._callSSH(config, user_host, port, cmd)

                cmd = 'cp -a {0} {1} && chmod ugo-wx {1}'.format(
                    ospath.join(path, src_pool, package_basename),
                    ospath.join(path, dst_pool, package_basename)
                )
                self._callSSH(config, user_host, port, cmd)
            else:
                src = ospath.join(rms_repo, src_pool, package_basename)
                dst = ospath.join(rms_repo, dst_pool, package_basename)

                if '/' in dst_pool:
                    self._executil.callExternal(
                        ['mkdir', '-p', ospath.join(rms_repo, dst_pool)])

                self._executil.callExternal([scpBin, '-Bq', src, dst])
                self._executil.callExternal(['chmod', 'ugo-wx', dst])

    def rmsGetList(self, config, rms_pool, package_hint):
        ospath = self._ospath
        re = self._ext.re

        env = config['env']
        rms_repo = config['rmsRepo']
        remote = re.match(self.REMOTE_PATTERN, rms_repo)

        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = ospath.join(remote.group(self.REMOTE_GRP_PATH), rms_pool)
            cmd = 'ls {0}'.format(path)
            ret = self._callSSH(config, user_host, port, cmd).split("\n")
        else:
            path = ospath.join(rms_repo, rms_pool)
            ret = self._os.listdir(path)

        return ret

    def rmsRetrieve(self, config, rms_pool, package_list):
        ospath = self._ospath
        re = self._ext.re

        scpBin = config['env']['scpBin']
        rms_repo = config['rmsRepo']

        remote = re.match(self.REMOTE_PATTERN, rms_repo)
        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = remote.group(self.REMOTE_GRP_PATH)

        for package in package_list:
            package_basename = ospath.basename(package)

            if remote:
                src = "{0}:{1}".format(
                    user_host,
                    ospath.join(path, rms_pool, package_basename)
                )
                self._callRemoteSCP(config, port, src, package_basename)
            else:
                src = ospath.join(rms_repo, rms_pool, package_basename)
                self._executil.callExternal(
                    [scpBin, '-Bq', src, package_basename])

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        ospath = self._ospath
        re = self._ext.re

        env = config['env']
        rms_repo = config['rmsRepo']
        remote = re.match(self.REMOTE_PATTERN, rms_repo)

        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = ospath.join(remote.group(
                self.REMOTE_GRP_PATH), rms_pool, package)
            cmd = "{0}sum {1}".format(hash_type, path)
            ret = self._callSSH(config, user_host, port, cmd,
                                verbose=False).strip().split()[0]
        else:
            path = ospath.join(rms_repo, rms_pool, package)
            ret = self.rmsCalcHash(path, hash_type).split(':', 1)[1]

        return ret

    def rmsPoolCreate(self, config, rms_pool):
        ospath = self._ospath
        re = self._ext.re

        env = config['env']
        rms_repo = config['rmsRepo']
        remote = re.match(self.REMOTE_PATTERN, rms_repo)

        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = ospath.join(remote.group(self.REMOTE_GRP_PATH), rms_pool)
            cmd = 'mkdir -p {0}'.format(path)
            self._callSSH(config, user_host, port, cmd)
        else:
            path = ospath.join(rms_repo, rms_pool)

            if not ospath.exists(path):
                self._os.makedirs(path)

    def rmsPoolList(self, config):
        os = self._os
        re = self._ext.re

        env = config['env']
        rms_repo = config['rmsRepo']
        remote = re.match(self.REMOTE_PATTERN, rms_repo)

        if remote:
            user_host = remote.group(self.REMOTE_GRP_USER_HOST)
            port = remote.group(self.REMOTE_GRP_PORT)
            path = remote.group(self.REMOTE_GRP_PATH)
            cmd = 'ls {0}'.format(path)
            ret = self._callSSH(config, user_host, port, cmd).split("\n")
        else:
            ret = os.listdir(rms_repo)

        return ret

    def _callRemoteSCP(self, config, port, src, dst):
        port = port or '22'
        env = config['env']
        self._executil.callExternal([
            env['scpBin'],
            '-Bq', '-P', port,
            '-o', 'StrictHostKeyChecking={0}'.format(
                env['sshStrictHostKeyChecking']),
            src, dst
        ])

    def _callSSH(self, config, user_host, port, cmd, **kwargs):
        port = port or '22'
        env = config['env']
        return self._executil.callExternal([
            env['sshBin'],
            '-Tqn',
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking={0}'.format(
                env['sshStrictHostKeyChecking']),
            '-p', port,
            user_host, '--', cmd
        ], **kwargs)
