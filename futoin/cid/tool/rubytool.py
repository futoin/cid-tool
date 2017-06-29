
import glob
import subprocess
import os

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn


class rubyTool(BashToolMixIn, RuntimeTool):
    """Ruby is a dynamic, open source programming language.

Home: https://www.ruby-lang.org/en/

By default the latest available Ruby binary is used for the following OSes:
* Debian & Ubuntu - uses Brightbox builds 1.9, 2.0, 2.1, 2.2, 2.3.
* CentOS, RHEL & Oracle Linux - uses SCL 1.9, 2.0, 2.2, 2.3

You can forbid source builds by setting rubyBinOnly to non-empty string.

Otherwise, System Ruby is used by default.

If rubyVer is set then RVM is used to setup custom rubies.
That may lead to long time and resource consumption due to compilation,
if binary versions are not found for specific system.
"""

    def getDeps(self):
        return ['rvm']

    def _installTool(self, env):
        ruby_ver = env['rubyVer']

        if ruby_ver == self.SYSTEM_VER:
            self._systemDeps()
            return

        if env['rubyBinOnly']:
            self._installBinaries(env)
            return

        self._buildDeps()
        self._callExternal([
            env['rvmBin'], 'install', ruby_ver, '--autolibs=read-only'
        ])
        self._callExternal([
            env['rvmBin'], 'cleanup', 'all'
        ])

    def _installBinaries(self, env):
        ver = env['rubyVer']
        pkgver = ver

        if self._isDebian() or self._isUbuntu():
            if self._osCodeName() == 'stretch':
                self._requireDeb(['equivs', 'libssl1.0.2'])
                cwd = os.getcwd()
                try:
                    tmpdir = self._tmpCacheDir(prefix='equivs-')
                    self._writeTextFile(
                        'libssl1.0.0', self._FAKE_LIBSSL100_DEB)
                    equivsbuild = self._which('equivs-build')
                    dpkg = self._which('dpkg')
                    self._callExternal([equivsbuild, 'libssl1.0.0'])
                    self._trySudoCall(
                        [dpkg, '-i', 'libssl1.0.0_1.0.2l_all.deb'])
                finally:
                    os.chdir(cwd)

            repo = env['rubyBrightboxRepo']

            self._addAptRepo(
                'brightbox-ruby',
                "deb {0} $codename$ main".format(repo),
                self._GPG_BIRGHTBOX_REPO,
                codename_map={
                    # Ubuntu
                    #'zesty': 'yakkety',
                    # Debian
                    'jessie': 'trusty',
                    'stretch': 'zesty',
                    'testing': 'zesty',
                    'sid': 'zesty',
                },
                repo_base='{0}/dists'.format(repo)
            )

            if ver == '1.9':
                pkgver = '1.9.[0-9]'
            self._requireDeb([
                'ruby{0}'.format(pkgver),
                'ruby{0}-dev'.format(pkgver),
            ])
            ruby_bin = glob.glob('/usr/bin/ruby{0}*'.format(ver))[0]

        elif self._isSCLSupported():
            sclname = self._rubySCLName(ver)

            self._requireSCL()

            self._requireYum(sclname)

            # required for LD_LIBRARY_PATH
            env_to_set = self._callExternal(
                ['scl', 'enable', sclname, 'env'], verbose=False)
            self._updateEnvFromOutput(env_to_set)

            ruby_bin = self._callExternal(
                ['scl', 'enable', sclname, 'which ruby'], verbose=False).strip()

        elif self._isMacOS():
            formula = 'ruby@{0}'.format(ver)
            self._requireBrew(formula)
            return
        else:
            self._systemDeps()
            return

        self._callExternal([
            env['rvmBin'], 'remove', 'ext-system-{0}'.format(ver)
        ], suppress_fail=True)

        self._callExternal([
            env['rvmBin'], 'mount', ruby_bin, '-n', 'system-{0}'.format(ver)
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
        bin_dir = os.path.join(env['rvmDir'], 'rubies', name, 'bin')

        for f in ['erb', 'gem', 'irb', 'rake', 'rdoc', 'ri', 'ruby', 'testrb']:
            f = os.path.join(bin_dir, f)
            res = glob.glob('{0}{1}*'.format(f, ver))

            if res:
                try:
                    os.unlink(f)
                except:
                    pass

                os.symlink(res[0], f)

    def updateTool(self, env):
        if env['rubyVer'] != self.SYSTEM_VER and not env['rubyBinOnly']:
            self._installTool(env)

    def uninstallTool(self, env):
        ruby_ver = env['rubyVer']

        if ruby_ver != self.SYSTEM_VER and not env['rubyBinOnly']:
            self._callExternal([
                env['rvmBin'], 'uninstall', env['rubyVer']
            ])
            self._have_tool = False

    def envNames(self):
        return ['rubyVer', 'rubyBin', 'rubyBinOnly']

    def initEnv(self, env):
        #---
        if self._isDebian() or self._isUbuntu():
            bb_repo = 'http://ppa.launchpad.net/brightbox/ruby-ng/ubuntu'
            ruby_binaries = ['1.9', '2.0', '2.1', '2.2', '2.3']

            code_name = self._osCodeName()

            if code_name == 'zesty':
                # 1.9 build is broken on LaunchPad
                bb_repo = 'http://ppa.launchpad.net/brightbox/ruby-ng-experimental/ubuntu'
            elif code_name == 'stretch':
                ruby_binaries = None

            env.setdefault('rubyBrightboxRepo', bb_repo)

        elif self._isSCLSupported():
            ruby_binaries = ['1.9', '2.0', '2.2', '2.3', '2.4']
        elif self._isMacOS():
            ruby_binaries = ['1.8', '1.9', '2.0', '2.2', '2.3', '2.4']
        else:
            ruby_binaries = None

        #---
        if ruby_binaries:
            ruby_ver = env.setdefault('rubyVer', ruby_binaries[-1])
            rubyBinOnly = ruby_ver in ruby_binaries

            rvm_ruby_ver = ruby_ver

            if rubyBinOnly:
                rvm_ruby_ver = 'ext-system-{0}'.format(ruby_ver)

                # required for LD_LIBRARY_PATH
                if self._isSCLSupported():
                    sclname = self._rubySCLName(ruby_ver)

                    try:
                        env_to_set = self._callExternal(
                            ['scl', 'enable', sclname, 'env'], verbose=False)
                        self._updateEnvFromOutput(env_to_set)
                    except subprocess.CalledProcessError:
                        pass
                elif self._isMacOS():
                    env['rubyBinOnly'] = True
                    formula = 'ruby@{0}'.format(ruby_ver)
                    brew_prefix = env['brewDir']
                    ruby_bin_dir = os.path.join(
                        brew_prefix, 'opt', formula, 'bin')

                    if os.path.exists(ruby_bin_dir):
                        self._addBinPath(ruby_bin_dir, True)
                        super(rubyTool, self).initEnv(env)
                    return
                elif self._isDebian() or self._isUbuntu():
                    self._fixRvmLinks(env, rvm_ruby_ver, ruby_ver)
        else:
            rubyBinOnly = False
            ruby_ver = env.setdefault('rubyVer', self.SYSTEM_VER)
            rvm_ruby_ver = ruby_ver

        if rubyBinOnly:
            env['rubyBinOnly'] = rubyBinOnly
        else:
            rubyBinOnly = env.setdefault('rubyBinOnly', rubyBinOnly)

        #---
        rvm_dir = env['rvmDir']

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
            self._updateEnvFromOutput(env_to_set)
            super(rubyTool, self).initEnv(env)

    def _buildDeps(self):
        # APT
        #---
        self._requireDeb([
            'build-essential',
            'gawk',
            'libssl-dev',
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
        #---
        self._requireYumEPEL()

        self._requireRpm([
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
            'openssl-devel',
            'automake',
            'libtool',
            'bison',
            'sqlite-devel',
            'make',
            'm4',
            'gdbm-devel',
            'libopenssl-devel',
            'sqlite3-devel',
        ])

        #---
        self._requireEmergeDepsOnly(['dev-lang/ruby'])
        self._requirePacman(['ruby'])
        self._requireApk('build-base')

    def _systemDeps(self):
        self._requirePackages(['ruby'])
        self._requireEmerge(['dev-lang/ruby'])
        self._requirePacman(['ruby'])
        self._requireApk(['ruby',
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

    _FAKE_LIBSSL100_DEB = """
Section: misc
Priority: optional
Standards-Version: 3.9.2

Package: libssl1.0.0
Version: 1.0.2l
Depends: libssl1.0.2 (>= 1.0.2l)
Architecture: all
Description: Dummy libssl1.0.0 package for dep resolution.
 Required due to lack of libssl1.0.0 on Stretch
"""

    def tuneDefaults(self):
        return {
            'minMemory': '8M',
            'socketType': 'none',
            'scalable': False,
        }
