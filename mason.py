from itertools import chain, tee, zip_longest, groupby
from typing import List, Set, Tuple, Any, Callable, Iterator
from collections import OrderedDict

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


def disjoint_combinations(items: List, key: Callable[[Any], Set]) \
        -> Iterator[Tuple[OrderedDict, ...]]:
    """Iterates over combinations of disjoint items.

    Iterates over combinations of disjoint items. Items are considered disjoint
    if their key sets are disjoint.

    Args:
        items: A list of items to select from.
        key: A function that maps each item to a set.

    Yields:
        A tuple of items.
    """
    def dfs(i: int, comb: List, keys: Set) \
            -> Iterator[Tuple[OrderedDict, ...]]:

        if i == len(items):
            return

        yield from dfs(i + 1, comb, keys)

        if keys.isdisjoint(items[i]):
            keys |= key(items[i])
            comb.append(items[i])
            yield tuple(comb)
            yield from dfs(i + 1, comb, keys)
            comb.pop()
            keys -= key(items[i])

    yield from dfs(0, [], set())


def determinant(graph: nx.DiGraph,
                cycle_combinations: List[Tuple[OrderedDict, ...]],
                path: OrderedDict = None) -> sp.core.expr.Expr:

    path = path or OrderedDict()
    gain_products_sums = []

    for size, group in groupby(cycle_combinations, key=len):

        gain_products = []

        for comb in group:

            if all(path.keys().isdisjoint(cycle.keys()) for cycle in comb):
                # If all cycles in this combination are pairwise disjoint with
                # the given path, compute the product of loop gains.

                gains = (graph.edges[u, v]['gain']
                         for cycle in comb
                         for u, v in pairwise_circular(cycle))
                gain_products.append(sp.Mul.fromiter(gains))

        sign = -1 if size % 2 else 1
        gain_products_sums.append(sp.Add.fromiter(gain_products) * sign)

    return 1 + sp.Add.fromiter(gain_products_sums)


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

    # Find all simple paths from the input node to the output node.
    paths = [OrderedDict.fromkeys(nodes) for nodes in all_simple_paths(graph, input_node, output_node)]

    # Find all simple cycles.
    cycles = [OrderedDict.fromkeys(nodes) for nodes in simple_cycles(graph)]

    # Find all combinations of non-touching cycles, sorted by combination size.
    cycle_combinations = list(disjoint_combinations(cycles, key=lambda cycle: cycle.keys()))
    cycle_combinations.sort(key=len)

    # Find overall determinant.
    denom = determinant(graph, cycle_combinations)

    # For each forward path, find its gain and determinant.
    path_gains = (sp.Mul.fromiter(graph.edges[u, v]['gain'] for u, v in pairwise(path))
                  for path in paths)
    determs = (determinant(graph, cycle_combinations, path=path)
               for path in paths)
    sum_terms = (sp.Mul(path_gain, determ) for path_gain, determ in zip(path_gains, determs))
    numer = sp.Add.fromiter(sum_terms)

    return numer / denom


if __name__ == '__main__':
    graph = nx.DiGraph()

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

    for src, dest, gain in edges:
        graph.add_edge(src, dest, gain=sp.Symbol(gain))

    sp.init_printing(use_unicode=True)
    h = transfer_function(graph, 'y1', 'y6')
    sp.pprint(h)