#!/usr/bin/env python
# ---------------------------------
#   Author: Ryan Groten
# ---------------------------------
#   Description:
#       Script for checking status of ovirt/RHEV Manager from command line
#       Requires ovirtFunctions, and configured ~/.ovirtparams
#       https://github.com/rgroten/ovirt-api-scripts
# ---------------------------------

from ovirtFunctions import ovirtConnect
import sys

def restart_manager():
    """
    Function used to automatically attempt to restart engine if connection
    test fails
    """
    import os
    sys.stderr.write("Attempting to restart ovirt-engine")
    command = 'PATH=/sbin:$PATH; service ovirt-engine restart'
    os.system(command)


def main(argv):
    """
    Connect to RHEV Manager and test connectivity. Defaults to localhost
    Takes one optional argument to specify which RHEV Manager to connect to
    """
    api = None
    ret_code = 0
    try:
        if len(argv) == 0:
            api = ovirtConnect()
        else:
            api = ovirtConnect(argv.pop(0))
        status = api.test()
        if status is False:
            raise Exception("Connection test failed")
    except Exception as e:
        # Insert something to handle RHEV-M being down here if you want
        # Example, uncomment next line and the script will restart ovirt-engine
        # restart_manager
        sys.stderr.write(str(e))
        ret_code = 1
    finally:
        if api is not None:
            api.disconnect()
    sys.exit(ret_code)

if __name__ == "__main__":
    main(sys.argv[1:])
