# ovirt-api-scripts
Collection of oVirt/RHEV SDK python scripts

### ovirtManageDisk.py 

Tool for managing disks for oVirt/RHEV from the command line.
Provides the ability to create, attach/detach, delete both internal (pool) disks and direct attach (lun) disks to VMs.
Requires ovirtFunctions.py so keep them in the same directory

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
```
