
from .apk import *
from .deb import *
from .ebuild import *
from .macos import *
from .pacman import *
from .rpm import *


def debrpm(packages):
    deb(packages)
    rpm(packages)


def generic(packages):
    apk(packages)
    deb(packages)
    brew(packages)
    pacman(packages)
    rpm(packages)

    # too different
    # emerge(packages)
