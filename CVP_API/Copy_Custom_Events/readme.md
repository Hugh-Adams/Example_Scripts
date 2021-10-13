#Copy CloudVision Custom Syslog Events

The Custom Syslog Event records are stored in the Aeris database to improve scaling and performance. 
To Access data in the Aeris database the resource APIs that use the Google RPC framework are required.

##copy_custom_events.py

The copy_custom_events.py script works for CVP 2020.x.x through to CVP 2022.x.x releases and requires CVP tokens to access the CVP servers. 
The tokens can be retrieved using the "get_token.py" script. 
The copy_custom_events script takes three arguments:
        **cvhost {{CVP IP / URL :8443}}** The CloudVision server to connect to on TCP port 8443
        **cvauth {{token, token_file_name, cert_file_name}}** Authentication scheme used to connect to CloudVision in this case use the token option
                                                              "token,{tokenFile}[,{caFile}]"
        **mode {{set / get}}** Mode set will apply previously retrieved Custom Syslog Events to the target CV cluster
                               Mode get retrieves Custom Syslog Events from the Target CV cluster.
                               In both modes a backup file is created (get - backupSourceCVP.json, set - backupDestCVP.json)

##get_token.py

The access token and certificate used in the "get_snapshots.py" script can be obtained by executing the **"get_token.py"** script. This script gets a session token and optional SSL cert from CVP and saves then in the local directory as token.txt and cvp.crt

The "get_token.py" script takes three required arguments plus one optional:
      **server {{CVP IP / URL}}** The CloudVision server to connect to.
      **username {{USERNAME}}** Username to authorize with for the CVP connection
      **password {{PASSWORD}}** Password to authorize with associated to the username
      **ssl** Save the self-signed certificate to cvp.crt in the local directory.

##Copying Custom Syslog Events

To copy a set of Custom Syslog Events from one CV cluster to another first retrieve the token files from the Source CV cluster and then 'get' the Custom Syslog Events:

```
./get_token.py --server 10.90.227.147 --username cvpadmin --password password --ssl
./copy_custom_events_cfg.py --mode get --cvhost 192.168.10.10:8443 --cvauth=token,token.txt,cvp.crt
```

Then retrieve the token files from the Destination CV cluster and then apply, 'set', the Custom Syslog Events:

```
./get_token.py --server 10.83.30.100 --username cvpadmin --password password --ssl
./copy_custom_events_cfg.py --mode set --cvhost 192.168.20.20:8443 --cvauth=token,token.txt,cvp.crt
```

##Requirement

All the required python libraries not supplied in this repo can be install using:

```
pip install -r requirements.txt
```

It is recommended that this script be run in a python virtual environment.