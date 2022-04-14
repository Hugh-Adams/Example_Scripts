# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

import argparse
import urllib3
import requests, ssl
import json
from cloudvision.Connector.grpc_client import GRPCClient, create_query

class grpcServer(object):
    """ CloudVision Connector Class
        Creates a GRPC connection to CloudVision
        Returns Path elements
    """

    def __init__(self, serverAddr, username, password) -> None:
        """ Create a GRPC connection
            Log in to CloudVision retrieve session token and
            SSL certicifcate then create a GRPC session
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        ssl._create_default_https_context = ssl._create_unverified_context
        self.GRPCport = 443
        self.SSLport = 443
        self.connect_timeout = 10
        self.headers = {"Accept": "application/json",
                "Content-Type": "application/json"}
        self.session = requests.Session()
        self.authdata = {"userId": username, "password": password}
        self.response = self.session.post(
            "https://" + str(serverAddr) + "/web/login/authenticate.do",
            data=json.dumps(self.authdata),
            headers=self.headers,
            timeout=self.connect_timeout,
            verify=False,
        )
        if self.response.json()["sessionId"]:
            self.tknFile = f"{serverAddr}_token.txt"
            self.certFile = f"{serverAddr}_cert.txt"
            with open(self.tknFile, "w") as f:
                f.write(self.response.json()["sessionId"])
            with open(self.certFile, "w") as f:
                f.write(ssl.get_server_certificate((str(serverAddr), self.SSLport)))
            self.client = GRPCClient(
                f"{serverAddr}:{self.GRPCport}", token=self.tknFile, key=None, ca=self.certFile, certs=None)
            print(f"Logged into {serverAddr}")
        else:
            print(f"Unable to log in to {serverAddr}")


    def __fetch_query(self, pathElts=[], dataSet="", dataKeys=[]):
        """ Generic fetch for retrieving path data
            Requires:
                pathElts - list of path elements to follow to access the data
                dataSet - name of data path elemenst belong to, see CVP Telemetry browser
                dataKeys - data points to rerieve from path end
            Returns:
                data points
        """
        self.notifications = []
        self.query = [create_query([(pathElts, dataKeys)], dataSet)]
        for batch in self.client.get(self.query):
            for notif in batch["notifications"]:
                self.notifications.append(notif)
        return self.notifications


    def get_Devices(self):
        """ Returns a dictionary of devices found in CloudVision"""
        self.deviceDict = {}
        pathElts = [
            "DatasetInfo",
            "Devices"
        ]
        self.devices = self.__fetch_query(pathElts, "analytics", [])
        for notif in self.devices:
            for device in notif["updates"]:
                self.deviceDict[str(device)] = notif["updates"][str(device)]
        return self.deviceDict


    def get_intStats(self, deviceID):
        """ Returns a dictionary of interface data for each interface
            associated with the device selected
            Requires
                devcieID - serial number of target device
            Returns
                diction of interfaces found and associated counter updates
        """
        self.intrfcDict = {}
        # get list of Interfaces on Device
        pathElts = [
            "Devices",
            deviceID,
            "versioned-data",
            "interfaces",
            "data"
        ]
        for notif in self.__fetch_query(pathElts, "analytics", []):
            # Get Interface counters for interfaces
            for interface in notif["updates"]:
                pathElts2 = [
                    "Devices",
                    deviceID,
                    "versioned-data",
                    "interfaces",
                    "data",
                    interface,
                    "rates"
                ]
                for intfNotif in self.__fetch_query(pathElts2, "analytics", []):
                    self.intrfcDict[interface] = intfNotif["updates"]
        return self.intrfcDict


def main(args):
    cvGRPC = grpcServer(args.server, args.user, args.pwd)
    cvDevices = cvGRPC.get_Devices()
    for device in cvDevices:
        print (f"{cvDevices[device]['hostname']}:")
        deviceInterfaces = cvGRPC.get_intStats(device)
        for interface in sorted(deviceInterfaces):
            print(f"  {interface}:{deviceInterfaces[interface]}")
    

if __name__ == "__main__":
    ds = ("Get Metrics for Devices, requires session token from get_token.py")
    parser = argparse.ArgumentParser(
        description=ds,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--server', required=True, type=str,
                        help="CloudVision Server URL or IP address")
    parser.add_argument('--user', required=True, type=str,
                        help="CVP User with required access")
    parser.add_argument('--pwd', required=True, type=str,
                        help="CVP User Password")
    args = parser.parse_args()
    main(args)
