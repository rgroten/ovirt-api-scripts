#!/usr/bin/python
# ---------------------------------                                             
#   Author: Ryan Groten
# ---------------------------------
#   Description:
#           Tool for managing disks for ovirt/RHEV from the command line
#           Provides the ability to create, attach/detach, delete both internal
#           (pool) disks or direct attach (lun) disks to VMs
#           Run without args for usage
#           Requires ovirtFunctions and ovirtsdk
# ---------------------------------

from ovirtsdk.api import API
from ovirtsdk.xml import params
import sys
import getopt
import time
import os
import imp
import ntpath


class UsageException(Exception):
    """UsageException thrown if invalid arguments provided, print usage"""

    def __init__(self, message):
        Exception.__init__(self, message)

        print("Usage: " + os.path.basename(__file__) +
                " : <operation> <arguments>")
        print("   Operations:")
        print("	attachdisk: Attach existing disk to a VM.  Requires -n -d")
        print("	detachdisk: Detach existing disk from a VM. Requires -n -d")
        print("	createdisk: Create a new disk and attach it to a VM. Requires -n -d -s")
        print("	deletedisk: Deletes an existing disk (must be detached). Requires -d")
        print("	createlun: Add a new direct lun disk and attach it to VM. Requires -d -l. Optional -n")
        print("   Arguments:")
        print("	-n: Name of VM Guest")
        print("	-d: Name of disk")
        print("	-s: Size of disk in GB")
        print("	-l: LUN id")
        print("	-w: no-activate/no-detach. When attaching disk, don't activate it. When deactivating, don't detach.")
        print(message)
        sys.exit(2)


def _activate(disk):
    """
    Activate specified disk
    Parameters:
        disk - ovirtsdk.infrastructure.brokers.VMDisk object to activate
    """
    try:
        if disk.get_active():
            print("Disk is already active")
        else:
            print("Activating disk: " + disk.alias)
            disk.activate()
    except Exception as e:
        print ("Error while activating disk: " + str(e))
        raise


def _deactivate(disk):
    """
    Deactivate specified disk
    Parameters:
        disk - ovirtsdk.infrastructure.brokers.VMDisk object to deactivate
    """
    try:
        if disk.get_active():
            print("Deactivating disk: " + disk.get_alias())
            disk.deactivate()
        else:
            print("Disk is already deactivated")
    except Exception as e:
        print ("Error while deactivating disk: " + str(e))
        raise


def _attach(vm, disk, activate):
    """
    Attach specified disk to VM
    Parameters:
        disk - ovirtsdk.infrastructure.brokers.Disk object to attach
        vm - ovirtsdk.infrastructure.brokers.VM object to attach disk to
    """
    vmDisk = vm.disks.get(id=disk.id)
    # Check if disk is already attached to the VM
    if vmDisk:
        print("Disk " + disk.get_alias() + " is already attached")
        # Disk is already attached so lets activate it
        if activate:
            _activate(vmDisk)
    else:
        print("Attaching " + disk.get_alias() + " to " + vm.get_name())
        vmDisk = vm.disks.add(params.Disk(id = disk.id, active = activate))
    return vmDisk


def _detach(vm, disk):
    """
    Detach specified disk from VM
    Parameters:
        disk - ovirtsdk.infrastructure.brokers.VMDisk object to detach
        vm - ovirtsdk.infrastructure.brokers.VM object to detach disk from
    """
    print("Detaching disk " + disk.get_alias() + " from " + vm.get_name())
    disk.delete(action=params.Action(detach=True))


def attachDisk(vm_name, disk_name, activate=True):
    """
    Attach disk_name to vm_name then activate it by default
    Parameters:
      vm_name - string of VM to attach disk to
      disk_name - string of disk to attach to VM
    """
    try:
        vm = api.vms.get(name=vm_name)
        disks = api.disks.list(alias=disk_name)
        if not disks:
            raise Exception("No disks with name " + disk_name + " found")
        for disk in disks.__iter__():
            vmDisk = _attach(vm, disk, activate)
    except Exception as e:
        print ("Error while attaching disk")
        raise


def detachDisk(vm_name, disk_name, detach=True):
    """
    Deactivate disk_name and by default detach it from vm_name
    """
    try:
        vm = api.vms.get(name=vm_name)
        disks = vm.disks.list(alias=disk_name)
        if not disks:
            raise Exception("No disks with name " + disk_name + " are attached to " + vm_name)
        for disk in disks.__iter__():
            _deactivate(disk)
            if detach:
                _detach(vm, disk)
    except Exception as e:
        print("Exception while detaching disk")
        raise


def createDisk(vm_name, disk_name, sizegb):
    """Create a new disk with specified name and size. Attach to vm_name"""
    return_code = 0
    try:
        vm = api.vms.get(name=vm_name)
        disk = vm.disks.get(name=disk_name)
        size = int(sizegb) * 1024 * 1024 * 1024
        disk_params = params.Disk()
        disk_params.set_wipe_after_delete(True)
        disk_params.set_active(True)
        disk_params.set_alias(disk_name)
        disk_params.set_size(size)
        disk_params.set_interface('virtio')
        disk_params.set_format('cow')
        print("Will create new disk " + disk_name + " with size " + str(size))
        disk = vm.disks.add(disk_params)
        print("Created disk: " + disk.alias + " with size " + str(disk.size))
        # TODO: Dont sleep, use VMDisk.get_creation_status somehow
        #time.sleep(5)
        #activate(disk)
    except Exception as e:
        print("Error while creating new disk: " + str(e))
        return_code = 1

    return return_code


def createLun(vm_name, disk_name, lun_id):
    """
    Create a new direct attach disk from lun_id then attach to vm_name
    WARNING: Due to bug in RHEV3.4.0, direct luns created with this function
    will be missing all meta-information. To be fixed in 3.5.0 release
    """
    return_code = 0
    try:

        lu = params.LogicalUnit()
        lu.set_id(lun_id)

        lus = list()
        lus.append(lu)

        storage_params = params.Storage()
        storage_params.set_id(lun_id)
        storage_params.set_logical_unit(lus)
        storage_params.set_type('fcp')
        disk_params = params.Disk()
        disk_params.set_format('raw')
        disk_params.set_interface('virtio')
        disk_params.set_alias(disk_name)
        disk_params.set_active(True)
        disk_params.set_lun_storage(storage_params)

        if vm_name:
            vm = api.vms.get(name=vm_name)
            disk = vm.disks.add(disk_params)
        else:
            disk = api.disks.add(disk_params)

    except Exception as e:
        print("Error while adding new lun: " + str(e))
        return_code = 1

    return return_code


def deleteDisk(disk_name, vm_name=None):
    """
    Permanently delete disk_name from OVIRT. Expects disk to be detached 
    already. Unless -y is specified in command line, prompt user to confirm
    before deleting.
    """
    # TODO: If vm_name is populated, detach disk before deleting, instead of raise exception
    return_code = 0
    try:
        disks = api.disks.list(alias=disk_name)
        if not disks:
            raise Exception("No disks with name " + disk_name + " are attached to " + vm_name)
        for disk in disks.__iter__():
            if disk is None:
                raise Exception("No such disk")

            if assumeYes is False:
                print("Will destroy disk " + disk.alias + " with size " + str(disk.size) + ". Are you sure? (Y/[N])")
                input = sys.stdin.readline().rstrip("\r\n")
            else:
                print("Assuming Yes since -y used...")
                input = "y"

            if not input or input not in "yY":
                print("Cancelled by user")
                continue
            disk.delete()
            print("Disk " + disk.alias + " deleted")
    except Exception as e:
        print("Error while deleting disk: " + str(e))
        return_code = 1
        
    return return_code


def main(argv):
    try:
        if len(argv) == 0:
            raise UsageException("No arguments specified")
        operation = argv.pop(0)
        ret_code = 0

        opts, args = getopt.getopt(argv, "hwyn:d:s:l:")
    except getopt.GetoptError as e:
        raise UsageException(str(e))
    try:
        vm_name = None
        activate = True # Default, activate disk when attaching
        global api
        functionsPath = ntpath.split(os.path.realpath(__file__))[0] + "/ovirtFunctions.py"
        ovirtConnect = imp.load_source('ovirtConnect', functionsPath)
        api = ovirtConnect.ovirtConnect()
        for opt, arg in opts:
            if opt == '-h':
                raise UsageException("Print usage")
            elif opt in ("-y", "--assume-yes"):
                global assumeYes
                assumeYes = True
            elif opt in ("-w", "--no-activate"):
                activate = False
            elif opt in ("-n", "--vm-name"):
                vm_name = arg
            elif opt in ("-d", "--disk-name"):
                disk_name = arg
            elif opt in ("-s", "--size"):
                size = arg
            elif opt in ("-l", "--lun-id"):
                lun_id = arg
            else:
                raise UsageException("Unknown argument:" + opt)

        if operation == 'attachdisk':
            ret_code = attachDisk(vm_name, disk_name, activate)
        elif operation == 'detachdisk':
            ret_code = detachDisk(vm_name, disk_name, activate)
        elif operation == 'createdisk':
            ret_code = createDisk(vm_name, disk_name, size)
        elif operation == 'deletedisk':
            if vm_name:
                ret_code = deleteDisk(disk_name, vm_name)
            else:
                ret_code = deleteDisk(disk_name)
        elif operation == 'createlun':
            ret_code = createLun(vm_name, disk_name, lun_id)
        else:
            raise UsageException("Unknown operation: " + operation)

    except Exception as e:
        print("Exception: " + str(e))
        ret_code = 1
    finally:
        if api is not None:
            api.disconnect()
    #return_code = diskOperation( vm_name, disk_name, operation )
    sys.exit(ret_code)

api = None
assumeYes = False
if __name__ == "__main__":
    main(sys.argv[1:])
