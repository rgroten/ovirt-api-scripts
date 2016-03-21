# ovirt-api-scripts
Collection of oVirt/RHEV SDK python scripts

### ovirtManageDisk.py 

Tool for managing disks for oVirt/RHEV from the command line.
Provides the ability to create, attach/detach, delete both internal (pool) disks and direct attach (lun) disks to VMs.
Requires ovirtFunctions.py so keep them in the same directory

Before running, you must create a ~/.ovirtparams file in your home directory which contains the connection information for your Manager instance.  A sample .ovirtparams file can be found in the repo.  You can add multiple connection sections to the file if connecting to multiple different Managers.

#### Usage
```
usage: ovirtManageDisk.py [-h] [-r RHEVM] {attach,create,detach,delete} ...

Create, attach, delete RHEV disks

positional arguments:
  {attach,create,detach,delete}
    attach              Attach existing disk to a VM.
    detach              Detach existing disk from a VM.
    create              Create a new disk (or direct lun) and optionally attach it to a VM.
    delete              Delete a disk or direct lun (must be detached from all VMs first).

optional arguments:
  -h, --help            show this help message and exit
  -r RHEVM, --rhevm RHEVM
                        Specify RHEV Manager to connect to
```
#### Examples

###### create 5GB disk and attach to rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py create -n rgtest -d test_disk -s 5
Will create new disk test_disk with size 5368709120
Created disk: test_disk with size 5368709120
```
###### Deactivate but dont detach newly create test_disk from rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detach -w -d test_disk -n rgtest
Deactivating disk: test_disk
```
###### Detach test_disk from rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detach  -d test_disk -n rgtest                             
Disk is already deactivated
Detaching disk test_disk from rgtest
```
###### Attach but dont activate test_disk to rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py attach -w -d test_disk -n rgtest                           
Attaching test_disk to rgtest
```
###### Activate test_disk
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py attach -d test_disk -n rgtest                              
Disk test_disk is already attached
Activating disk: test_disk
```
###### Deactivate and detach test_disk from rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detach -d test_disk -n rgtest                              
Deactivating disk: test_disk
Detaching disk test_disk from rgtest
```
###### Permanently delete test_disk
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py delete -d test_disk                                         
Will destroy disk test_disk with size 5368709120. Are you sure? (Y/[N])
y
Disk test_disk deleted
```
###### Create direct attach disk and attach to rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py create -n rgtest -d test_lun -l 3600a098038303053453f463045727459
```
###### Detach direct attach disk, note other than creation all commands on internal disks and direct attach disks are the same
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detach -n rgtest -d test_lun
Deactivating disk: test_lun
Detaching disk test_lun from rgtest
```
###### Delete test_lun without prompting for confirmation
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py delete -d test_lun -y
Assuming Yes since -y used...
Disk test_lun deleted
```

### ovirtTestConn.py

Simple python script connects to oVirt/RHEV Manager to check if it's available.  Can make it automatically restart the manager service or add in another action like notify admin team.

### ovirt-backup-db.sh

This script will backup your oVirt/RHEV Manager database and copy it to a standby host, then cleanup any old backups stored on the standby.  Run from cron.  As of RHEV/oVirt 3.6 this script can be replaced with a built-in monitor on storage domains.

### ovirt-check-storage-pools.sh

Script to alert users if a storage pool fills up beyond a certain threshold. Threshold percentage can be specified in ovirt-check-storage-pools.inf file.
