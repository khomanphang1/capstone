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
            # Handle cases where some prefixes are case-insensitive
            last = last.lower()

        if last not in _si_prefix:
            # Neither the lower case or original case version of the prefix
            # is valid
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
        print(prefix)
        print(cls._netlist_prefix_registry)
        constructor = cls._netlist_prefix_registry.get(prefix)

        if not constructor:
            print("not registered", prefix)
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

    @property
    @abstractmethod
    def value(self):
        ...


class Component(ABC):
    """Component base class.
    """

    # The prefix field is used to indicate that a subclass is capable of
    # parsing a particular type of netlist component. For example, if a
    # subclass sets prefix = "V", then, when the parser encounters the
    # netlist entry "Vs n001 n002 ...", it will invoke the from_netlist_entry
    # function for that particular subclass. This makes it easier to add support
    # for additional components, who can simply inherit from this base class.

    _prefix = NotImplemented

    def __init_subclass__(cls):
        print("in init subclass", cls)
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

    @property
    def value(self):
        return self.voltage


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

    @property
    def value(self):
        return self.current


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

    @property
    def value(self):
        return self.gain


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

    @property
    def value(self):
        return self.gain


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

    @property
    def value(self):
        return self.resistance


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

    @property
    def value(self):
        return self.capacitance


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
        print("in from_netlist_entry:",entry)
        name, collector, base, emitter, substrate, model = \
            entry.split(' ', 5)
        print(name, ", ", collector, ", ", base, ", ", emitter, ", ", substrate, " , ", model)
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

        return g, r_pi, r_o

class MOSFET(Component):

    _prefix = 'm'

    def __init__(self, name: str,
                 source: str,
                 gate: str,
                 drain: str,
                 substrate: str,
                 model: str):

        Component.__init__(self, name)
        self.source = source
        self.gate = gate
        self.drain = drain
        self.substrate = substrate
        self.model = model

    @classmethod
    def from_netlist_entry(cls, entry: str) -> 'MOSFET':
        print("in from_netlist_entry:",entry)
        name, source, gate, drain, substrate, model = \
            entry.split(' ', 5)
        if(model.startswith("P") ):
            print("starts with p:")
            print(name, ", ", source, ", ", gate, ", ", drain, ", ", substrate, " , ", model)
            return MOSFET(name, source, gate, drain, substrate,
                                 model)
        print(name, ", ", source, ", ", gate, ", ", drain, ", ", substrate, " , ", model)
        return MOSFET(name, drain, gate, source, substrate,
                                 model)

    def to_netlist_entry(self) -> str:
        args = (self.name, self.source, self.gate, self.drain,
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
            self.gate,
            self.source,
            1e25
        )

        g = VoltageDependentCurrentSource(
            f'G_{self.name}',
            self.source,
            self.drain,
            self.gate,
            self.source,
            g_m
        )

        r_o = Resistor(
            f'R_O_{self.name}',
            self.drain,
            self.source,
            r_o
        )

        return g, r_pi, r_o

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
    print("in get_hybrid_pi_parameters")
    in_transistor_section = False
    relevant_rows = OrderedDict.fromkeys(('Name', 'Gm', 'Rpi', 'Ro', 'Id', 'Gds'))

    for line in op_point_log.splitlines():
        print("the line that is being parsed:\n", line,"\n")

        if not in_transistor_section:

            in_transistor_section = bool(transistor_section_pattern.match(line))
            print("transistor regular expression matching:\n",line,"\n",transistor_section_pattern.match(line), transistor_section_pattern,"\n")
            continue
        
        row = re.findall(r'\S+', line)
        print(row)
        if not row:
            in_transistor_section = False
            continue

        row_header = row[0][:-1]
        print("row_header:",row_header)
        if row_header in relevant_rows:
            if row_header == 'Name':
                relevant_rows[row_header] = [name.lower() for name in row[1:]]
            else:
                relevant_rows[row_header] = [si_prefix_to_float(val)
                                             for val in row[1:]]

    
    print("after loop",relevant_rows,"\n")
    names = relevant_rows.pop('Name')
    print("names:",names)
    if(len(names) and names[0][0] == 'm'):
        print("inside:",relevant_rows['Gds'])
        _Id = relevant_rows.pop('Id')
        print("Id",_Id)
        _Gds = relevant_rows.pop('Gds')
        print("_Gds",_Gds)
        _lambda = [ _Gds[i]/_Id[i] for i in range(len(_Gds))] # [ _Gds[i]/_Id[i] for i in range(len(_Gds))] , [_Gds[0]/_Id[0], _Gds[1]/_Id[1]]
        print("lambda:",_lambda)
        relevant_rows['Ro'] = [ 1 / ( _lambda[i] * _Id[i]) for i in range(len(_lambda))] # [ 1 / ( _lambda[i] * _Id[i]) for i in range(len(_lambda))] , [1 / ( _lambda[0] * _Id[0]) , 1 / ( _lambda[1] * _Id[1])]
        print(relevant_rows['Ro'])
        relevant_rows['Rpi'] = [ 1e25 for i in range(len(_Gds))] # [ 1e25 for i in range(len(_Gds))]
        print(relevant_rows['Rpi'])
    print("after loop",relevant_rows,"\n")
    params = zip(*(val for _, val in relevant_rows.items() if val is not None))  # (Gm, Rpi, Ro)
    print("exit get_hybrid_pi_parameters")
    return {name: param for name, param in zip(names, params)}


class Circuit:
    """Class that represents an ideal small-signal circuit.
    """
    def __init__(self, multigraph: nx.MultiGraph):
        self.multigraph = multigraph

    def parameters(self):
        params = {comp.name: comp.value
                  for _, _, comp in self.iter_components()
                  if type(comp.value) is float}

        params['f'] = 1e3

        return params

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
        print("op log:",op_point_log)
        hybrid_pi_parameters = get_hybrid_pi_parameters(op_point_log) if \
                                  op_point_log else {}
        print("parameters:",hybrid_pi_parameters)
        graph = nx.MultiGraph()
        dc_sources = []

        print("in from_ltspice_netlist!!!")
        for line in netlist.splitlines():

            if line.startswith(('.', '*', ';', '+')):
                # Ignore comments and models.
                continue
            print("in line loop", line)
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
                print("before small signal equivalent")
                g_m, r_pi, r_o = hybrid_pi_parameters[component.name.lower()]
                print(f"parameters: {g_m},{r_pi},{r_o}")
                for comp in component.small_signal_equivalent(g_m, r_pi, r_o):
                    graph.add_edge(comp.pos_node, comp.neg_node,
                                   key=comp.name, component=comp)
                print("after small signal equivalent")
                
            elif isinstance(component, MOSFET):
                # Replace transistors with small-signal equivalent.
                print("before small signal equivalent in MOSFET:",hybrid_pi_parameters)
                print(component.name)
                g_m, r_pi, r_o = hybrid_pi_parameters[component.name.lower()]
                print(f"parameters: {g_m},{r_pi},{r_o}")
                for comp in component.small_signal_equivalent(g_m, r_pi, r_o):
                    graph.add_edge(comp.pos_node, comp.neg_node,
                                   key=comp.name, component=comp)
                print("after small signal equivalent")
        print("after from_ltspice_netlist!!!")
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

    import os
    import json

    root = os.path.join(os.path.dirname(__file__), 'test_data')
    json_path = os.path.join(root, 'json', 'ideal_common_source.json')

    with open(json_path, 'r') as f:
        args = json.loads(f.read())

    circ = Circuit.from_ltspice_netlist(args['netlist'],
                                        args.get('op_point_log'))
    circ.print_components()
    pass
