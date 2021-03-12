#Script Overview and Setup#

In previous versions of CVP prior to 2020.0.0 the Snapshot records were available through the Provisioning API calls; with later releases this changed as the Snapshot records were incorporated into the Aeris database to improve scaling and performance. To Access data in the Aeris database a different set of APIs is required, these are resource APIs that use the Google RPC framework.

These scripts will retrieve the CVP Snapshots and have been created in Python version 3.8.1.
#get_snapshots_202x.py#

The get_snapshots_202x.py script works for CVP 2020.x.x through to CVP 2021.x.x releases and requires CVP tokens to access the CVP servers. 
The tokens can be retrieved using the "get_token.py" script. 
The snapshot script takes five arguments:

      **user {{CVP user name}}** The user to connect to CVP with at least Read access to the Snapshots
      **passwd {{CVP user password}}** The password for the above user
      **server {{lCVP server}}**  Name of CVP Server to fetch snapshots from
      **snapshot {{Snapshot Name}}** Name of Snapshot to retrieve from CVP.
      **device {{Device Name}}** Name of Device to retrieve Snapshot data for.

"device" and "snapshot" are optional arguments that default to "all" if not provided

The script will return a formatted file of the Snapshots data found. 
If the Snapshots contain "show tech" commands these will be saved in separate files to the rest of the Snapshot command outputs.


#get_token.py#

The access token and certificate used in the "get_snapshots.py" script can be obtained by executing the **"get_token.py"** script. This script gets a session token and optional SSL cert from CVP and saves then in the local directory as token.txt and cvp.crt

The "get_token.py" script takes three required arguments plus one optional:
      **server {{CVP IP / URL}}** The CloudVision server to connect to.
      **username {{USERNAME}}** Username to authorize with for the CVP connection
      **password {{PASSWORD}}** Password to authorize with associated to the username
      **ssl** Save the self-signed certificate to cvp.crt in the local directory.

#Script setup#

The scripts can be installed by Cloning or downloading the zip of this repository.

Clone the repo or Unzip the download file to a local directory then change directory to it.

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
chmod 755 ./get_snapshots_202x.py
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
./get_snapshots_202x.py --server {cvpIP/URL} --username {username} --password {password} --snapshot {snapshot_name}
```

The output from the get_snapshot_202x.py script will, upon successful connection, retrieve the results of the Snapshots stored in CVP.

#Script execution with the unsupported API#

The get_snapshots_202x.py can accommodate the slightly older API version that is available in the pre 2020.2.x versions of CVP.
First a different set of Certificates is needed, these can be collected by the following command:

```
scp "root@<CVPserver_Address>://cvpi/tls/certs/*" ./
```

Copy these files into the same directory as the python script then execute the python script as follows:

```
./get_snapshots_202x.py --server {cvpIP/URL} --username {username} --password {password} --snapshot {snapshot_name} -u
```

The "-u" option tells the script to use the unsupported version of the API that is available on the CVP server.

