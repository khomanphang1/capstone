import networkx as nx
import sympy as sp


graph = nx.DiGraph()

R_D, g_m, r_o, R_S, C_D, w = sp.symbols('R_D g_m r_o R_S C_D w')

#
#
# graph.graph['parameters'] = parameters

edges = [
    ('v_i', 'v_gs', 1),
    ('v_gs', 'v_x', g_m),
    ('v_gs', 'I_sco', -g_m),
    ('v_x', 'v_s', 1 / (1 / R_S + 1 / r_o)),
    ('v_s', 'v_gs', -1),
    ('v_s', 'I_sco', 1 / r_o),
    ('I_sco', 'v_o', 1 / (1 / R_D + 1 / r_o + sp.I * w * C_D)),
    ('v_o', 'v_x', 1 / r_o)
]

for src, dest, gain in edges:
    graph.add_edge(src, dest, gain=gain)

sfg = graph


parameters = {
    'R_D': 1,
    'g_m': 2,
    'r_o': 3,
    'R_S': 4,
    'C_D': 5,
    'w': 100e3
}