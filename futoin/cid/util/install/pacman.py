
from ...mixins.ondemand import ext as _ext


def pacman(packages):
    pacman = _ext.path.which('pacman')

    if pacman:
        if not isinstance(packages, list):
            packages = [packages]

        _ext.exec.trySudoCall(
            [pacman, '-S', '--noconfirm', '--needed'] + packages,
            errmsg='you may need to install the build deps manually !'
        )
