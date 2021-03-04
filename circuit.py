from abc import ABC, abstractmethod
from typing import Dict, Tuple, Callable, Union, Optional
from collections import OrderedDict
import re

import networkx as nx


_si_prefix = {
    'y': 1e-24,  # yocto
    'z': 1e-21,  # zepto
    'a': 1e-18,  # atto
    'f': 1e-15,  # femto
    'p': 1e-12,  # pico
    'n': 1e-9,   # nano
    'u': 1e-6,   # micro
    'm': 1e-3,   # mili
    'c': 1e-2,   # centi
    'd': 1e-1,   # deci
    'k': 1e3,    # kilo
    'M': 1e6,    # mega
    'G': 1e9,    # giga
    'T': 1e12,   # tera
    'P': 1e15,   # peta
    'E': 1e18,   # exa
    'Z': 1e21,   # zetta
    'Y': 1e24,   # yotta
}


def si_prefix_to_float(s) -> float:
    """Converts a string ending in an SI prefix to a float.

    Args:
        s: A string.

    Returns:
        A floating point number.
    """
    if not isinstance(s, str):
        return float(s)

    s = s.strip()
    last = s[-1] if s else ''

    if not last.isnumeric() and last != '.':
        if last not in _si_prefix:
            raise ValueError
        return float(s[:-1]) * _si_prefix[last]

    else:
        return float(s)


class ComponentFactory:
    """A factory class that handles component construction."""

    _netlist_prefix_registry = {}

    @classmethod
    def register(cls, prefix, constructor: Callable[[str], 'Component']):
        cls._netlist_prefix_registry[prefix] = constructor

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'Component':
        """Creates a component from a netlist entry.

        Args:
            entry: A line in a LTSpice netlist.

        Returns:
            A component.
        """
        prefix = entry[0].lower()
        constructor = cls._netlist_prefix_registry.get(prefix)

        if not constructor:
            raise ValueError(f'No component found with prefix {prefix}.')

        return constructor(entry)


class TwoTerminal:
    """A mixin class for components with two terminals.
    """

    def __init__(self, pos_node: str, neg_node: str):
        self.pos_node = pos_node
        self.neg_node = neg_node

    def is_shorted(self):
        return self.pos_node == self.neg_node


class Component(ABC):
    """Component base class.
    """

    _prefix = NotImplemented

    def __init_subclass__(cls):
        # Register the subclass constructor with ComponentFactory.
        if cls._prefix is NotImplemented:
            raise NotImplementedError('Component subclass must define a prefix.')

        ComponentFactory.register(cls._prefix, cls.from_netlist_entry)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        attributes = [f'{k}={v}' for k, v in self.__dict__.items()]
        return str(f'{self.__class__.__name__}({", ".join(attributes)})')

    @classmethod
    @abstractmethod
    def from_netlist_entry(cls, entry: str) -> 'Component':
        """Creates a component from a netlist entry.

        Args:
            entry: A netlist entry.

        Returns:
            A component.
        """
        ...

    @abstractmethod
    def to_netlist_entry(self) -> str:
        """Converts a component to a netlist entry.

        Returns:
            A netlist entry.
        """
        ...


class VoltageSource(Component, TwoTerminal):

    _prefix = 'v'

    def __init__(self, name: str,
                 pos_node: str,
                 neg_node: str,
                 voltage: Union[str, float]):

        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.voltage = voltage

    def is_dc(self) -> bool:
        return isinstance(self.voltage, float)

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'VoltageSource':
        name, pos_node, neg_node, voltage = entry.split(' ', 3)

        # A numeric voltage value is interpreted as DC.
        try:
            voltage = si_prefix_to_float(voltage)
        except ValueError:
            pass

        return VoltageSource(name, pos_node, neg_node, voltage)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.pos_node, self.neg_node, self.voltage)
        return ' '.join(str(arg) for arg in args)


class CurrentSource(Component, TwoTerminal):

    _prefix = 'i'

    def __init__(self, name: str,
                 pos_node: str,
                 neg_node: str,
                 current: Union[str, float]):

        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.current = current

    def is_dc(self) -> bool:
        return isinstance(self.current, float)

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'CurrentSource':
        name, pos_node, neg_node, current = entry.split(' ', 3)

        # A numeric voltage value is interpreted as DC.
        try:
            current = si_prefix_to_float(current)
        except ValueError:
            pass

        return CurrentSource(name, pos_node, neg_node, current)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.pos_node, self.neg_node, self.current)
        return ' '.join(str(arg) for arg in args)


class VoltageDependentVoltageSource(Component, TwoTerminal):

    _prefix = 'e'

    def __init__(self, name: str,
                 pos_node: str,
                 neg_node: str,
                 pos_input_node: str,
                 neg_input_node: str,
                 gain: Union[str, float]):

        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.pos_input_node = pos_input_node
        self.neg_input_node = neg_input_node
        self.gain = gain

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'VoltageDependentVoltageSource':
        name, pos_node, neg_node, pos_input_node, neg_input_node, gain = \
            entry.split(' ', 5)

        try:
            gain = si_prefix_to_float(gain)
        except ValueError:
            pass

        return VoltageDependentVoltageSource(name, pos_node, neg_node,
                                             pos_input_node, neg_input_node,
                                             gain)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.pos_node, self.neg_node, self.pos_input_node,
                self.neg_input_node, self.gain)

        return ' '.join(str(arg) for arg in args)


class VoltageDependentCurrentSource(Component, TwoTerminal):

    _prefix = 'g'

    def __init__(self, name: str,
                 pos_node: str,
                 neg_node: str,
                 pos_input_node: str,
                 neg_input_node: str,
                 gain: Union[str, float]):

        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.pos_input_node = pos_input_node
        self.neg_input_node = neg_input_node
        self.gain = gain

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'VoltageDependentCurrentSource':
        name, pos_node, neg_node, pos_input_node, neg_input_node, gain = \
            entry.split(' ', 5)

        try:
            gain = si_prefix_to_float(gain)
        except ValueError:
            pass

        return VoltageDependentCurrentSource(name, pos_node, neg_node,
                                             pos_input_node, neg_input_node,
                                             gain)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.pos_node, self.neg_node, self.pos_input_node,
                self.neg_input_node, self.gain)

        return ' '.join(str(arg) for arg in args)


class Resistor(Component, TwoTerminal):

    _prefix = 'r'

    def __init__(self, name: str,
                 pos_node: str,
                 neg_node: str,
                 resistance: float):

        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.resistance = resistance

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'Resistor':
        name, pos_node, neg_node, resistance = entry.split(' ', 3)
        resistance = si_prefix_to_float(resistance)

        return Resistor(name, pos_node, neg_node, resistance)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.pos_node, self.neg_node, self.resistance)
        return ' '.join(str(arg) for arg in args)


class Capacitor(Component, TwoTerminal):

    _prefix = 'c'

    def __init__(self, name: str,
                 pos_node: str,
                 neg_node: str,
                 capacitance: float):
        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.capacitance = capacitance

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'Capacitor':
        name, pos_node, neg_node, capacitance = entry.split(' ', 3)
        capacitance = si_prefix_to_float(capacitance)

        return Capacitor(name, pos_node, neg_node, capacitance)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.pos_node, self.neg_node, self.capacitance)
        return ' '.join(str(arg) for arg in args)


class BipolarTransistor(Component):

    _prefix = 'q'

    def __init__(self, name: str,
                 collector: str,
                 base: str,
                 emitter: str,
                 substrate: str,
                 model: str):

        Component.__init__(self, name)
        self.collector = collector
        self.base = base
        self.emitter = emitter
        self.substrate = substrate
        self.model = model

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'BipolarTransistor':
        name, collector, base, emitter, substrate, model = \
            entry.split(' ', 5)
        return BipolarTransistor(name, collector, base, emitter, substrate,
                                 model)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.collector, self.base, self.emitter,
                self.substrate, self.model)

        return ' '.join(args)

    def small_signal_equivalent(self, g_m: float, r_pi: float, r_o: float) \
            -> Tuple[Component, Component, Component]:
        """Finds the small-signal equivalent of the transistor.

        Args:
            g_m: The transconductance.
            r_pi: The resistance between the base and emitter nodes.
            r_o: The resistance between the collector and emitter nodes.

        Returns:
            A tuple (g, r_pi, r_o), where g is a voltage-dependent current
            source, and r_pi and r_o are resistors.
        """

        r_pi = Resistor(
            f'R_PI_{self.name}',
            self.base,
            self.emitter,
            r_pi
        )

        g = VoltageDependentCurrentSource(
            f'G_{self.name}',
            self.collector,
            self.emitter,
            self.base,
            self.emitter,
            g_m
        )

        r_o = Resistor(
            f'R_O_{self.name}',
            self.collector,
            self.emitter,
            r_o
        )

        return (g, r_pi, r_o)


transistor_section_pattern = re.compile(r' *--- (\S+) Transistors --- *$')


def get_hybrid_pi_parameters(op_point_log: str) \
        -> Dict[str, Tuple[float, float, float]]:
    """Extract the hybrid-pi model parameters.

    Args:
        op_point_log: An LTSpice operating point analysis log.

    Returns:
        A dictionary that maps transistor names to (g_m, r_pi, r_o) tuples.

    Todo:
        Add support MOSFET transistors.
    """
    in_transistor_section = False
    relevant_rows = OrderedDict.fromkeys(('Name', 'Gm', 'Rpi', 'Ro'))

    for line in op_point_log.splitlines():

        if not in_transistor_section:
            in_transistor_section = bool(transistor_section_pattern.match(line))
            continue

        row = re.findall(r'\S+', line)

        if not row:
            in_transistor_section = False
            continue

        row_header = row[0][:-1]

        if row_header in relevant_rows:
            if row_header == 'Name':
                relevant_rows[row_header] = [name.lower() for name in row[1:]]
            else:
                relevant_rows[row_header] = [si_prefix_to_float(val)
                                             for val in row[1:]]

    names = relevant_rows.pop('Name')
    params = zip(*(val for _, val in relevant_rows.items()))  # (Gm, Rpi, Ro)

    return {name: param for name, param in zip(names, params)}


class Circuit:
    """Class that represents an ideal small-signal circuit.
    """
    def __init__(self, multigraph: nx.MultiGraph):
        self.multigraph = multigraph

    def print_components(self):
        for e in self.multigraph.edges(data='component'):
            src_node, dest_node, component = e
            print(src_node, dest_node, component)

    def iter_nodes(self):
        yield from self.multigraph

    def iter_neighbours(self, node):
        for nbr, edgedict in self.multigraph.adj[node].items():
            for edge_key, edge_attribs in edgedict.items():
                yield nbr, edge_attribs['component']

    def iter_components(self) -> Tuple[str, str, Component]:
        for e in self.multigraph.edges(data='component'):
            src_node, dest_node, component = e
            yield src_node, dest_node, component

    def netlist(self) -> str:
        return '\n'.join(c.to_netlist_entry() for _, _, c in self.iter_components())

    @classmethod
    def from_ltspice_schematic(cls, schematic: str,
                               op_point_log: Optional[str] = None) -> 'Circuit':
        import ltspice

        netlist = ltspice.asc_to_netlist(schematic)
        return cls.from_ltspice_netlist(netlist, op_point_log)

    @classmethod
    def from_ltspice_netlist(cls, netlist: str,
                             op_point_log: Optional[str] = None) -> 'Circuit':

        hybrid_pi_parameters = get_hybrid_pi_parameters(op_point_log) if \
                                  op_point_log else {}
        graph = nx.MultiGraph()
        dc_sources = []

        for line in netlist.splitlines():

            if line.startswith(('.', '*')):
                # Ignore comments and models.
                continue

            component = ComponentFactory.from_netlist_entry(line)

            if isinstance(component, TwoTerminal):
                # Add two-terminal components to circuit as-is.
                graph.add_edge(component.pos_node, component.neg_node,
                               key=component.name, component=component)

                # Mark DC sources to be turned off later.
                if (isinstance(component, (VoltageSource, CurrentSource)) and
                        component.is_dc()):
                    dc_sources.append(component)

            elif isinstance(component, BipolarTransistor):
                # Replace transistors with small-signal equivalent.
                g_m, r_pi, r_o = hybrid_pi_parameters[component.name.lower()]

                for comp in component.small_signal_equivalent(g_m, r_pi, r_o):
                    graph.add_edge(comp.pos_node, comp.neg_node,
                                   key=comp.name, component=comp)

        for node in graph:
            graph.nodes[node]['alias'] = set()

        if not op_point_log:
            return Circuit(graph)

        for source in dc_sources:

            if isinstance(source, VoltageSource):
                node_names = (source.pos_node, source.neg_node)
                rename_to = next((node for node in node_names if node == '0'),
                                 min(node_names))
                rename_from = next((node for node in node_names
                                    if node != rename_to), None)

                if not rename_from:
                    raise ValueError(f'Invalid circuit: source {source.name}' 
                                     'is shorted.')

                graph.nodes[rename_to]['alias'].add(rename_from)

                graph.remove_edge(source.pos_node,
                                  source.neg_node,
                                  source.name)

                for nbr, nbrdict in graph.adj[rename_from].items():
                    for edge in nbrdict.items():
                        # node_from, node_to, edge_key, component
                        # print(relabel_from, nbr, edge[0], edge[1]['instance'])
                        instance = edge[1]['component']

                        if instance.pos_node == rename_from:
                            instance.pos_node = rename_to

                        if instance.neg_node == rename_from:
                            instance.neg_node = rename_to

                # Relabel node relabel_from as relabel_to
                nx.relabel_nodes(graph, {rename_from: rename_to},
                                 copy=False)

        return Circuit(graph)


if __name__ == '__main__':

    from os import path
    test_data_dir = path.join(path.dirname(__file__), 'test_data')

    # netlist_file = path.join(test_data_dir, '2N3904_common_emitter.net')
    # log_file = path.join(test_data_dir, '2N3904_common_emitter.log')

    # schematic_file = path.join(test_data_dir, 'transresistance.asc')
    schematic_file = path.join(test_data_dir, 'common_source.asc')

    # with open(netlist_file) as f:
    #     netlist = f.read()
    #
    # with open(log_file) as f:
    #     op_point_log = f.read()

    with open(schematic_file) as f:
        schematic = f.read()

    circ = Circuit.from_ltspice_schematic(schematic, op_point_log=None)
    circ.print_components()
    pass

    # Instantiate a circuit by passing in the netlist file and log file.
    # The circuit will be converted to small-signal.
    # circuit = Circuit.from_ltspice(netlist, log)

    # print('\nIterating through nodes:')
    # for node in circuit.multigraph.nodes:
    #     print(node)
    #
    # print('\nIterating through edges:')
    # for edge in circuit.multigraph.edges:
    #     src_node, dst_node, component_name = edge
    #     print(f'{component_name}: {src_node} <-> {dst_node}')

    # print('\nIterating through edges, this time with component names and objects:')
    # for edge in circuit.multigraph.edges(keys=True, data='component'):
    #     src_node, dst_node, component_name, component_obj = edge
    #     print(f'{component_name}: {src_node} <-> {dst_node}')
    #     print(f'\t{component_obj}')
    #
    #     # Node that because the multigraph is undirected, we need some way to
    #     # keep track of the polarity of components. This is done by inspecting
    #     # component objects, which are instances of Component classes. They
    #     # specify which node is positive and which node is negative.
    #
    #     # Example:
    #     # V2: 0 <-> Vin
    #     #
    #     # V2 is the name of a voltage source.
    #     # V2 exists between node 0 and node Vin.
    #     # V2.pos_node is Vin, meaning Vin is the positive node.
    #     # V2.neg_node is 0, meaning 0 is the negative node.

    # for node in circuit.iter_nodes():
    #     for nbr, component in circuit.iter_neighbours(node):
    #         print(f'{node} <-> {nbr}: {component}')

    # for n, nbrsdict in circuit.multigraph.adjacency():
    #     print('*' * 100)
    #     print(f'Current node = {n}')
    #     # print(f'\tNeighbours = {[nbr for nbr in nbrsdict]}')
    #
    #     for nbr, edgedict in nbrsdict.items():
    #         print(f'\tNeighbour = {nbr}')
    #         # print(f'\tEdges between {n} and {nbr}: {[key for key in edgedict]}')
    #
    #         for key, edge_attrib_dict in edgedict.items():
    #             print(f'\t\tComponent {key}: {n} <-> {nbr}')
    #             component_obj = edge_attrib_dict['component']
    #             print(f'\t\t\t{component_obj}')


    # print(f'\nAccess the neighbours of a specific node "VE":')
    # for nbr, edgedict in circuit.multigraph['VE'].items():
    #     print(f'\tNeighbour: {nbr}')
    #     for key, edge_attrib_dict in edgedict.items():
    #         print(f'\t\tComponent {key}: {n} <-> {nbr}')
    #         component_obj = edge_attrib_dict['component']
    #         print(f'\t\t{component_obj}')
