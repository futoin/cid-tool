#!/bin/bash

if ! test -e bin/cid; then
    echo "Invoke from CITool project root!"
    exit 1
fi

# ArchLinux images comes without python
if ! which python >/dev/null; then
    which pacman && sudo pacman -S --noconfirm --needed python
    which dnf && sudo dnf install -y python
    which apt-get && sudo apt-get install -y python
fi

# Run test out of sync folder
if [ "$(id -un)" = "vagrant" ]; then
    export CIDTEST_RUN_DIR=/testrun
    sudo mkdir -p $CIDTEST_RUN_DIR
    sudo chown vagrant:$(id -gn) $CIDTEST_RUN_DIR
fi

if ! grep -q "$(hostname)" /etc/hosts; then
    echo "127.0.0.1 $(hostname)" | sudo tee /etc/hosts
fi

CID_BOOT=$(pwd)/bin/cid

if [ "$1" = 'fast' ]; then
    fast=fast
    shift 1
fi

if [ "$1" = 'frompip' ]; then
    frompip=frompip
    shift 1
    # make it fresh after editable mode
    sudo rm -rf ~/.virtualenv-*
    pip_install_opts="--upgrade --no-cache-dir futoin-cid"
else
    pip_install_opts="-e $(pwd)"
fi

if [ "$1" = 'nocompile' ]; then
    export CIDTEST_NO_COMPILE=1
    shift 1
else
    unset CIDTEST_NO_COMPILE
fi


if [ -z "$1" ]; then
    tests=
    tests+=" tests/cid_vcs_test.py"
    tests+=" tests/cid_rms_test.py"    
    tests+=" tests/cid_install_test.py"
    tests+=" tests/cid_buildtool_test.py"
    tests+=" tests/cid_runcmd_test.py"
    tests+=" tests/cid_initcmd_test.py"
    tests+=" tests/cid_misc_test.py"
else
    tests="$*"
fi

# CentOS 6
[ -e /opt/rh/python27/enable ] && source /opt/rh/python27/enable 

# Workaround, if docker is not enabled by default
which docker >/dev/null 2>&1 && sudo systemctl start docker

function run_common() {
    (
        export pythonVer=$1
        echo "Python $pythonVer"
        
        $CID_BOOT tool exec pip -- install $pip_install_opts
        eval $($CID_BOOT tool env virtualenv)
        export CIDTEST_BIN=$(which cid)
        
        $CIDTEST_BIN tool exec pip -- install nose
        $CIDTEST_BIN tool exec python -- -m nose $tests
    )   
}

if [ "$fast" != 'fast' ]; then
    run_common 3
    run_common 2
else
    run_common $(python -c 'import sys; sys.stdout.write(str(sys.version_info.major))')
fi