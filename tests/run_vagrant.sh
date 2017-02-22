#!/bin/bash

vm=$1

if [ -z "$vm" ]; then
    echo "Usage: $(basename $0) <vm>"
    exit 1
fi

vagrant up $vm
vagrant rsync $vm
vagrant ssh $vm -c 'cd /vagrant && tests/run_all.sh'
res=$?
#vagrant 
exit $res
