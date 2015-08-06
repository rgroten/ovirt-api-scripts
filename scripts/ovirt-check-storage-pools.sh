#!/bin/bash
# ---------------------------------
#   Author: Ryan Groten
#   Description:
#           Script will check the remaining free space in storage pools. 
#           If the consumed space of a pool exceeds $THRESHOLD %, send alert
#           Requires rhev-check-storage-pools.inf or $THRESHOLD variable set
# ---------------------------------

CONFIGFILE="ovirt-check-storage-pools.inf"
# Set the threshold from config file
if [ -s $CONFIGFILE ]; then
    . $CONFIGFILE
fi

su - postgres -c  \
  'psql -d engine  -A -q -c "select storage_name,available_disk_size,used_disk_size,commited_disk_size 
   from storage_domains 
   where storage_domain_type in (0, 1)"' | \
  tail -n +2 | grep -v "^(.*row" | tr "\|" " " | while read POOL AVAIL USED COMMITTED; do
     
     TOTAL=`(echo $AVAIL+$USED) | bc`
    PER=`(echo $USED*100/$TOTAL) | bc`

    if [ $PER -ge $THRESHOLD ]; then
        # Send alert with whatever method here
        echo "Warning: $POOL storage pool is $PER% full (warning threshold is $THRESHOLD%)."
    fi
done
