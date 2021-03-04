from itertools import tee, zip_longest, groupby
from typing import List, Set, Tuple, Any, Callable, Iterator, Optional
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
        -> Iterator[Tuple]:
    """Iterates over combinations of disjoint items.

    Iterates over combinations of disjoint items. Items are considered disjoint
    if their key sets are disjoint.

    Args:
        items: A list of items to select from.
        key: A function that maps each item to a set.

    Yields:
        A tuple of items that constitutes a combination.
    """
    def dfs(i: int, comb: List, keys: Set) -> Iterator[Tuple]:

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
                path: Optional[OrderedDict] = None) -> sp.Expr:
    """Finds the determinant of an SFG.

    Finds the determinant of an SFG, considering only feedback loops not
    touching a given simple path. If no simple path is given, all feedback
    loops are considered.

    Args:
        graph: An SFG.
        cycle_combinations: All combinations of non-touching cycles in the SFG.
        path: Optional; A simple path with which feedback loops should not
            intersect.

    Returns:
        The determinant as a symbolic expression.
    """

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

        # Odd-sized combinations have a negative sign.
        sign = -1 if size % 2 else 1
        gain_products_sums.append(sp.Add.fromiter(gain_products) * sign)

    return 1 + sp.Add.fromiter(gain_products_sums)


def transfer_function(sfg: nx.DiGraph, input_node: str, output_node: str) \
        -> sp.Expr:
    """Computes the transfer function of an SFG.

    Args:
        sfg: An SFG with weighted edges.
        input_node: The name of the input node.
        output_node: The name of the output node.

    Returns:
        A string that represents the transfer function from the input to output
        node.

    Todo:
        handle input nodes differently.
    """

    # Find all simple paths from the input node to the output node.
    paths = [OrderedDict.fromkeys(nodes) for nodes
             in all_simple_paths(sfg, input_node, output_node)]

    # Find all simple cycles.
    cycles = [OrderedDict.fromkeys(nodes) for nodes in simple_cycles(sfg)]

    # Find all combinations of non-touching cycles, sorted by combination size.
    cycle_combinations = list(disjoint_combinations(
        cycles, key=lambda cycle: cycle.keys()))
    cycle_combinations.sort(key=len)

    # Find overall determinant.
    denom = determinant(sfg, cycle_combinations)

    # For each forward path, find its gain and determinant. Then, find the sum
    # of their products.
    path_gains = (sp.Mul.fromiter(sfg.edges[u, v]['gain']
                                  for u, v in pairwise(path))
                  for path in paths)
    determs = (determinant(sfg, cycle_combinations, path) for path in paths)
    sum_terms = (sp.Mul(path_gain, determ)
                 for path_gain, determ in zip(path_gains, determs))
    numer = sp.Add.fromiter(sum_terms)

    return numer / denom


if __name__ == '__main__':
    # Example:
    # Find the transfer function between two nodes in an SFG. For simplicity,
    # the gain associated with each edge is a single, unique variable.

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
        # Insert the edge, and its gain attribute to a symbolic variable.
        graph.add_edge(src, dest, gain=sp.Symbol(gain))

    h = transfer_function(graph, 'y1', 'y6')
    sp.pprint(h, use_unicode=True)

    ltx = sp.latex(h)
    print(ltx)




