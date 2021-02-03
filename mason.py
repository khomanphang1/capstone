import networkx.algorithms as algo

from itertools import chain, tee

import itertools
import networkx as nx
from networkx.algorithms import all_simple_paths, simple_cycles
from typing import List, Iterable, Set, Tuple


def pairwise(iterable):
    """Returns a pairwise iterator."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def pairwise_circular(iterable):
    """Returns a pairwise circular iterator."""
    a, b = tee(iterable)
    first = next(b, None)
    return itertools.zip_longest(a, b, fillvalue=first)


def transfer_function(graph: nx.DiGraph, input_node: str, output_node: str) -> str:
    """Computes the transfer function of a signal-flow graph.

    Args:
        graph: A signal-flow graph with weighted edges.
        input_node: The name of the input node.
        output_node: The name of the output node.

    Returns:
        A string that represents the transfer function from the input to output
        node.

    Raises:
        KeyError: The input or output node is not in the signal-flow graph.
    """

    paths = []

    # Finds all simple paths from the input to output node.
    for path in all_simple_paths(graph, input_node, output_node):
        weights = [graph.edges[u, v]['weight'] for u, v in pairwise(path)]
        nodes = set(path)
        paths.append((weights, nodes))

    cycles = []

    # Finds all simple cycles in the graph.
    for cycle in simple_cycles(graph):
        weights = [graph.edges[u, v]['weight'] for u, v in pairwise_circular(cycle)]
        nodes = set(cycle)
        cycles.append((weights, nodes))

    combinations = []

    def non_touching_combinations(i, comb: List, nodes: Set):
        if i == len(cycles):
            return

        non_touching_combinations(i + 1, comb, nodes)

        curr_weights, curr_nodes = cycles[i]

        if nodes.isdisjoint(curr_nodes):
            nodes |= curr_nodes
            comb.append((curr_weights, curr_nodes))
            combinations.append(comb[:])
            non_touching_combinations(i + 1, comb, nodes)
            comb.pop()
            nodes -= curr_nodes

    # Find all combination of non-touching cycles.
    non_touching_combinations(0, [], set())
    # Sort cycle combinations by combination size.
    combinations.sort(key=len)

    determinant = '1'

    for size, group in itertools.groupby(combinations, key=len):
        sign = ' - ' if size % 2 else ' + '
        gain_products = (''.join(itertools.chain.from_iterable(weights for weights, _ in comb)) for comb in group)
        sum = '(' + ' + '.join(gain_products) + ')'
        determinant += sign + sum

    numerator = '0'

    for path, nodes in paths:

        determ = '1'

        for size, group in itertools.groupby(combinations, key=len):
            sign = ' - ' if size % 2 else ' + '
            gain_products = []

            for comb in group:
                if not all(nodes.isdisjoint(nodes_) for _, nodes_ in comb):
                    # If any cycle in the current combination touches the
                    # current forward path, ignore it.
                    break
                gain_products.append(''.join(
                    itertools.chain.from_iterable(
                        weights for weights, _ in comb
                    )
                ))

            if gain_products:
                sum = '(' + ' + '.join(gain_products) + ')'
                determ += sign + sum

        s = f'({determ}) * {"".join(path)}'
        numerator += ' + ' + s

    print(numerator)
    print(determinant)
    pass

g = nx.DiGraph()

edges = [
    ('y1', 'y2', 'a'),
    ('y2', 'y3', 'b'),
    ('y3', 'y2', 'j'),
    ('y3', 'y4', 'c'),
    ('y3', 'y5', 'g'),
    ('y4', 'y5', 'd'),
    ('y5', 'y5', 'f'),
    ('y5', 'y3', 'h'),
    ('y5', 'y4', 'i'),
    ('y5', 'y6', 'e')
]

for src, dest, weight in edges:
    g.add_edge(src, dest, weight=weight)

transfer_function(g, 'y1', 'y6')

print('Simple paths in SFG from a -> e: ')
simple_paths = []
simple_paths_nodes = []

for node_pairs in algo.all_simple_edge_paths(g, 'y1', 'y6'):
    weights = [g.edges[u, v]['weight'] for u, v in node_pairs]
    nodes = set(chain.from_iterable(node_pairs))
    simple_paths_nodes.append(nodes)
    simple_paths.append(weights)
    print(weights)

print('\nSimple cycles (loops) in SFG: ')
simple_cycles = []

for nodes in algo.simple_cycles(g):
    weights = [g.edges[u, v]['weight'] for u, v in pairwise_circular(nodes)]
    simple_cycles.append((weights, set(nodes)))
    print(weights)


print('\nFinding combinations of non-touching loops:')

combinations = []


def backtrack(i, comb, node_set):
    if i == len(simple_cycles):
        return

    backtrack(i + 1, comb, node_set)

    if node_set.isdisjoint(simple_cycles[i][1]):
        node_set |= simple_cycles[i][1]
        comb.append(simple_cycles[i][0])
        combinations.append(comb[:])
        backtrack(i + 1, comb, node_set)
        comb.pop()
        node_set -= simple_cycles[i][1]


backtrack(0, [], set())

# note to self: generate node_set for each comb and cache it
# can use it later to calculate delta_i
combinations.sort(key=lambda entry: len(entry))

from itertools import groupby

for size, group in groupby(combinations, lambda entry: len(entry)):
    print(f'Combination size: {size}')
    for comb in group:
        print(f'\t{comb}')

print('\nFinding loops not touching forward paths:')
for path, nodes in zip(simple_paths, simple_paths_nodes):
    print(f'For forward path {path}, combinations of non-touching cycles: ')
    non_touching_indices = [i for i in range(len(simple_cycles)) if simple_cycles[i][1].isdisjoint(nodes)]
    print(non_touching_indices)


terms = []

print('\nTransfer function:')
for path, nodes in zip(simple_paths, simple_paths_nodes):
    p = ''.join(path)
    non_touching_loops = [loops for loops, nodes_ in simple_cycles if nodes_.isdisjoint(nodes)]
    delta = '1'

    for loops in non_touching_loops:
        gain = ''.join(chain.from_iterable(loops))
        if len(loops) % 2:
            delta += ' - ' + gain
        else:
            delta += ' + ' + gain

    terms.append(f'{delta} * {p}')

print(' + '.join(terms))
print(len(' + '.join(terms)) * '-')

delta = '1'

for size, group in groupby(combinations, lambda entry: len(entry)):
    gain = ' + '.join(''.join(chain.from_iterable(comb)) for comb in group)
    gain = f'({gain})'
    if size % 2:
        gain = ' - ' + gain
    else:
        gain = ' + ' + gain

    delta += gain

print(delta)


