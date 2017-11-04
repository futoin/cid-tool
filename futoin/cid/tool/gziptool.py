#
# Copyright 2015-2017 (c) Andrey Galkin
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
    __TO_GZIP = '\.(js|json|css|svg|txt|xml|html)$'

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
            elif m == '/' and webroot.get('main', None) is not None:
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
        webroot = config.get('webcfg', {}).get('root', '.')
        re = self._ext.re
        to_gzip_re = self._getTune(config, 'toGzipRe', self.__TO_GZIP)
        to_gzip_re = re.compile(to_gzip_re, re.I)

        ospath = self._ospath
        gzip = self._ext.gzip
        shutil = self._ext.shutil

        for (path, dirs, files) in self._os.walk(webroot):
            for f in files:
                if to_gzip_re.search(f):
                    f = ospath.join(path, f)
                    with open(f, 'rb') as f_in:
                        with gzip.open(f + '.gz', 'wb', 9) as f_out:
                            shutil.copyfileobj(f_in, f_out)
