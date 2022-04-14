#Metrics Export

Example script to parse the CloudVision Inventory using the CloudVision connector and retrieve the latest updates for the interface counters on each switch found.

##metrics_parser.py

The script requires access to a CloudVision instance using command line arguments supplied. It will login into the resource API and collector a session token and the servers SSL certificate. It will then use these credentials to create a GRPC connection to the server. Once the connection is established the script will retrieve a list of switches and then collect the latest interface counter updates for them.
The metrics_parser.py script takes three arguments:
        **server {{CVP IP / URL }}** The source CloudVision server to connect to on port 443
        **user {{CVP username}}** CVP user name to access the CVP server
        **pwd {{password}}** Password for the CVP user

To execute the script enter the following on the command line:
```bash
%  python ./metrics_parser.py --server {{IP / URL}} --user {{Username}} --pwd {{Password}}
```

##Requirement

All the required python libraries not supplied in this repo can be install using:

```
pip install -r requirements.txt
```

It is recommended that this script be run in a python virtual environment.
