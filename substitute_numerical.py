# First, parse the circuit

import circuit_parser

with open(r'test_data/2N3904_common_emitter.cir') as netlist_file, \
     open(r'test_data/2N3904_common_emitter.log') as op_point_log_file:
    netlist = netlist_file.read()
    op_point_log = op_point_log_file.read()

print('2N3904 Common Emitter Circuit')
print('-----------------------------')
circuit = circuit_parser.Circuit.from_ltspice_netlist(netlist, op_point_log)
circuit.print_components()

# Then, get its component parameters. This is given as a dictionary that maps
# parameter names to their numerical values.

import json # Only used for pretty printing dictionary

params = circuit.parameters()
print('\n')
print('Circuit parameters and their numerical values')
print('---------------------------------------------')
print(json.dumps(params, indent=4))

# Note that "f" denotes the frequency term.


# Next, generate the DPI
from dpi import DPI_algorithm as DPI
import sys
import os


try:
    with open(os.devnull, 'w') as f:
        sys.stdout = f
        sfg = DPI(circuit).graph
except Exception:
    pass
finally:
    sys.stdout = sys.__stdout__


# Finally, substitute numerical values into symbolic edge expressions

import cmath # Built-in complex math library
import sympy

# Since edge expressions are given in terms of "s", but our circuit parameters
# uses frequency "f", we can convert between "s" and "f" using the following
# formulas:
#
#   s = j * w
#   s = j * 2 * pi * f
#
freq = 2j * sympy.pi * sympy.Symbol('f')


print('Numerical values for SFG Edges')
print('------------------------------')
# Iterate over each edge in the SFG
for src, dst, weight in sfg.edges(data='weight'):

    # This is the edge expression
    symbolic = sfg.edges[src, dst]['weight']

    if isinstance(weight, sympy.Expr):
        # If the edge expression is symbolic, we must substitute it.
        #   1. Re-write the expression in terms of "f" instead of "s"
        #   2. Plug in all numerical values from params
        numeric = symbolic.subs('s', freq).subs(params)
    else:
        numeric = symbolic

    # It's possible for the numerical value to be complex. If desired, we can
    # express this in polar form or rectangular
    numeric = complex(numeric) # In case it's not complex
    magnitude, phase = cmath.polar(numeric)

    print(f'{src} --> {dst}')
    print(f'Complex: {numeric:.6f}')
    print(f'Magnitude: {magnitude:.6f} | Phase: {phase:.6f}')
    print(f'Real: {numeric.real:.6f} | Imaginary: {numeric.imag:.6f}\n')