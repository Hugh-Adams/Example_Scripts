#Script Overview and Setup#

These scripts will retrieve the CVP Snapshots and have been created in Python version 3.8.1.
#get_snapshots.py#
The "get_snapshots.py" script can be used to retrieve the Snapshots contained in CVP and display them on the CLI. The script can be easily modified to store these outputs in other formats for further processing.

The script takes two arguments:
**apiserver {{CVP Server Address:TCP Port}}** The URL and TCP port of the CVP API server to connect to in the format {{CVP IP / URL}}:{{TCP PORT number}}. For example (apiserver.examplecvp.com:11002)
**auth {{Authentication scheme}}**  The Authentication scheme used to connect to CloudVision. The possible values accepted are:
      **"none"**: no authentication
      **"none-tls[,{caFile}]"**: no authentication, TLS encryption
      **"token,{tokenFile}[,{caFile}]"**: access token based authentication
      **"certs,{certFile},{keyFile}[,{caFile}]"**: client-side certificate

For this solution the "token" authentication scheme will be used. This scheme requires an access token and a certificate.

The script will return a formatted output of the Snapshot data found.

#get_token.py#

The access token and certificate used in the "get_snapshots.py" script can be obtained by executing the **"get_token.py"** script. This script gets a session token and optional SSL cert from CVP and saves then in the local directory as token.txt and cvp.crt

The "get_token.py" script takes three required arguments plus one optional:
      **server {{CVP IP / URL}}** The CloudVision server to connect to.
      **username {{USERNAME}}** Username to authorize with for the CVP connection
      **password {{PASSWORD}}** Password to authorize with associated to the username
      **ssl** Save the self-signed certificate to cvp.crt in the local directory.

#Script setup#

The scripts can be installed from the zip file located at {{GitHub Repository}}

Unzip the file Get-Snapshot.zip to a local directory then change directory to it.

From inside the directory use the python package installer pip to install the required libraries:

```
pip install -r ./requirments.txt
```

change directory to the cloudvision-python directory:

```
cd ./cloudvision-python
```

install the cloudvision supporting libraries from inside thisl directory:

```
python setup.py install
```

change back to the top level director and ensure the python scripts are executable:

```
chmod 755 ./get_snapshots.py
chmod 755 ./get_token.py
```

The scripts should now be ready to use.

#Script execution#

The scripts can now be used to get the CVP snapshots:

First get the access token and certificate for the CVP cluster that holds the required Snapshots:

```
./get_token.py --server {cvpIP/URL} --username {username} --password {password} --ssl
```

This will create "token.tx" and "cvp.crt" these will be used to create the gRPC session with CVP to get the Snapshots:

```
./get_snapshots.py --apiserver {cvpIPaddres}:8443 --auth=token,./token.txt,./cvp.crt
```

For the access to the Telemetry APIs port 8443 is required hence the {cvpIPaddress}:8443 command argument.
The output from the get_snapshot.py script will, upon successful connection, to CVP display the results of the Snapshots stored in CVP.
