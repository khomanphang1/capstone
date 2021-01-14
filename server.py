from flask import Flask, request
from circuit import Circuit

app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Distant Reading Archive</h1>
<p>A prototype API for distant reading of science fiction novels.</p>'''


@ app.route('/small_signal_netlist', methods=['POST'])
def small_signal_circuit():
    print(request.json)
    circuit = Circuit.from_ltspice(**request.json)

    return {'netlist': circuit.netlist()}

app.run()