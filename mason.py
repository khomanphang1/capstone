from itertools import chain, tee, zip_longest
from typing import List, Set, Tuple, Generator, Any, Callable, Iterator

import sympy as sp
import networkx as nx
from networkx.algorithms import all_simple_paths, simple_cycles


def pairwise(iterable):
    """Returns a pairwise iterator."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def pairwise_circular(iterable):
    """Returns a pairwise circular iterator."""
    a, b = tee(iterable)
    first = next(b, None)
    return zip_longest(a, b, fillvalue=first)


def disjoint_set_combination_indices(sets: List[Set]) -> Generator[Iterator[int], None, None]:

    # Uses a DFS backtracking algorithm to generate all disjoint combinations
    # of sets. Yields the set indices for each combination.
    def backtrack(i: int, comb: List[int], set: Set) -> List[int]:
        if i == len(sets):
            return

        yield from backtrack(i + 1, comb, set)

        if set.isdisjoint(sets[i]):
            set |= sets[i]
            comb.append(i)
            yield iter(comb)
            yield from backtrack(i + 1, comb, set)
            comb.pop()
            set -= sets[i]

    # Convert the set indices to getter functions.
    yield from backtrack(0, [], set())


def determinant(cycles_gains, cycles_nodes, path_nodes=None) -> str:
    """Computes the determinant of cycles not touching the given path.

    Args:
        cycles_gains:
        cycles_nodes:
        path_nodes:

    Returns:
        A string that represents the determinant.
    """
    return ''


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

    # Find all simple paths from the input node to the output node. For each
    # path, store the edge gains and the set of (unique) nodes on the path.

    paths = all_simple_paths(graph, input_node, output_node)

    paths_gains = []
    paths_nodes = []

    for path in all_simple_paths(graph, input_node, output_node):
        gains = [graph.edges[u, v]['weight'] for u, v in pairwise(path)]
        paths_gains.append(gains)
        paths_nodes.append(set(path))

    # Find all simple cycles in the graph. For each cycle, store the edge gains
    # and the set of (unique) nodes in the cycle.

    cycles_gains = []
    cycles_nodes = []

    for cycle in simple_cycles(graph):
        gains = [graph.edges[u, v]['weight'] for u, v in pairwise_circular(cycle)]
        cycles_gains.append(gains)
        cycles_nodes.append(set(cycle))

    # To find non-touching combinations of cycles, examine the set of nodes for
    # each cycle. If a collection of node sets are disjoint, then the
    # corresponding cycles are non-touching.
    combinations = [[cycles_gains[i] for i in indices] for indices
                    in disjoint_set_combination_indices(cycles_nodes)]

    # Sort the combinations of cycles by size. This makes it easier to
    # compute the determinant summation, where the sign of each term is
    # dependent on the size.
    combinations.sort(key=len)




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


