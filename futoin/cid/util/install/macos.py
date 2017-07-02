
from ...mixins.ondemand import ext as _ext
from .. import log as _log


def brewTap(tap):
    if not _ext.detect.isMacOS():
        return

    brew = _ext.path.which('brew')
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()
    _ext.exec.callExternal(brew_sudo + [brew, 'tap', tap], cwd='/')


def brewUnlink(formula=None, search=None):
    if not _ext.detect.isMacOS():
        return

    brew = _ext.path.which('brew')
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()

    flist = []

    if formula is not None:
        if isinstance(formula, list):
            flist += formula
        else:
            flist.append(formula)

    if search:
        flist += _ext.exec.callExternal([brew,
                                         'search', search], cwd='/').split()

    for f in flist:
        try:
            _ext.exec.callExternal(brew_sudo + [brew, 'unlink', f], cwd='/')
        except _ext.subprocess.CalledProcessError:
            _log.warn('You may need to unlink the formula manually!')


def brew(packages, cask=False):
    if not _ext.detect.isMacOS():
        return

    if not isinstance(packages, list):
        packages = [packages]

    brew = _ext.path.which('brew')
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()

    for package in packages:
        try:
            if cask:
                _ext.exec.callExternal(
                    brew_sudo + [brew, 'cask', 'install', package],
                    cwd='/',
                    user_interaction=True)
            elif brew == '/usr/local/bin/brew':
                _ext.exec.callExternal(
                    brew_sudo + [brew, 'install',
                                 '--force-bottle', package],
                    cwd='/')
            else:
                _ext.exec.callExternal(
                    brew_sudo + [brew, 'install', package],
                    cwd='/')
        except _ext.subprocess.CalledProcessError:
            _log.warn('You may need to enable the package manually')


def dmg(packages):
    if not _ext.detect.isMacOS():
        return

    if not isinstance(packages, list):
        packages = [packages]

    os = _ext.os
    path = _ext.path
    glob = _ext.glob

    curl = _ext.path.which('curl')
    hdiutil = _ext.path.which('hdiutil')
    installer = _ext.path.which('installer')
    volumes_dir = '/Volumes'

    for package in packages:
        base_name = package.split('/')[-1]
        local_name = os.path.join(os.environ['HOME'])

        # TODO: change to use env timeouts
        _ext.exec.callExternal([
            curl,
            '-fsSL',
            '--connect-timeout', '10',
            '--max-time', '300',
            '-o', base_name,
            package
        ])

        volumes = set(os.listdir(volumes_dir))
        _ext.exec.trySudoCall([hdiutil, 'attach', local_name])
        volume = (set(os.listdir(volumes_dir)) - volumes)[0]

        pkg = glob.glob(os.path.join(volumes_dir, volume, '*.pkg'))
        _ext.exec.trySudoCall([installer, '-package', pkg, '-target', '/'])

        _ext.exec.trySudoCall([hdiutil, 'dettach', local_name])
