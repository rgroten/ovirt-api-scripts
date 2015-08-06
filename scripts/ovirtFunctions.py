#!/usr/bin/python
# ---------------------------------
#   Author: Ryan Groten
#   Description:
#           Utility functions used by other ovirt python scripts
#           ovirtConnect gets connection info from users ~/.ovirtparams
#           See example .ovirtparams file for details
# ---------------------------------

import socket
import os

def ovirtConnect(configSection=None):
    """
    Connect to hostname ovirt server using user/pass in ~/.ovirtparams
    By default uses localhost fqdn or pass fqdn of server to connect to as arg
    """
    from ovirtsdk.api import API
    from ovirtsdk.xml import params
    import ConfigParser
    try:
        confParser = ConfigParser.ConfigParser()
        confParser.read(os.getenv("HOME") + "/.ovirtparams")
        if configSection is None:
            configSection = socket.getfqdn()

        url = confParser.get(configSection, "url")
        ca_file = confParser.get(configSection, "cafile")
        username = confParser.get(configSection, "username")
        password = confParser.get(configSection, "password")

        api = API(url=url, username=username,
                password=password, ca_file=ca_file)
        return api
    except Exception as e:
        print("Unexpected error while connecting: " + str(e))
        raise


def getHost(vmname, api=None):
    """Helper function to get name of host that specified VM is running on"""
    disconnect = False
    if api is None:
        api = ovirtConnect()
        disconnect = True

    try:
        host = api.hosts.get(id=api.vms.get(vmname).get_host().get_id())
    except Exception as e:
        printc("Error")
    if disconnect:
        print("disconnecting")
        api.disconnect()

    return host


def printc(message, level=0):
    """Print message to stdout using severity color provided"""
    color = (
            '\033[0m',  # Turn off color.
            '\033[94m', # Blue.
            '\033[92m', # Green.
            '\033[95m', # Purple.
            '\033[91m', # Red.
            )

    NONE = color[0]

    print color[level] + message + NONE
