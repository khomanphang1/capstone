import os
import requests

# This directory contains all the circuit schematic / netlist files.
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

# Read netlist file into string.
netlist_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.net')
with open(netlist_path, 'r') as f:
    netlist = f.read()

# Read op point analysis file into string.
op_log_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.log')
with open(op_log_path, 'r') as f:
    op_log = f.read()

# Send a post request to the local web server's small signal netlist API
# Include in the request a dictionary (serialized to json) the netlist and
# op point log.

# The server returns a json object. Inside this object, the small signal
# netlist is embedded.
url = 'http://127.0.0.1:5000/small_signal_netlist'
r = requests.post(url, json={'netlist': netlist, 'op_log': op_log})

for line in r.json()['netlist'].splitlines():
    print(line)

