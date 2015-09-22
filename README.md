# ovirt-api-scripts
Collection of oVirt/RHEV SDK python scripts

### ovirtManageDisk.py 

Tool for managing disks for oVirt/RHEV from the command line.
Provides the ability to create, attach/detach, delete both internal (pool) disks and direct attach (lun) disks to VMs.
Requires ovirtFunctions.py so keep them in the same directory

Before running, you must create a ~/.ovirtparams file in your home directory which contains the connection information for your Manager instance.  A sample .ovirtparams file can be found in the repo.  You can add multiple connection sections to the file if connecting to multiple different Managers.

#### Usage
```
Usage: ovirtManageDisk.py : <operation> <arguments>
   Operations:
	attachdisk: Attach existing disk to a VM.  Requires -n -d
	detachdisk: Detach existing disk from a VM. Requires -n -d
	createdisk: Create a new disk and attach it to a VM. Requires -n -d -s
	deletedisk: Deletes an existing disk (must be detached). Requires -d
	createlun: Add a new direct lun disk and attach it to VM. Requires -n -d -l
   Arguments:
	-n: Name of VM Guest
	-d: Name of disk
	-s: Size of disk in GB
	-l: LUN id
	-w: no-activate/no-detach. When attaching disk, don't activate it. When deactivating, don't detach.
```
#### Examples

###### create 5GB disk and attach to rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py createdisk -n rgtest -d test_disk -s 5
Will create new disk test_disk with size 5368709120
Created disk: test_disk with size 5368709120
```
###### Deactivate but dont detach newly create test_disk from rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detachdisk -w -d test_disk -n rgtest
Deactivating disk: test_disk
```
###### Detach test_disk from rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detachdisk  -d test_disk -n rgtest                             
Disk is already deactivated
Detaching disk test_disk from rgtest
```
###### Attach but dont activate test_disk to rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py attachdisk -w -d test_disk -n rgtest                           
Attaching test_disk to rgtest
```
###### Activate test_disk
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py attachdisk -d test_disk -n rgtest                              
Disk test_disk is already attached
Activating disk: test_disk
```
###### Deactivate and detach test_disk from rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detachdisk -d test_disk -n rgtest                              
Deactivating disk: test_disk
Detaching disk test_disk from rgtest
```
###### Permanently delete test_disk
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py deletedisk -d test_disk                                         
Will destroy disk test_disk with size 5368709120. Are you sure? (Y/[N])
y
Disk test_disk deleted
```
###### Create direct attach disk and attach to rgtest
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py createlun -n rgtest -d test_lun -l 3600a098038303053453f463045727459
```
###### Detach direct attach disk, note other than creation all commands on internal disks and direct attach disks are the same
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py detachdisk -n rgtest -d test_lun
Deactivating disk: test_lun
Detaching disk test_lun from rgtest
```
###### Delete test_lun without prompting for confirmation
```
[rgroten@rg-rhevm ~] $ ovirtManageDisk.py deletedisk -d test_lun -y
Assuming Yes since -y used...
Disk test_lun deleted
```
