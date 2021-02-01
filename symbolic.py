import sympy as sp
from sympy.abc import s
from sympy.physics.control.lti import TransferFunction

from os import path
from circuit import Circuit
import circuit as cc

test_data_dir = path.join(path.dirname(__file__), 'test_data')

netlist_file = path.join(test_data_dir, '2N3904_common_emitter.net')
log_file = path.join(test_data_dir, '2N3904_common_emitter.log')

with open(netlist_file) as f:
    netlist = f.read()

with open(log_file) as f:
    log = f.read()

circuit = Circuit.from_ltspice(netlist, log)

import sympy as sp

def parallel(*impedances):
    result = 0
    for imp in impedances:
        result += 1 / imp

    return 1 / result

all_loads = []

for _, _, component in circuit.iter_components():
    if any(isinstance(component, cls) for cls in (cc.Resistor, cc.Capacitor)):
        print(f'+ : {component.pos_node}')
        print(f'- : {component.neg_node}')
        print(f'impedance: {component.impedance}\n')
        all_loads.append(component.impedance)

print('Compute all impedances in parallel')

sp.init_printing(use_unicode=True)
from pprint import pprint

result = parallel(*all_loads)
pass