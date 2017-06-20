#!/bin/bash

if ! test -e bin/cid; then
    echo "Invoke from CITool project root!"
    exit 1
fi

CID_BOOT=$(pwd)/bin/cid

# ArchLinux images comes without python
if ! which python >/dev/null; then
    which pacman && sudo pacman -S --noconfirm --needed python
    which dnf && sudo dnf install -y python
    which apt-get && sudo apt-get install -y python
fi

# Run test out of sync folder
export CIDTEST_USER=$(id -un)

if [ "$CIDTEST_USER" = "vagrant" ]; then
    export CIDTEST_RUN_DIR=/testrun
    CIDTEST_USER=cidtest
    sudo mkdir -p $CIDTEST_RUN_DIR
    id $CIDTEST_USER >/dev/null 2>&1 || \
        sudo useradd -U -s /bin/bash -d $CIDTEST_RUN_DIR $CIDTEST_USER
    sudo chown $CIDTEST_USER:$CIDTEST_USER $CIDTEST_RUN_DIR
    
    sudo chmod go+rx $HOME
    
    HOME=$HOME/fake
    mkdir -p $HOME
    sudo chmod go+rwx $HOME
    umask 0000
    
    sudo mkdir -p /etc/futoin && sudo chmod 777 /etc/futoin

    sudo grep -q $CIDTEST_USER /etc/sudoers || \
        $CID_BOOT sudoers $CIDTEST_USER | sudo sh -c 'cat >> /etc/sudoers'
fi

if ! grep -q "$(hostname)" /etc/hosts; then
    echo "127.0.0.1 $(hostname)" | sudo tee /etc/hosts
fi

fast=
rmshost=
tests=

if [ "$1" = 'rmshost' ]; then
    rmshost=rmshost
    fast=fast
    tests='tests/cid_rmshost_test.py'
    shift 1
fi

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
    export CIDTEST_NO_COMPILE=0
fi


if [ -n "$tests" ]; then
    :
elif [ -z "$1" ]; then
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

        sudo sudo -u $CIDTEST_USER bash <<EOF
        export HOME=$HOME
        export CIDTEST_RUN_DIR=$CIDTEST_RUN_DIR
        export CIDTEST_BIN=$CIDTEST_BIN
        export CIDTEST_NO_COMPILE=$CIDTEST_NO_COMPILE
        export pythonVer=$pythonVer
        \$CIDTEST_BIN tool exec python -- -m nose $tests
EOF
    )   
}

if [ "$fast" != 'fast' ]; then
    run_common 3
    run_common 2
else
    run_common $(python -c 'import sys; sys.stdout.write(str(sys.version_info.major))')
fi