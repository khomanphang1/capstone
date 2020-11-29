from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass
import re
import networkx as nx


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
        rpi = Resistor('rpi_' + self.name, self.base, self.emitter, model.rpi)
        g = VoltageDependentCurrentSource('g_' + self.name, self.collector,
                                          self.emitter, self.base,
                                          self.emitter, model.gm)
        ro = Resistor('ro_' + self.name, self.collector, self.emitter, model.ro)
        return [rpi, g, ro]


transistor_section_pattern = re.compile(r' *--- (\S+) Transistors --- *$')


@dataclass
class HybridPiModel:
    gm: str
    rpi: str
    ro: str

    @classmethod
    def from_ltspice_op_log(cls, op_log_file: str, encoding: str = 'utf-8') \
            -> Dict[str, 'HybridPiModel']:
        """
        Parses an operating point analysis log file produced by LTspice and
        extracts the hybrid-pi small-signal model for each transistor.

        :param op_log_file: an operating point analysis log file
        :param encoding: the file encoding, defaults to "utf-8"
        :return: a dictionary of models with transistor names as keys
        """
        with open(op_log_file, 'r', encoding=encoding) as log:
            transistor_section = False
            valid_keys = {'gm', 'rpi', 'ro'}
            transistor_names = None
            models = None

            for line in log:
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
        for e in self.multigraph.edges(data=True):
            src_node, dest_node, edge_attrbs = e
            print(src_node, dest_node, edge_attrbs['component'])

    @classmethod
    def from_ltspice(cls, netlist_file: str, op_log_file: str) -> 'Circuit':
        models = HybridPiModel.from_ltspice_op_log(op_log_file)
        multigraph = nx.MultiGraph()
        dc_sources = []
        with open(netlist_file, 'r', encoding='utf-8') as netlist:
            for line in netlist:
                if line.startswith('.') or line.startswith('*'):
                    # LTspice comments are ignored.
                    continue

                # Instantiate component.
                comp = ComponentFactory.from_netlist_entry(line.rstrip('\n'))

                if isinstance(comp, TwoTerminal):
                    # Two terminal components are added relabel_to the graph as-is.
                    multigraph.add_edge(comp.pos_node, comp.neg_node,
                                        key=comp.name, component=comp)

                    # Mark DC sources relabel_to be turned off later.
                    if (isinstance(comp, VoltageSource) or
                            isinstance(comp, CurrentSource)) and comp.is_dc():
                        dc_sources.append(comp)

                elif isinstance(comp, BipolarTransistor):
                    # Transistors are first converted relabel_to small signal
                    # equivalents components.
                    model = models[comp.name.lower()]
                    small_signal_comps = comp.small_signal_components(model)
                    for comp in small_signal_comps:
                        multigraph.add_edge(comp.pos_node, comp.neg_node,
                                            key=comp.name, component=comp)

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

    netlist_file = path.join(test_data_dir, 'npn_ce.cir')
    log_file = path.join(test_data_dir, 'npn_ce.log')

    circuit = Circuit.from_ltspice(netlist_file, log_file)
    circuit.print_components()

