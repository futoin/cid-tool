#
# Copyright 2015-2020 Andrey Galkin <andrey@futoin.org>
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

# pylint: disable=no-member

class BashToolMixIn(object):
    __slots__ = ()

    def getDeps(self):
        return ['bash']

    def _callBash(self, env, cmd=None, bash_args=[], *args, **nargs):
        if cmd:
            cmd_args = ['-c', cmd]
        else:
            cmd_args = ['-s']

        return self._executil.callExternal(
            [env['bashBin'], '--noprofile', '--norc'] + cmd_args + bash_args,
            *args, **nargs)

    def _callBashInteractive(self, env, cmd, replace=True):
        return self._executil.callInteractive([
            env['bashBin'],
            '--noprofile', '--norc',
            '-c', cmd,
        ], replace=replace)
