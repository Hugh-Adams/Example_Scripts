#Decommission Device in Inventory

The decomm_device.py takes a list of device names and removes them from the CloudVision Telementry Inventory. The devices should have TerminAttr shutdown or pointed at another CloudVision cluster to prevent them re-appearing in the Inventory view.

##decomm_device.py

The copy_custom_events.py script works for CVP 2020.x.x through to CVP 2022.x.x releases and requires CVP tokens to access the CVP servers.
The tokens can be retrieved using the "get_token.py" script.
The copy_custom_events script takes three arguments:
        **src {{CVP IP / URL :8443}}** The source CloudVision server to connect to on TCP port 8443
        **srcauth {{token, token_file_name, cert_file_name}}** Authentication scheme used to connect to CloudVision in this case use the token option
                                                              "token,{tokenFile}[,{caFile}]"
        **dst {{CVP IP / URL :8443}}** The destination CloudVision server to connect to on TCP port 8443
        **dstauth {{token, token_file_name, cert_file_name}}** Authentication scheme used to connect to CloudVision in this case use the token option
                                                              "token,{tokenFile}[,{caFile}]"
        **device {{List of device Names}}** device will take a list of device names to be removed from the CloudVision Inventory

##get_token.py

The access token and certificate used in the "get_snapshots.py" script can be obtained by executing the **"get_token.py"** script. This script gets a session token and optional SSL cert from CVP and saves then in the local directory as token.txt and cvp.crt

The "get_token.py" script takes three required arguments plus one optional:
      **server {{CVP IP / URL}}** The CloudVision server to connect to.
      **username {{USERNAME}}** Username to authorize with for the CVP connection
      **password {{PASSWORD}}** Password to authorize with associated to the username
      **ssl** Save the self-signed certificate to cvp.crt in the local directory.

##Decommissioning Devices

To decommission a set of devices on a CV cluster retrieve the token files from the CV cluster and then use device_decomm.py to remove them:

```
./get_token.py --server 10.90.227.147 --username cvpadmin --password password --ssl
./device_decomm.py --device "host1,host2" get --src 192.168.10.10:8443 --srcauth=token,token.txt,cvp.crt
```

##Requirement

All the required python libraries not supplied in this repo can be install using:

```
pip install -r requirements.txt
```

It is recommended that this script be run in a python virtual environment.
