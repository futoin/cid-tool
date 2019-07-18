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

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn
from .rvmtool import rvmTool


class rubyTool(BashToolMixIn, RuntimeTool):
    """Ruby is a dynamic, open source programming language.

Home: https://www.ruby-lang.org/en/

By default the latest available Ruby binary is used for the following OSes:
* Debian & Ubuntu - uses Brightbox builds 1.9, 2.0, 2.1, 2.2, 2.3, 2.4.
* CentOS, RHEL & Oracle Linux - uses SCL 1.9, 2.0, 2.2, 2.3

You can forbid source builds by setting rubyBinOnly to non-empty string.

Otherwise, System Ruby is used by default.

If rubyVer is set then RVM is used to setup custom rubies.
That may lead to long time and resource consumption due to compilation,
if binary versions are not found for specific system.

Note: RUBY_ENV and RAILS_ENV are set based on rubyEnv or .env.type
"""
    __slots__ = ()

    def getDeps(self):
        return ['rvm']

    def _installTool(self, env):
        rvmTool('rvm').ensureGpgKeys(env)

        if env['rubyFoundBinary']:
            self._installBinaries(env)
            return

        self._buildDeps(env)
        self._executil.callExternal([
            env['rvmBin'], 'install', env['rubySourceVer'], '--autolibs=read-only'
        ])
        self._executil.callExternal([
            env['rvmBin'], 'cleanup', 'all'
        ])

    def _installBinaries(self, env):
        detect = self._detect
        install = self._install
        pathutil = self._pathutil
        executil = self._executil

        ver = env['rubyVer']
        rvm_ruby_ver = 'system-{0}'.format(ver)
        pkgver = ver

        if detect.isDebian() or detect.isUbuntu():
            code_name = self._detect.osCodeName()

            if code_name in ['stretch']:
                install.aptRepo('jessie-ssl10bp',
                                'deb http://deb.debian.org/debian jessie-backports main')

            repo = env['rubyBrightboxRepo']

            install.aptRepo(
                'brightbox-ruby',
                "deb {0} $codename$ main".format(repo),
                self._GPG_BIRGHTBOX_REPO,
                codename_map={
                    # Ubuntu
                    # Debian
                    'jessie': 'trusty',
                    'stretch': 'xenial',
                    'buster': 'bionic',
                    'testing': 'bionic',
                    'sid': 'bionic',
                },
                repo_base='{0}/dists'.format(repo)
            )

            if ver == '1.9':
                pkgver = '1.9.[0-9]'

            if detect.isDebian():
                UBUNTU_MIRROR = 'https://debian.charite.de/ubuntu'
                pkg = UBUNTU_MIRROR + '/pool/main/r/readline6/libreadline6_6.3-8ubuntu2_amd64.deb'
                install.dpkg(env, 'libreadline6', pkg)

                pkg = UBUNTU_MIRROR + '/pool/main/g/gdbm/libgdbm5_1.14.1-6_amd64.deb'
                install.dpkg(env, 'libgdbm5', pkg)

            install.deb([
                'ruby{0}'.format(pkgver),
                'ruby{0}-dev'.format(pkgver),
            ])
            ruby_bins = self._ext.glob.glob('/usr/bin/ruby{0}*'.format(ver))

            if len(ruby_bins) == 0:
                self._errorExit('No Ruby found for version {0}'.format(ver))

            ruby_bin = ruby_bins[0]

        elif detect.isSCLSupported():
            sclname = self._rubySCLName(ver)

            install.yumSCL()

            install.yum(sclname)

            # required for LD_LIBRARY_PATH
            env_to_set = executil.callExternal(
                ['scl', 'enable', sclname, 'env'], verbose=False)
            pathutil.updateEnvFromOutput(env_to_set)

            ruby_bin = executil.callExternal(
                ['scl', 'enable', sclname, 'which ruby'], verbose=False).strip()

        elif detect.isMacOS():
            formula = 'ruby@{0}'.format(ver)
            install.brew(formula)
            return
        else:
            self._systemDeps()
            rvm_ruby_ver = 'system'
            ruby_bin = pathutil.which('ruby')

        executil.callExternal([
            env['rvmBin'], 'remove', 'ext-{0}'.format(rvm_ruby_ver)
        ], suppress_fail=True)

        executil.callExternal([
            env['rvmBin'], 'mount', ruby_bin, '-n', rvm_ruby_ver
        ])

    def _rubySCLName(self, ver):
        pkgver = ver.replace('.', '')

        if pkgver == '19':
            sclname = 'ruby193'
        elif pkgver == '20':
            sclname = 'ruby200'
        else:
            sclname = 'rh-ruby' + pkgver

        return sclname

    def _fixRvmLinks(self, env, name, ver):
        ospath = self._ospath
        os = self._os
        glob = self._ext.glob
        bin_dir = ospath.join(env['rvmDir'], 'rubies', name, 'bin')

        for f in ['erb', 'gem', 'irb', 'rake', 'rdoc', 'ri', 'ruby', 'testrb']:
            f = ospath.join(bin_dir, f)
            res = glob.glob('{0}{1}*'.format(f, ver))

            if res:
                res = ospath.basename(res[0])

                if os.readlink(f) == res:
                    continue

                try:
                    os.unlink(f)
                except Exception as e:
                    self._warn(str(e))

                os.symlink(res, f)

    def _updateTool(self, env):
        if not env['rubyFoundBinary']:
            self._installTool(env)

    def uninstallTool(self, env):
        ruby_ver = env['rubyVer']

        if not env['rubyFoundBinary']:
            self._executil.callExternal([
                env['rvmBin'], 'uninstall', env['rubyVer']
            ])
            self._have_tool = False

    def envNames(self):
        return ['rubyVer', 'rubyBin', 'rubyBinOnly', 'rubyForceBuild', 'rubySourceVer', 'rubyEnv']

    def initEnv(self, env):
        environ = self._environ
        ospath = self._ospath
        detect = self._detect
        path = self._pathutil

        # ---
        ruby_env = env.get('rubyEnv', '')

        if ruby_env:
            pass
        elif env['type'] == 'dev':
            ruby_env = 'development'
        else:
            ruby_env = 'production'

        environ['RUBY_ENV'] = ruby_env
        environ['RAILS_ENV'] = ruby_env

        # ---
        if 'GEM_HOME' in environ:
            path.delEnvPath('PATH', environ['GEM_HOME'])
            path.delEnvPath('GEM_PATH', environ['GEM_HOME'])
            del environ['GEM_HOME']

        # ---
        rubyForceBuild = env.setdefault('rubyForceBuild', False)
        rubyBinOnly = env.setdefault('rubyBinOnly', not rubyForceBuild)

        if rubyBinOnly and rubyForceBuild:
            self._warn('"rubyBinOnly" and "rubyForceBuild" do not make sense'
                       ' when set together!')

        # ---
        if detect.isDebian() or detect.isUbuntu():
            bb_repo = 'http://ppa.launchpad.net/brightbox/ruby-ng/ubuntu'
            ruby_binaries = ['1.9', '2.0', '2.1',
                             '2.2', '2.3', '2.4', '2.5', '2.6']

            code_name = self._detect.osCodeName()

            if code_name in []:
                # 1.9 build is broken on LaunchPad
                bb_repo = 'http://ppa.launchpad.net/brightbox/ruby-ng-experimental/ubuntu'

            env.setdefault('rubyBrightboxRepo', bb_repo)

        elif detect.isSCLSupported():
            if detect.isCentOS():
                ruby_binaries = ['1.9', '2.0', '2.2', '2.3', '2.4', '2.5']
            else:
                ruby_binaries = ['1.9', '2.0', '2.2', '2.3', '2.4', '2.5']
        elif detect.isMacOS():
            ruby_binaries = ['1.8', '1.9', '2.0',
                             '2.2', '2.3', '2.4', '2.5', '2.6']
        else:
            ruby_binaries = None

        # ---
        if ruby_binaries and not rubyForceBuild:
            ruby_ver = env.setdefault('rubyVer', ruby_binaries[-1])
            foundBinary = ruby_ver in ruby_binaries

            rvm_ruby_ver = ruby_ver

            if foundBinary:
                rvm_ruby_ver = 'ext-system-{0}'.format(ruby_ver)

                # required for LD_LIBRARY_PATH
                if detect.isSCLSupported():
                    sclname = self._rubySCLName(ruby_ver)

                    try:
                        env_to_set = self._executil.callExternal(
                            ['scl', 'enable', sclname, 'env'], verbose=False)
                        self._pathutil.updateEnvFromOutput(env_to_set)
                    except self._ext.subprocess.CalledProcessError:
                        pass
                    except OSError:
                        pass
                elif detect.isMacOS():
                    env['rubyFoundBinary'] = True
                    formula = 'ruby@{0}'.format(ruby_ver)
                    brew_prefix = env['brewDir']
                    ruby_bin_dir = ospath.join(
                        brew_prefix, 'opt', formula, 'bin')

                    if ospath.exists(ruby_bin_dir):
                        self._pathutil.addBinPath(ruby_bin_dir, True)
                        super(rubyTool, self).initEnv(env)
                        self._environ['rubyVer'] = ruby_ver
                    return
                elif detect.isDebian() or detect.isUbuntu():
                    self._fixRvmLinks(env, rvm_ruby_ver, ruby_ver)
        else:
            ruby_ver = env.setdefault('rubyVer', self.SYSTEM_VER)
            foundBinary = ruby_ver == self.SYSTEM_VER
            rvm_ruby_ver = foundBinary and ruby_ver or 'ext-system'

        # ---
        rvm_dir = env['rvmDir']
        env['rubyFoundBinary'] = foundBinary

        if rubyForceBuild or not foundBinary:
            rvm_ruby_ver = env.setdefault('rubySourceVer', ruby_ver or 'ruby')

        try:
            env_to_set = self._callBash(env,
                                        'source {0} && \
                rvm use {1} >/dev/null && \
                env | grep "rvm"'.format(env['rvmInit'], rvm_ruby_ver),
                                        verbose=False
                                        )
        except:
            return

        if env_to_set:
            self._pathutil.updateEnvFromOutput(env_to_set)
            super(rubyTool, self).initEnv(env)
            self._environ['rubyVer'] = ruby_ver

    def _buildDeps(self, env):
        self._builddep.require(env, 'ssl')

        # APT
        # ---
        self._install.deb([
            'build-essential',
            'gawk',
            'make',
            'libc6-dev',
            'zlib1g-dev',
            'libyaml-dev',
            'libsqlite3-dev',
            'sqlite3',
            'autoconf',
            'libgmp-dev',
            'libgdbm-dev',
            'libncurses5-dev',
            'automake',
            'libtool',
            'bison',
            'pkg-config',
            'libffi-dev',
            'libgmp-dev',
            'libreadline-dev',
        ])

        # Extra repo before the rest
        # ---
        self._install.yumEPEL()

        self._install.rpm([
            'binutils',
            'patch',
            'libyaml-devel',
            'autoconf',
            'gcc',
            'gcc-c++',
            'glibc-devel',
            'readline-devel',
            'zlib-devel',
            'libffi-devel',
            'automake',
            'libtool',
            'bison',
            'sqlite-devel',
            'make',
            'm4',
            'gdbm-devel',
            'sqlite3-devel',
        ])

        # ---
        self._install.emergeDepsOnly(['dev-lang/ruby'])
        self._install.pacman(['ruby'])
        self._install.apk('build-base')

    def _systemDeps(self):
        self._install.debrpm(['ruby'])
        self._install.emerge(['dev-lang/ruby'])
        self._install.pacman(['ruby'])
        self._install.apk(['ruby',
                           'ruby-bigdecimal',
                           'ruby-libs',
                           'ruby-io-console',
                           'ruby-irb',
                           'ruby-json',
                           'ruby-minitest',
                           'ruby-net-telnet',
                           'ruby-power_assert',
                           'ruby-xmlrpc'
                           ])

    _GPG_BIRGHTBOX_REPO = '''
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: SKS 1.1.6
Comment: Hostname: keyserver.ubuntu.com

mI0ETKTCMQEEAMX3ttL4YFO5AQ7Z6L5gaGw57CJBQl6jCv6lka0p8DaGNkeX0Rs9DhINa8qR
hxJCPK6ijeoNss69G/ni+sMSRViJBFWXzitEE1ew5YM2sw7wLE3guToDu60kaDwIn5mR3GTx
cgqDrQeCuGZJgz3e2lgmGYw2rAhMe78rRgkR5GFvABEBAAG0G0xhdW5jaHBhZCBQUEEgZm9y
IEJyaWdodGJveIi4BBMBAgAiBQJMpMIxAhsDBgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAK
CRD12l8Jwxc6pl2BA/4p5DFEpGVvkgLj7/YLYCtYmZDw8i/drGbkWfIQiOgPWIf8QgpJXVME
1tkH8N1ssjbJlUKl/HubNBKZ6HDyQsQASFug+eI6KhSFMScDBf/oMX3zVCTTvUkgJtOWYc5d
77zJacEUGoSEx63QUJVvp/LAnqkZbt17JJL6HOou/CNicw==
=G8vE
-----END PGP PUBLIC KEY BLOCK-----
'''

    def tuneDefaults(self, env):
        return {
            'minMemory': '8M',
            'socketType': 'none',
            'scalable': False,
            'reloadable': False,
            'multiCore': True,
        }
