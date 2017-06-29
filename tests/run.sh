#!/bin/bash

if ! test -e bin/cid; then
    echo "Invoke from CID Tool project root!"
    exit 1
fi

CID_SOURCE_DIR=$(pwd)
CID_BOOT=${CID_SOURCE_DIR}/bin/cid
TEST_ROOT=${CID_SOURCE_DIR}

# go out of project root to avoid tool autodetection
cd ..
CWD=$(pwd) 

if [ ${CWD} = '/' ]; then
    export CIDTEST_RUN_DIR=/testrun
else
    export CIDTEST_RUN_DIR=${CWD}/testrun
fi

# ArchLinux images comes without python
if ! which python >/dev/null; then
    which pacman && sudo pacman -S --noconfirm --needed python
    which dnf && sudo dnf install -y python
    which apt-get && sudo apt-get install --no-install-recommends -y python
    which apk && sudo apk add python2
fi

# Run test out of sync folder
export CIDTEST_USER=$(id -un)

if [ "$CIDTEST_USER" = "vagrant" ]; then
    CIDTEST_USER=cidtest
    sudo mkdir -p $CIDTEST_RUN_DIR
    if ! id $CIDTEST_USER >/dev/null 2>&1; then
        if [ -e /usr/sbin/useradd ]; then
            sudo /usr/sbin/useradd -U -s /bin/bash -d $CIDTEST_RUN_DIR $CIDTEST_USER
        elif [ -e /usr/sbin/addgroup ]; then
            sudo addgroup $CIDTEST_USER;
            sudo adduser -DH -s /bin/bash -h $CIDTEST_RUN_DIR -G $CIDTEST_USER $CIDTEST_USER
        elif [ -e /usr/bin/dscl ]; then
            sudo -H bash <<EOF
                dscl . create /Groups/$CIDTEST_USER
                dscl . create /Groups/$CIDTEST_USER RealName “CID Test”
                dscl . create /Groups/$CIDTEST_USER gid 1010
                
                dscl . -create /Users/$CIDTEST_USER
                dscl . -create /Users/$CIDTEST_USER UserShell /bin/bash
                dscl . -create /Users/$CIDTEST_USER RealName "CID Test" 
                dscl . -create /Users/$CIDTEST_USER UniqueID "1010"
                dscl . -create /Users/$CIDTEST_USER PrimaryGroupID 1010
                dscl . -create /Users/$CIDTEST_USER NFSHomeDirectory $CIDTEST_RUN_DIR

                dscl . -append /Groups/$CIDTEST_USER GroupMembership $CIDTEST_USER
                
                mkdir -p $CIDTEST_RUN_DIR/Library/Caches
EOF
        fi
    fi
    
    sudo chown -R $CIDTEST_USER:$CIDTEST_USER $CIDTEST_RUN_DIR
    
    sudo chmod go+rx $HOME
    
    HOME=$(dirname $HOME)/fake
    sudo mkdir -p $HOME
    sudo chmod go+rwx $HOME
    umask 0000
    
    sudo mkdir -p /etc/futoin && sudo chmod 777 /etc/futoin

    if [ -d /etc/sudoers.d ]; then
        $CID_BOOT sudoers $CIDTEST_USER | sudo tee /etc/sudoers.d/cidtest
        sudo chmod 400 /etc/sudoers.d/cidtest
        sudo egrep -q '^#includedir\s+/etc/sudoers.d\s*$' /etc/sudoers || \
            echo '#includedir /etc/sudoers.d' | sudo tee -a /etc/sudoers
    else
        sudo grep -q $CIDTEST_USER /etc/sudoers || \
            $CID_BOOT sudoers $CIDTEST_USER | sudo tee -a /etc/sudoers
    fi
    
    # Alpine Linux, etc.
    sudo grep -q root /etc/sudoers || \
        sudo sh -c 'echo "root    ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers'
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
    sudo rm -rf ${HOME}/.virtualenv-*
    pip_install_opts="--upgrade --no-cache-dir futoin-cid"
    unset CID_SOURCE_DIR
else
    export CID_SOURCE_DIR
    pip_install_opts="-e ${CID_SOURCE_DIR}"
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
    tests+=" tests/cid_deploy_test.py"
    tests+=" tests/cid_service_test.py"
    tests+=" tests/cid_realapp_test.py"
    tests+=" tests/cid_misc_test.py"
else
    tests="$*"
fi

tests=$(for t in $tests; do [[ $t =~ ^tests/ ]] && echo -n ${TEST_ROOT}/$t || echo -n $t; echo -n ' '; done)

# CentOS 6
[ -e /opt/rh/python27/enable ] && source /opt/rh/python27/enable 

# Workaround, if docker is not enabled by default
which docker >/dev/null 2>&1 && (
    sudo systemctl start docker ||
    sudo rc-service docker start
)

which systemctl >/dev/null 2>&1 && sudo systemctl mask \
    nginx.service \
    apache2.service \
    php7.0-fpm.service \
    php7.1-fpm.service \
    php7-fpm.service \
    php5-fpm.service
    
sudo rm -f $CIDTEST_RUN_DIR/stdout.log $CIDTEST_RUN_DIR/stderr.log

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
        if [ -n "$CID_SOURCE_DIR" ]; then
            export CID_SOURCE_DIR=$CID_SOURCE_DIR
        fi
        export pythonVer=$pythonVer
        # detection fails for AlpineLinux
        export JAVA_OPTS="-Xmx256m"
        export brewSudo='/usr/bin/sudo -n -H -u vagrant'
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