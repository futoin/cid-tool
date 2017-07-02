
from ..mixins.ondemand import ext as _ext


def isCentOS():
    return _ext.platform.linux_distribution()[0].startswith('CentOS')


def isFedora():
    return _ext.ospath.exists('/etc/fedora-release')


def isGentoo():
    return _ext.ospath.exists('/etc/gentoo-release')


def isArchLinux():
    # There are cases when platform.linux_distribution() is empty on Arch
    return (_ext.ospath.exists('/etc/arch-release') or
            _ext.platform.linux_distribution()[0].startswith('arch'))


def isDebian():
    return _ext.platform.linux_distribution()[0].startswith('debian')


def isUbuntu():
    return _ext.platform.linux_distribution()[0].startswith('Ubuntu')


def isOracleLinux():
    return _ext.platform.linux_distribution()[0].startswith('Oracle Linux')


def isRHEL():
    return _ext.platform.linux_distribution()[0].startswith('Red Hat Enterprise Linux')


def isOpenSUSE():
    return _ext.platform.linux_distribution()[0].startswith('openSUSE')


def isSLES():
    return _ext.platform.linux_distribution()[0].startswith('SUSE Linux Enterprise')


def isAlpineLinux():
    return _ext.ospath.exists('/etc/alpine-release')


def isLinux():
    return _ext.platform.system() == 'Linux'


def isMacOS():
    return _ext.platform.system() == 'Darwin'


def isAMD64():
    return _ext.platform.machine() == 'x86_64'


def osCodeName():
    codename = _ext.subprocess.check_output(['lsb_release', '-cs'])

    try:
        codename = str(codename, 'utf8')
    except:
        pass

    return codename.strip()


def isAdmin():
    return _ext.os.geteuid() == 0


def haveGroup(grpname):
    gid = _ext.grp.getgrnam(grpname)[2]
    return gid in _ext.os.getgroups()


def isSCLSupported():
    "Check if Software Collections are supported"
    return (
        isCentOS() or
        isRHEL() or
        isOracleLinux()
    )


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
