#!/bin/bash

if ! test -e bin/cid; then
    echo "Invoke from CITool project root!"
    exit 1
fi

if [ "$1" = 'fast' ]; then
    fast=fast
    shift 1
fi

if [ "$1" = 'nocompile' ]; then
    export CIDTEST_NO_COMPILE=1
    shift 1
else
    unset CIDTEST_NO_COMPILE
fi

if [ -z "$1" ]; then
    tests=
    tests+=" tests/citool_tools_test.py"
    tests+=" tests/citool_git_test.py"
    tests+=" tests/citool_hg_test.py"
    tests+=" tests/citool_svn_test.py"
else
    tests="$*"
fi

# CentOS 6
[ -e /opt/rh/python27/enable ] && source /opt/rh/python27/enable 

if [ "$fast" != 'fast' ]; then
    echo "Python 3"
    pythonVer='3' ./bin/cid tool exec pip install nose
    pythonVer='3' ./bin/cid tool exec python -- -m nose $tests
fi

echo "Python 2"
pythonVer='2' ./bin/cid tool exec pip install nose
pythonVer='2' ./bin/cid tool exec python -- -m nose $tests
