
from ..mixins.ondemand import ext as _ext
from . import simple_memo as _simple_memo
from . import complex_memo as _complex_memo
from . import log as _log


@_simple_memo
def isCentOS():
    return _ext.platform.linux_distribution()[0].startswith('CentOS')


@_simple_memo
def isFedora():
    return _ext.ospath.exists('/etc/fedora-release')


@_simple_memo
def isGentoo():
    return _ext.ospath.exists('/etc/gentoo-release')


@_simple_memo
def isArchLinux():
    # There are cases when platform.linux_distribution() is empty on Arch
    return (_ext.ospath.exists('/etc/arch-release') or
            _ext.platform.linux_distribution()[0].startswith('arch'))


@_simple_memo
def isDebian():
    return _ext.platform.linux_distribution()[0].startswith('debian')


@_simple_memo
def isUbuntu():
    return _ext.platform.linux_distribution()[0].startswith('Ubuntu')


@_simple_memo
def isOracleLinux():
    return _ext.platform.linux_distribution()[0].startswith('Oracle Linux')


@_simple_memo
def isRHEL():
    return _ext.platform.linux_distribution()[0].startswith('Red Hat Enterprise Linux')


@_simple_memo
def isOpenSUSE():
    return _ext.platform.linux_distribution()[0].startswith('openSUSE')


@_simple_memo
def isSLES():
    return _ext.platform.linux_distribution()[0].startswith('SUSE Linux Enterprise')


@_simple_memo
def isAlpineLinux():
    return _ext.ospath.exists('/etc/alpine-release')


@_simple_memo
def alpineLinuxVersion():
    return _ext.pathutil.readTextFile('/etc/alpine-release').strip().split('.')


@_simple_memo
def linuxDistVersion():
    if isAlpineLinux():
        return alpineLinuxVersion()

    return _ext.platform.linux_distribution()[1]


def linuxDistMajorVer():
    return linuxDistVersion().split('.')[0]


@_simple_memo
def isLinux():
    return _ext.platform.system() == 'Linux'


@_simple_memo
def isMacOS():
    return _ext.platform.system() == 'Darwin'


@_simple_memo
def isAMD64():
    return _ext.platform.machine() == 'x86_64'


@_simple_memo
def basearch():
    return _ext.platform.machine()


@_simple_memo
def osCodeName():
    codename = _ext.subprocess.check_output(['lsb_release', '-cs'])
    codename = _ext.executil.toString(codename)
    return codename.strip()


@_simple_memo
def osRelease():
    codename = _ext.subprocess.check_output(['lsb_release', '-rs'])
    codename = _ext.executil.toString(codename)
    return codename.strip()


def isAdmin():
    return _ext.os.geteuid() == 0


@_complex_memo
def haveGroup(grpname):
    try:
        gid = _ext.grp.getgrnam(grpname)[2]
    except KeyError as e:
        _log.warn(str(e))
        return False

    return gid in _ext.os.getgroups()


@_simple_memo
def isSCLSupported():
    "Check if Software Collections are supported"
    return (
        isCentOS() or
        isRHEL() or
        isOracleLinux()
    )


@_simple_memo
def installerType():
    # Known OS
    #---
    if isDebian() or isUbuntu():
        return 'apt'

    if isArchLinux():
        return 'pacman'

    if isFedora():
        return 'dnf'

    if isCentOS() or isRHEL() or isOracleLinux():
        return 'yum'

    if isAlpineLinux():
        return 'apk'

    if isGentoo():
        return 'emerge'

    if isOpenSUSE() or isSLES():
        return 'zypper'

    if isMacOS():
        return 'brew'

    # Fallback
    #---
    pathutil = _ext.pathutil

    if pathutil.which('apt-get'):
        return 'apt'

    if pathutil.which('dnf'):
        return 'dnf'

    if pathutil.which('zypper'):
        return 'zypper'

    if pathutil.which('yum'):
        return 'yum'

    if pathutil.which('pacman'):
        return 'pacman'

    if _ext.ospath.exists('/sbin/apk'):
        return 'apk'

    if pathutil.which('emerge'):
        return 'emerge'

    return None


@_simple_memo
def packageType():
    installer = installerType()

    if installer == 'apt':
        return 'deb'

    if installer in ('dnf', 'zypper', 'yum'):
        return 'rpm'

    if installer == 'emerge':
        return 'ebuild'

    return installer


def isDeb():
    return packageType() == 'deb'


def isRPM():
    return packageType() == 'rpm'


def isEmerge():
    return installerType() == 'emerge'


def isApk():
    return installerType() == 'apk'


def isPacman():
    return installerType() == 'pacman'


def isBrew():
    return installerType() == 'brew'


def isYum():
    return installerType() == 'yum'


def isDnf():
    return installerType() == 'dnf'


def isZypper():
    return installerType() == 'zypper'


def isExternalToolsSetup(env):
    return env['externalSetup'] != False


def autoDetectByCfg(name, config, file_name):
    if name in config.get('toolOrder', []):
        return True

    if type(file_name) is type(''):
        file_name = [file_name]

    root_list = config['projectRootSet']

    for f in file_name:
        if f in root_list:
            return True

    return False
