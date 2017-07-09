
from ...mixins.ondemand import ext as _ext

_pacman = _ext.pathutil.which('pacman')


def pacman(packages):
    if _pacman:
        packages = _ext.configutil.listify(packages)

        _ext.executil.trySudoCall(
            [_pacman, '-S', '--noconfirm', '--needed'] + packages,
            errmsg='you may need to install the build deps manually !'
        )
