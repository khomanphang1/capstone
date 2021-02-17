from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from dataclasses import dataclass
import networkx as nx
import re
import sympy as sp


class ComponentFactory:

    prefix_registry: Dict[str, 'Component'] = {}

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'Component':
        """Creates a component from an LTspice netlist entry.

        The exact type of component created is determined by the first
        character (i.e. prefix) of the netlist entry.

        :param entry: a line in an LTspice netlist
        :return: a component
        """
        # Prefixes are case-insensitive.
        prefix = entry[0].lower()

        if prefix not in cls.prefix_registry:
            raise ValueError(f'No component subclass is registered with prefix '
                             f'"{prefix}".')

        return cls.prefix_registry[prefix].from_netlist_entry(entry)


class TwoTerminal:
    """A mixin class for components with two terminals.
    """

    def __init__(self, pos_node: str, neg_node: str):
        self.pos_node = pos_node
        self.neg_node = neg_node

    @property
    @abstractmethod
    def impedance(self):
        ...


class Component(ABC):

    # Component subclasses must define a prefix to register with the factory.
    prefix: str = NotImplemented

    def __init_subclass__(cls):
        if cls.prefix is NotImplemented:
            raise NotImplementedError('Concrete components must define a '
                                      'prefix character.')

        # Upon the creating a subclass, register its prefix with
        # ComponentFactory.
        ComponentFactory.prefix_registry[cls.prefix] = cls

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        attributes = [f'{k}={v}' for k, v in self.__dict__.items()]
        return str(f'{self.__class__}({", ".join(attributes)})')

    @classmethod
    @abstractmethod
    def from_netlist_entry(cls, entry: str) -> 'Component':
        """Creates a component from a netlist entry string.

        Subclasses must implement this method.

        :param entry: a line in an LTspice netlist
        :return: a component
        """
        ...


class VoltageSource(Component, TwoTerminal):

    prefix = 'v'

    def __init__(self, name: str, pos_node: str, neg_node: str, voltage: str):
        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.voltage = voltage

    def is_dc(self) -> bool:
        try:
            float(self.voltage)
        except ValueError:
            return False
        return True

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'VoltageSource':
        args = entry.split(' ', 3)
        return cls(*args)

    def to_netlist_entry(self) -> str:
        return ' '.join([self.name, self.pos_node, self.neg_node, self.voltage])


class CurrentSource(Component, TwoTerminal):

    prefix = 'i'

    def __init__(self, name: str, pos_node: str, neg_node: str, current: str):
        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.current = current

    def is_dc(self) -> bool:
        try:
            float(self.current)
        except ValueError:
            return False
        return True

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'CurrentSource':
        args = entry.split(' ', 3)
        return cls(*args)

    def to_netlist_entry(self) -> str:
        return ' '.join([self.name, self.pos_node, self.neg_node, self.current])


class VoltageDependentCurrentSource(Component, TwoTerminal):

    prefix = 'g'

    def __init__(self, name: str, pos_node: str, neg_node: str,
                 pos_input_node: str, neg_input_node: str, gain: str):
        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.pos_input_node = pos_input_node
        self.neg_input_node = neg_input_node
        self.gain = gain

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'VoltageDependentCurrentSource':
        args = entry.split(' ', 5)
        return cls(*args)

    def to_netlist_entry(self) -> str:
        return ' '.join([self.name, self.pos_node, self.neg_node, self.pos_input_node,
                         self.neg_input_node, self.gain])


class Resistor(Component, TwoTerminal):

    prefix = 'r'

    def __init__(self, name: str, pos_node: str, neg_node: str, value: str):
        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.value = value

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'Resistor':
        args = entry.split(' ', 3)
        return cls(*args)

    def to_netlist_entry(self) -> str:
        return ' '.join([self.name, self.pos_node, self.neg_node, self.value])

    @property
    def impedance(self):
        return sp.symbols(self.name)


class Capacitor(Component, TwoTerminal):

    prefix = 'c'

    def __init__(self, name: str, pos_node: str, neg_node: str,
                 capacitance: str):
        Component.__init__(self, name)
        TwoTerminal.__init__(self, pos_node, neg_node)
        self.capacitance = capacitance

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'Capacitor':
        args = entry.split(' ', 3)
        return cls(*args)

    def to_netlist_entry(self) -> str:
        return ' '.join([self.name, self.pos_node, self.neg_node, self.capacitance])

    @property
    def impedance(self):
        return 1 / (sp.symbols('s') * sp.symbols(self.name))


class BipolarTransistor(Component):

    prefix = 'q'

    def __init__(self, name: str, collector: str, base: str, emitter: str,
                 substrate: str, model: str):
        Component.__init__(self, name)
        self.collector = collector
        self.base = base
        self.emitter = emitter
        self.substrate = substrate
        self.model = model

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'BipolarTransistor':
        args = entry.split(' ', 5)
        return cls(*args)

    def small_signal_components(self, model: 'HybridPiModel') -> List[Component]:
        rpi = Resistor('RPI_' + self.name, self.base, self.emitter, model.rpi)
        g = VoltageDependentCurrentSource('G_' + self.name, self.collector,
                                          self.emitter, self.base,
                                          self.emitter, model.gm)
        ro = Resistor('RO_' + self.name, self.collector, self.emitter, model.ro)
        return [rpi, g, ro]


transistor_section_pattern = re.compile(r' *--- (\S+) Transistors --- *$')


@dataclass
class HybridPiModel:
    gm: str
    rpi: str
    ro: str

    @classmethod
    def from_ltspice_op_log(cls, log: str) -> Dict[str, 'HybridPiModel']:
        """
        Parses an operating point analysis log file produced by LTspice and
        extracts the hybrid-pi small-signal parameters for each transistor.

        :param op_log_file: an operating point analysis log file
        :param encoding: the file encoding, defaults to "utf-8"
        :return: a dictionary of models with transistor names as keys
        """
        transistor_section = False
        valid_keys = {'gm', 'rpi', 'ro'}
        transistor_names = None
        models = None

        for line in log.splitlines():
            if transistor_section:
                # Currently inside a transistor section.

                # Data in transistor section is whitespace-delimited.
                row = re.findall(r'\S+', line)

                if not row:
                    # The end of a transistor section is marked by an empty
                    # line.
                    transistor_section = False
                    continue

                # Strip trailing ":" character from row header.
                key = row[0][:-1].lower()

                if key == 'name':
                    # Initialize models with transistor names as keys, and
                    # {} as values. As we iterate over subsequent rows, {}
                    # is populated.
                    transistor_names = row[1:]
                    models = dict.fromkeys(transistor_names, {})

                elif key in valid_keys:
                    # Add parameter name-value pair for each transistor.
                    for name, value in zip(transistor_names, row[1:]):
                        models[name][key] = value

            else:
                # Check that the line is a transistor section header. Set
                # the transistor_section flag accordingly.
                match = transistor_section_pattern.match(line)
                # For now, handle only BJTs.
                transistor_section = match and match.group(1) == 'Bipolar'

        for name in models:
            # Construct HybridPiModel instances from using dictionary as kwargs.
            models[name] = cls(**models[name])

        return models


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
    def from_ltspice(cls, netlist: str, op_log: str = None) -> 'Circuit':
        if op_log is None:
            models = {}
        else:
            models = HybridPiModel.from_ltspice_op_log(op_log)

        multigraph = nx.MultiGraph()
        dc_sources = []

        for line in netlist.splitlines():
            if line.startswith('.') or line.startswith('*'):
                # LTspice comments are ignored.
                continue

            # Instantiate component.
            comp = ComponentFactory.from_netlist_entry(line)

            if isinstance(comp, TwoTerminal):
                # Two terminal components are added to the graph as-is.
                multigraph.add_edge(comp.pos_node, comp.neg_node,
                                    key=comp.name, component=comp)

                # Mark DC sources to be turned off later.
                if (isinstance(comp, VoltageSource) or
                        isinstance(comp, CurrentSource)) and comp.is_dc():
                    dc_sources.append(comp)

            elif isinstance(comp, BipolarTransistor):
                # Transistors are first converted to small signal
                # equivalents components.
                model = models[comp.name.lower()]
                small_signal_comps = comp.small_signal_components(model)
                for comp in small_signal_comps:
                    multigraph.add_edge(comp.pos_node, comp.neg_node,
                                        key=comp.name, component=comp)

        if op_log is None:
            return cls(multigraph)

        for source in dc_sources:
            if isinstance(source, VoltageSource):
                nodes = (source.pos_node, source.neg_node)
                relabel_to = next((node for node in nodes if node == '0'),
                                  min(nodes))
                relabel_from = next((node for node in nodes
                                     if node != relabel_to), None)

                if not relabel_from:
                    raise ValueError('Cannot handle shorted DC source yet.')

                # Remove the voltage source.
                multigraph.remove_edge(source.pos_node, source.neg_node,
                                       source.name)

                # Find all components that connects the node relabel_from,
                # and relabel their pos_node and/or neg_nodes.
                for nbr, nbrdict in multigraph.adj[relabel_from].items():
                    for edge in nbrdict.items():
                        # node_from, node_to, edge_key, component
                        # print(relabel_from, nbr, edge[0], edge[1]['instance'])
                        instance = edge[1]['component']

                        if instance.pos_node == relabel_from:
                            instance.pos_node = relabel_to
                        if instance.neg_node == relabel_from:
                            instance.neg_node = relabel_to
                
                # Relabel node relabel_from relabel_to
                nx.relabel_nodes(multigraph, {relabel_from: relabel_to},
                                 copy=False)

            else:
                raise ValueError('Cannot handle DC current sources yet.')

        return cls(multigraph)


if __name__ == '__main__':
    from os import path
    test_data_dir = path.join(path.dirname(__file__), 'test_data')

    netlist_file = path.join(test_data_dir, 'simple_rc.net')
    log_file = path.join(test_data_dir, 'simple_rc.log')

    with open(netlist_file) as f:
        netlist = f.read()

    with open(log_file) as f:
        log = f.read()

    # Instantiate a circuit by passing in the netlist file and log file.
    # The circuit will be converted to small-signal.
    circuit = Circuit.from_ltspice(netlist)

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

    for node in circuit.iter_nodes():
        for nbr, component in circuit.iter_neighbours(node):
            print(f'{node} <-> {nbr}: {component}')

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
