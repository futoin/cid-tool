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

from .subtool import SubTool

__all__ = ['VcsTool']


class VcsTool(SubTool):
    __slots__ = ()

    def autoDetect(self, config):
        return self._autoDetectVCS(config, self.autoDetectFiles())

    def vcsGetRepo(self, config, wc_dir=None):
        raise NotImplementedError(self._name)

    def vcsCheckout(self, config, branch):
        raise NotImplementedError(self._name)

    def vcsCommit(self, config, message, files):
        raise NotImplementedError(self._name)

    def vcsTag(self, config, tag, message):
        raise NotImplementedError(self._name)

    def vcsPush(self, config, refs):
        raise NotImplementedError(self._name)

    def vcsGetRevision(self, config):
        raise NotImplementedError(self._name)

    def vcsGetRefRevision(self, config, vcs_cache_dir, branch):
        raise NotImplementedError(self._name)

    def vcsListTags(self, config, vcs_cache_dir, tag_hint):
        raise NotImplementedError(self._name)

    def vcsListBranches(self, config, vcs_cache_dir, branch_hint):
        raise NotImplementedError(self._name)

    def vcsExport(self, config, vcs_cache_dir, vcs_ref, dst_path):
        raise NotImplementedError(self._name)

    def vcsBranch(self, config, vcs_ref):
        raise NotImplementedError(self._name)

    def vcsMerge(self, config, vcs_ref, cleanup):
        raise NotImplementedError(self._name)

    def vcsDelete(self, config, vcs_cache_dir, vcs_ref):
        raise NotImplementedError(self._name)

    def vcsRevert(self, config):
        raise NotImplementedError(self._name)

    def vcsIsMerged(self, config, vcs_ref):
        raise NotImplementedError(self._name)

    def vcsClean(self, config):
        raise NotImplementedError(self._name)

    def _autoDetectVCS(self, config, vcsDir):
        if config.get('vcs', None) == self._name:
            return True

        if vcsDir in config['projectRootSet']:
            if config.get('vcs', self._name) != self._name:
                self._errorExit(
                    'Another VCS type {0} has been already detected!'.format(config['vcs']))
            config['vcs'] = self._name
            return True

        return False
