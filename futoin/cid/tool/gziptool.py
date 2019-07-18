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

from ..buildtool import BuildTool


class gzipTool(BuildTool):
    """Compression utility designed to be a replacement for compress.

Home: http://www.gzip.org/

Auto-detected, if webcfg has mount points serving static files with gzip
static enabled.

Tune:
* toGzipRe = '\.(js|json|css|svg|txt|xml|html)$'
"""
    __slots__ = ()
    __TO_GZIP = '\.(js|json|css|svg|txt|xml|html|md)$'

    def autoDetect(self, config):
        if not config.get('packageGzipStatic', True):
            return False

        webcfg = config.get('webcfg', {})
        webroot = webcfg.get('root', '.')

        for (m, v) in webcfg.get('mounts', {}).items():
            if not isinstance(v, dict):
                continue

            if v.get('static', False):
                pass
            elif v.get('app', None) is None:
                pass
            else:
                continue

            if v.get('tune', {}).get('staticGzip', True):
                return True

        return False

    def _installTool(self, env):
        self._install.debrpm(['gzip'])
        self._install.emerge(['app-arch/gzip'])
        self._install.pacman(['gzip'])
        self._install.apk(['gzip'])
        self._install.brew('gzip')

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._detect.isAlpineLinux() and self._ospath.islink('/bin/gzip'):
            return

        super(gzipTool, self).initEnv(env, bin_name)

    def onBuild(self, config):
        if not self.autoDetect(config):
            return

        self._info('Generating GZip files of static content')
        webcfg = config.get('webcfg', {})
        webroot = webcfg.get('root', '.')
        re = self._ext.re
        to_gzip_re = self._getTune(config, 'toGzipRe', self.__TO_GZIP)
        to_gzip_re = re.compile(to_gzip_re, re.I)

        ospath = self._ospath
        gzip = self._ext.gzip
        shutil = self._ext.shutil

        for (m, v) in webcfg.get('mounts', {}).items():
            if not isinstance(v, dict):
                continue

            if v.get('static', False):
                pass
            elif v.get('app', None) is None:
                pass
            else:
                continue

            if not v.get('tune', {}).get('staticGzip', True):
                continue

            gzip_dir = ospath.join(webroot, m)
            gzip_dir = gzip_dir.lstrip('/')
            self._info('> ' + gzip_dir)

            for (path, dirs, files) in self._os.walk(gzip_dir):
                for f in files:
                    if to_gzip_re.search(f):
                        f = ospath.join(path, f)
                        with open(f, 'rb') as f_in:
                            with gzip.open(f + '.gz', 'wb', 9) as f_out:
                                shutil.copyfileobj(f_in, f_out)
