
from ...mixins.ondemand import ext as _ext
from .. import log as _log


def _brew():
    brew = globals().get('_brew_bin', None)

    if brew is None:
        brew = _ext.pathutil.which('brew')
        globals()['_brew_bin'] = brew

    return brew


def brewTap(tap):
    if not _ext.detect.isMacOS():
        return

    brew = _brew()
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()
    _ext.executil.callExternal(brew_sudo + [brew, 'tap', tap], cwd='/')


def brewUnlink(formula=None, search=None):
    if not _ext.detect.isMacOS():
        return

    brew = _brew()
    brew_sudo = _ext.os.environ.get('brewSudo', '').split()

    flist = []

    if formula is not None:
        formula = _ext.configutil.listify(formula)
        flist += formula

    if search:
        flist += _ext.executil.callExternal([brew,
                                             'search', search], cwd='/').split()

    for f in flist:
        try:
            _ext.executil.callExternal(
                brew_sudo + [brew, 'unlink', f], cwd='/')
        except _ext.subprocess.CalledProcessError:
            _log.warn('You may need to unlink the formula manually!')


def brew(packages, cask=False):
    if not _ext.detect.isMacOS():
        return

    packages = _ext.configutil.listify(packages)

    os = _ext.os
    brew = _brew()
    brew_sudo = os.environ.get('brewSudo', '').split()
    saved_mask = os.umask(0o022)

    try:
        for package in packages:
            try:
                if cask:
                    _ext.executil.callExternal(
                        brew_sudo + [brew, 'cask', 'install', package],
                        cwd='/',
                        user_interaction=True)
                elif brew == '/usr/local/bin/brew':
                    _ext.executil.callExternal(
                        brew_sudo + [brew, 'install',
                                     '--force-bottle', package],
                        cwd='/')
                else:
                    _ext.executil.callExternal(
                        brew_sudo + [brew, 'install', package],
                        cwd='/')
            except _ext.subprocess.CalledProcessError:
                _log.warn('You may need to enable the package manually')
    finally:
        os.umask(saved_mask)


def dmg(packages):
    if not _ext.detect.isMacOS():
        return

    packages = _ext.configutil.listify(packages)

    os = _ext.os
    path = _ext.pathutil
    glob = _ext.glob

    curl = _ext.pathutil.which('curl')
    hdiutil = _ext.pathutil.which('hdiutil')
    installer = _ext.pathutil.which('installer')
    volumes_dir = '/Volumes'

    for package in packages:
        base_name = package.split('/')[-1]
        local_name = os.path.join(os.environ['HOME'])

        # TODO: change to use env timeouts
        _ext.executil.callExternal([
            curl,
            '-fsSL',
            '--connect-timeout', '10',
            '--max-time', '300',
            '-o', base_name,
            package
        ])

        volumes = set(os.listdir(volumes_dir))
        _ext.executil.trySudoCall([hdiutil, 'attach', local_name])
        volume = (set(os.listdir(volumes_dir)) - volumes)[0]

        pkg = glob.glob(os.path.join(volumes_dir, volume, '*.pkg'))
        _ext.executil.trySudoCall([installer, '-package', pkg, '-target', '/'])

        _ext.executil.trySudoCall([hdiutil, 'dettach', local_name])
