#!/bin/bash
# ---------------------------------
#   Author: Ryan Groten
#   Description:
#           Script to backup the ovirt manager database.
#           Requires the engine-db user password in $PGPASSFILE (.pgpass)
# ---------------------------------

# Path to backup db to
BACKUPPATH=/var/lib/ovirt-engine-backups
# Backup file name
BACKUPFILE=$BACKUPPATH/engine-backup-$(date +%Y%m%d%H%M%S).`hostname`.tar.bz2
# Log of backup
BACKUPLOG=/var/log/ovirt-engine-backups.log
# Second server to copy backup files to. Disabled if blank. Requires ssh-key
BACKUPHOST=my-backup-host.example.com

if [ ! -d $BACKUPPATH ]; then
    mkdir $BACKUPPATH
fi

/usr/bin/engine-backup --mode=backup --scope=all --file=$BACKUPFILE --log=$BACKUPLOG > /dev/null
if [ $? -ne 0 ]; then
  echo "Error while backing up RHEV-M database using engine-backup - backup not completed"
  exit_code=1
fi

# Copy backup to standby ovirt manager or another host
if [ -n $BACKUPHOST ]; then
    scp -q $BACKUPFILE $BACKUPHOST:$BACKUPPATH
    if [ $? -ne 0 ]; then
        echo "Error while copying backup file to standby RHEV-M server"
        exit_code=1
    fi

    # Cleanup old backups that are older than 15 days
    find $BACKUPPATH -mtime +15 -exec rm -f {} \;
    ssh -q $BACKUPHOST "find $BACKUPPATH -mtime +15 -name "*.`hostname`.tar.bz2" -exec rm -f {} \;"
fi

exit $exit_code
