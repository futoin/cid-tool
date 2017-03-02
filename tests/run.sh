#!/bin/bash

if ! test -e bin/cid; then
    echo "Invoke from CITool project root!"
    exit 1
fi

if [ "$1" = 'fast' ]; then
    fast=fast
    shift 1
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
    for nt in nosetests3 nosetests-3.4; do
        if which $nt; then
            echo "Python 3"
            $nt $tests;
            break
        fi
    done
fi

for nt in nosetests-2.7 nosetests; do
    if which $nt; then
        echo "Python 2"
        $nt $tests;
        break
    fi
done
