#!/bin/bash

VM_LIST=$(vagrant status --machine-readable | grep metadata | cut -d, -f2)
CID_DESTROY=${CID_DESTROY:-0}
CID_FAST=${CID_FAST:-fast}
args=

for vm in $VM_LIST; do
    if [ $vm = 'cid_rmshost' ]; then
        vagrant up cid_rmshost
        continue
    fi

    $(dirname $0)/run_vagrant.sh $vm $args "$@";

    [ $vm = 'cid_rhel_7' ] && \
        [ $CID_DESTROY -eq 1 ] && \
        vagrant ssh $vm -- sudo subscription-manager unregister

    [ $CID_DESTROY -eq 1 ] && vagrant destroy -f $vm
    
    args=$CID_FAST
done
