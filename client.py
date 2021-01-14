import os
import requests


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

netlist_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.net')
with open(netlist_path, 'r') as f:
    netlist = f.read()

op_log_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.log')
with open(op_log_path, 'r') as f:
    op_log = f.read()

url = 'http://127.0.0.1:5000/small_signal_netlist'
r = requests.post(url, json={'netlist': netlist, 'op_log': op_log})

for line in r.json()['netlist'].splitlines():
    print(line)

