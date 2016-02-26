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
import argparse
import getopt
import imp
import ntpath
import os
import sys
import time


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


def _attach(vm, disk, noactivate):
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
        if not noactivate:
            _activate(vmDisk)
    else:
        print("Attaching " + disk.get_alias() + " to " + vm.get_name())
        vmDisk = vm.disks.add(params.Disk(id = disk.id, active = not noactivate))
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


def attachDisk(vm_name, disk_name, noactivate=False):
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
            vmDisk = _attach(vm, disk, noactivate)
    except Exception as e:
        print ("Error while attaching disk")
        raise


def detachDisk(vm_name, disk_name, nodetach=False):
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
            if not nodetach:
                _detach(vm, disk)
    except Exception as e:
        print("Exception while detaching disk")
        raise


def createDisk(vm_name, disk_name, sizegb):
    """Create a new disk with specified name and size. Attach to vm_name"""
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
        raise


def createLun(vm_name, disk_name, lun_id):
    """
    Create a new direct attach disk from lun_id then attach to vm_name
    WARNING: Due to bug in RHEV3.4.0, direct luns created with this function
    will be missing all meta-information. To be fixed in 3.5.0 release
    """
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
        raise


def deleteDisk(disk_name, vm_name=None, assume_yes=False):
    """
    Permanently delete disk_name from OVIRT. Expects disk to be detached 
    already. Unless -y is specified in command line, prompt user to confirm
    before deleting.
    """
    if vm_name:
        detachDisk(vm_name, disk_name)

    try:
        disks = api.disks.list(alias=disk_name)
        if not disks:
            raise Exception("No disks with name " + disk_name + " are attached to " + vm_name)
        for disk in disks.__iter__():
            if disk is None:
                raise Exception("No such disk")

            if not assume_yes:
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
        raise


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="""Create, attach, delete RHEV disks""")
    parser.add_argument("-r","--rhevm", help="Specify RHEV Manager to connect to")

    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = "command"

    attach_parser = subparsers.add_parser('attach',
            help="Attach existing disk to a VM.")
    detach_parser = subparsers.add_parser('detach',
            help="Detach existing disk from a VM.")
    create_parser = subparsers.add_parser('create',
            help="Create a new disk (or direct lun) and optionally attach it to a VM.")
    delete_parser = subparsers.add_parser('delete',
            help="Delete a disk or direct lun (must be detached from all VMs first).")

    attach_parser.add_argument("-n", "--vm", help="(Required) VM Name")
    attach_parser.add_argument("-d", "--disk", help="(Required) Disk Alias")
    attach_parser.add_argument("-w", "--noactivate", action="store_true",
            default=False,
            help="Attach disk but don't activate it. By default disk is attached then activated.")

    detach_parser.add_argument("-n", "--vm", help="(Required) VM Name")
    detach_parser.add_argument("-d", "--disk", help="(Required) Disk Alias")
    detach_parser.add_argument("-w", "--nodetach", action="store_true",
            default=False,
            help="Deactivate disk but don't detach it. By default disk is deactivated then detached.")

    create_parser.add_argument("-n", "--vm", help="VM Name. If not provided disk will not attach")
    create_parser.add_argument("-d", "--disk", help="(Required) Disk Alias")
    create_group = create_parser.add_mutually_exclusive_group()
    create_group.add_argument("-s", "--size", help="Pool Disk Size in GB")
    create_group.add_argument("-l", "--lunid", help="WWID of direct lun to create")

    delete_parser.add_argument("-n", "--vm",
            help="VM Name. If provided disk will detach before deleteing")
    delete_parser.add_argument("-d", "--disk", help="(Required) Disk Alias")
    delete_parser.add_argument("-y", "--assumeyes", action="store_true", help="(Required) Disk Alias")

    try:
        args = parser.parse_args()
        return args
    except IOError, error:
        print error
        sys.exit(1)


def main():
    """Main Function"""

    try:
        args = parse_args()

        ret_code = 0
        global api
        functionsPath = ntpath.split(os.path.realpath(__file__))[0] + "/ovirtFunctions.py"
        ovirtConnect = imp.load_source('ovirtConnect', functionsPath)
        api = ovirtConnect.ovirtConnect(args.rhevm)

        if args.command == 'attach':
            if not args.vm or not args.disk:
                raise Exception("Missing vm or disk name")
            attachDisk(args.vm, args.disk, args.noactivate)
        elif args.command == 'detach':
            if not args.vm or not args.disk:
                raise Exception("Missing vm or disk name")
            detachDisk(args.vm, args.disk, args.nodetach)
        elif args.command == 'create':
            if not args.vm or not args.disk:
                raise Exception("Missing vm or disk name")
            if args.size:
                createDisk(args.vm, args.disk, args.size)
            elif args.lunid:
                createLun(args.vm, args.disk, args.lunid)
            else:
                raise Exception("Missing disk size or lunid")
        elif args.command == 'delete':
            deleteDisk(args.disk, args.vm, assume_yes=args.assumeyes)

    except Exception as e:
        print "Exception: " + str(e)
        ret_code = 1
    finally:
        if api:
            api.disconnect()
    #return_code = diskOperation( vm_name, disk_name, operation )
    sys.exit(ret_code)

api = None
if __name__ == "__main__":
    main()
