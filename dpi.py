from importlib.resources import path
import re
import networkx as nx
import circuit_parser as cir
from collections import defaultdict
import sympy as sy
from sympy import symbols

class test:
    def __init__(self):
        pass

class MetaComponent(type):
    def __new__(cls, name, bases, attrs):
        
        
        return type(name, bases, attrs)
        pass
    def __init__(cls, name , bases, attrs):
    
        pass


class Component(metaclass = MetaComponent):
    def __init__(self, name, **kwargs):
        
        self.name = name
        self.type = self.__class__
        
        if isinstance(self, Resistor):
            self.resistance = kwargs["resistance"]
           
                
        elif isinstance(self, VoltageSource):
            self.voltage = kwargs["voltage"]
            
        
        elif isinstance(self, CurrentSource):
            self.current = kwargs["current"]
            self.direction = kwargs["direction"]
            
        elif isinstance(self, Capacitor):
            self.capacitance = kwargs["capacitance"]
        
        #
        #... ... for more types
        

class VoltageSource(Component):
    def __init__(self, name , voltage):
        super().__init__( name = name, voltage = voltage )
    
        
class CurrentSource(Component):
    def __init__(self, name , current, direc):
        super().__init__( name = name , current = current, direction = direc)
        #control voltage is a tuple with positive node and negative node. Voltage difference is Vposnode - Vneganode
    def __repr__(self):
        return "current source:" + self.name + "current:" + str(self.direction) + self.current
        
class Resistor(Component):
    def __init__(self, name , value):
        #print(super().__init__)
        super().__init__( name = name, resistance = value)
        
    def __repr__(self):
        return "Resistor:" + self.name + " resistance:" + str(self.resistance)

class Capacitor(Component):
    def __init__(self, name , capacitance):
        super().__init__( name = name , capacitance = capacitance)
    
    def __repr__(self):
        return "Capacitance:" + self.name + " capacitance:" + str(self.capacitance)
        


class SFG():
    def __init__(self):
        self.graph = nx.DiGraph()
        self.edges = []
    
    def add_edge(self, source , target , wt):
        self.graph.add_edge(source, target , weight = wt)
    
    def add_all_edges(self, edges):
        self.graph.add_edges_from(edges)

def removing_branch(sfg, source, target):
    print("removing branch...")
    # paths = nx.all_simple_paths(sfg, source, target)
    # path = []
    
    # print source and target
    print('source: ', source)
    print('target: ', target)
    sfg.remove_edge(source, target)
    return sfg


def remove_dead_branches(sfg):
    """Remove nodes and branches that only have one connection (i.e., dead branches)."""
    print("Starting to remove dead branches...")

    # List of nodes to remove (nodes with a degree of 1)
    dead_nodes = [node for node, degree in sfg.degree() if degree == 1]
    
    print(f"Dead nodes identified: {dead_nodes}")

    # Remove dead nodes from the graph
    sfg.remove_nodes_from(dead_nodes)
    
    # Now, we also need to ensure that any edges connected to these dead nodes are removed.
    # These edges will automatically be removed when we remove the nodes, 
    # but let's confirm and print out the edges that were removed
    dead_edges = [(u, v) for u, v in sfg.edges if u in dead_nodes or v in dead_nodes]
    
    print(f"Dead edges removed: {dead_edges}")

    # Return the modified graph
    return sfg



# This function will simplify the entire graph 
# Inputs: The Signal Flow Graph 
# Output: A simplified graph where and successful or error message 
def simplify_whole_graph(sfg):
    """
    Simplify the entire graph by iterating over all node pairs and simplifying them.
    Repeated simplifications continue until no further changes can be made.
    
    Parameters:
    sfg (networkx.Graph): The signal-flow graph to be simplified.
    
    Returns:
    networkx.Graph: The simplified graph.
    """
    print("Simplifying entire graph...")

    # Track if any simplification was done
    simplified = False

    # List to store node pairs that need simplification
    simplify_pairs = []

    target_pairs = [("Vvin", "Vvout")]

    # Dictionary to store transmittance for all paths
    path_transmittance = {}

    # Dictionary for Path, Transmittance Source, Target 

    # Substitute numerical values
    numerical_values = {
        'G_M1': 10,  # Gain of M1
        'R_O_M1': 1000,  # Resistance of M1
        'C1': 1e-6,  # Capacitance
        'RD1': 500,  # Resistance RD1
        'G_M2': 20,  # Gain of M2
        'C2': 2e-6,  # Capacitance
        'R_O_M2': 2000,  # Resistance of M2
        'RD2': 1000,  # Resistance RD2
        'R2': 100,  # Resistance R2
        's': 1e3,  # Frequency-domain variable (e.g., for s=jω, substitute a frequency)
        'C3': 1e2,
        'R1': 1e2, 
        'R2': 1e2
    }

    largest_transmittance_list = []

    for source, target in target_pairs:
        if nx.has_path(sfg, source, target):
            # Find all paths between the source and target
            paths = list(nx.all_simple_paths(sfg, source, target))

            # Initialize transmittance for this pair
            path_transmittance[(source, target)] = []

            # Calculate transmittance for each path
            for path in paths:
                symbolic_transmittance = 1  # Start with a multiplier of 1 for symbolic calculation
                for i in range(len(path) - 1):
                    edge = (path[i], path[i + 1])
                    if sfg.has_edge(*edge):
                        weight = sfg.edges[edge].get('weight', 1)  # Default weight is 1 if not specified
                        symbolic_transmittance *= weight  # Multiply edge weights
                    else:
                        print(f"Warning: Edge {edge} not found in the graph!")

                # Substitute numerical values into the symbolic transmittance
                numerical_transmittance = symbolic_transmittance.subs(numerical_values)

                # Store both symbolic and numerical results
                path_transmittance[(source, target)].append(
                    (path, symbolic_transmittance, numerical_transmittance)
                )

            # Print results for the pair
            maxTransmittance = 0
            largest_path = None  

            print(f"Transmittance for paths between {source} and {target}:")
            for path, symbolic, numerical in path_transmittance[(source, target)]:
                print(f"  Path: {path}")
                print(f"    Symbolic Transmittance: {symbolic}")
                print(f"    Numerical Transmittance: {numerical}")
                # Check if this path has the largest transmittance
                if numerical > maxTransmittance:
                    maxTransmittance = numerical
                    largest_path = path  # Update the largest path

            if largest_path is not None:
                largest_transmittance_list.append((source, target, largest_path, maxTransmittance))        

        else:
            print(f"No path found between {source} and {target}")
        print("Largest is: ", largest_transmittance_list)



    #TODO: Check if it is removing the correct paths 
    # Second pass: simplify the paths that are NOT the largest transmittance
    # Iterate over source-target pairs and their corresponding paths
    for (source, target), paths in path_transmittance.items():
        # Identify the largest transmittance path for the current source-target pair
        largest_path = None
        max_transmittance = -float("inf")
        for path, _, numerical in paths:
            if numerical > max_transmittance:
                max_transmittance = numerical
                largest_path = path

        # Simplify all paths except the largest one for this source-target pair
        for path, symbolic, numerical in paths:
            if path == largest_path:
                continue  # Skip the largest transmittance path for this pair

            try:
                # Combine weights for the current path
                combined_weight = 1
                for i in range(len(path) - 1):
                    edge = (path[i], path[i + 1])
                    if sfg.has_edge(*edge):
                        weight = sfg.get_edge_data(*edge)['weight']
                        combined_weight *= weight
                    else:
                        print(f"Error: Edge {edge} not found in the graph!")
                        raise KeyError(edge)

                print(f"Simplifying path: {path} with combined weight: {combined_weight}")

                # Remove intermediate edges, but skip those in the largest path for this pair
                for i in range(len(path) - 1):
                    edge = (path[i], path[i + 1])
                    if edge not in zip(largest_path[:-1], largest_path[1:]):  # Ensure edge is not in the largest path
                        sfg.remove_edge(*edge)

                # Add a direct edge between source and target
                sfg.add_edge(source, target, weight=combined_weight)

                # Remove intermediate nodes, but skip nodes in the largest path for this pair
                for node in path[1:-1]:
                    if node not in largest_path:
                        sfg.remove_node(node)

            except KeyError as e:
                print(f"Error: Missing edge data for {e}")
                continue  # Skip this path if edge data is missing

    # Report the result
    print("Graph simplification complete.")
    return sfg

# simiplification algorithm: takes in source and target nodes and
# simplifies path mathematically; only works by simplifying 1 node in between
def simplify(sfg, source, target):
    print("simplifying...")

    # get shortest path between nodes
    # get all paths and find one with 3 nodes
    paths = nx.all_simple_paths(sfg, source, target)
    path = []
    for p in paths:
        # print path
        if len(p) == 2:
            if sfg.has_edge(source, target) and sfg.has_edge(target, source):
                simplify_loop(sfg, source, target)
                return sfg

        elif len(p) == 3:
            path = p
            break


    # path_nodes = nx.shortest_path(self.graph, source, target)

    # return response: path not found 
    if len(path) != 3:
        return "Path is too short"
    
    #get all connected nodes
    in_edges = sfg.in_edges(path[1])
    connected_nodes = list(sfg.__getitem__(path[1])) + [item[0] for item in in_edges]
    # in_edges = sfg.in_edges(path[1])
    # breakpoint()

    # check for any loops and inward/outward edges
    for node in connected_nodes:
        
        #Check if there is a loop, loop can be with the source or target node as well
        if sfg.has_edge(node, path[1]) and sfg.has_edge(path[1], node):
            if node == source:
                simplify_loop(sfg, node, path[1])
            else:
                simplify_loop(sfg, path[1], node)

        # for the next set of checks, we do not count the source or target
        if node == source or node == target:
            continue
        
        #shift inward edge
        if sfg.has_edge(node, path[1]):
            # edge = sfg.get_edge_data(node, path[1])
            # simplify any loops between nodes
            if sfg.has_edge(node, path[2]) and sfg.has_edge(path[2], node):
                simplify_loop(sfg, path[1], path[2])
            # prev_edge = sfg.get_edge_data(path[1], path[2])
            shiftEdge([node, path[1]], sfg, [path[1], path[2]], False)
        
        #shift outward edge
        else:
            # edge = sfg.get_edge_data(path[1], node)
            if sfg.has_edge(node, path[0]) and sfg.has_edge(path[0], node):
                simplify_loop(sfg, path[0], path[1])
            # prev_edge = sfg.get_edge_data(path[0], path[1])
            shiftEdge([path[1], node], sfg, [path[0], path[1]], True)

    # now simplify adjacent nodes
    weight = sy.simplify(sfg.get_edge_data(path[0], path[1])['weight'] * sfg.get_edge_data(path[1], path[2])['weight'])
    sfg.remove_edge(path[0], path[1])
    sfg.remove_edge(path[1], path[2])
    sfg.add_edge(source, target, weight = weight)
    sfg.remove_node(path[1])
    return sfg

def simplify_loop(sfg, source_node, target_node):
        
    #get edge values
    a = sfg.get_edge_data(source_node, target_node)['weight']
    b = sfg.get_edge_data(target_node, source_node)['weight']

    # calculate edge weight
    c = sy.simplify(a/(1-b*a))

    # remove loop
    sfg.remove_edge(source_node, target_node)
    sfg.remove_edge(target_node, source_node)

    # replace edge
    # check for sign to decide direction of arrow
    # dk if this works bc we're working w symbolic values
    # if c > 0:
    sfg.add_edge(source_node, target_node, weight=c)
    # elif c < 0:
    #     sfg.add_edge(target_node, source_node, weight=abs(c))
    # print("new graph:", sfg.edges)
    

def shiftEdge(edge, sfg, prev_edge, outward):
    #calculate edge weight
    weight = sy.simplify(sfg.get_edge_data(edge[0], edge[1])['weight'] * sfg.get_edge_data(prev_edge[0], prev_edge[1])['weight'])
    #if upward make new node source else target
    if outward:
        sfg.add_edge(prev_edge[0], edge[1], weight = weight)
    else:
        sfg.add_edge(edge[0], prev_edge[1], weight = weight)

    sfg.remove_edge(edge[0], edge[1]) 

def DPI_algorithm( circuit : cir.Circuit ):
    sfg = SFG()
    impedance_list = []
    neighbors = defaultdict(list)

    # for n in circuit.multigraph.nodes:
    #     for ne in circuit.multigraph.neighbors(n):
    #         for k in circuit.multigraph.get_edge_data(n , ne):
    #             print(k)
    for n in circuit.multigraph.nodes:
        if n == "0" or n.lower() == "vcc":
            continue
        impedance = "1/("
        complete = False
        for ne in circuit.multigraph.neighbors(n):
            neighbors[n].append(ne)
            for k in circuit.multigraph.get_edge_data(n , ne):
                if circuit.multigraph.edges[n,ne,k]['component'].name.find("PI") != -1:
                    continue
                if (isinstance(circuit.multigraph.edges[n,ne,k]['component'], cir.CurrentSource)):
                    cur_target = "Isc" + n[1:].lower() if n.startswith("V") else "Isc" + n.lower()
                    cur_source = circuit.multigraph.edges[n,ne,k]['component'].name
                    sfg.graph.add_edge( cur_source , cur_target , weight = "1" )
                if (isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageSource) and ne == "0") or isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentVoltageSource) and ne == "0":
                    
                    impedance = 0
                    complete = True
                elif not complete and not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentCurrentSource) and not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageSource) and not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.CurrentSource):
                    impedance += " + " + ("(s*"+circuit.multigraph.edges[n,ne,k]['component'].name +")" if isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.Capacitor) else "1/" + circuit.multigraph.edges[n,ne,k]['component'].name)
                if (ne != "0" and ne.lower() != "vcc") or isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentVoltageSource) or isinstance( circuit.multigraph.edges[n,ne,k]['component'], cir.VoltageDependentCurrentSource ):
                    # REFACTOR POS_NODE AND NEG_NODE TO BE i_in_node AND i_out_node
                    if not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentCurrentSource) and not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageSource) and not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.CurrentSource) and not isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentVoltageSource):
                        
                        cur_target = "Isc" + ne[1:].lower() if ne.startswith("V") else "Isc" + ne.lower()
                        cur_source = "V" + n.lower() if not n.startswith("V") else n
                        if circuit.multigraph.edges[n,ne,k]['component'].name !="C1":
                            if sfg.graph.has_edge(cur_source, cur_target):
                                sfg.graph.edges[cur_source , cur_target]['weight'] += " + " + ("(s*"+circuit.multigraph.edges[n,ne,k]['component'].name +")" if isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.Capacitor) else "1/" + circuit.multigraph.edges[n,ne,k]['component'].name)
                            else:
                                sfg.graph.add_edge(cur_source , cur_target , weight = "+" + ("(s*"+circuit.multigraph.edges[n,ne,k]['component'].name +")" if isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.Capacitor) else "1/" + circuit.multigraph.edges[n,ne,k]['component'].name))
                        else:
                            if sfg.graph.has_edge(cur_source, cur_target):
                                sfg.graph.edges[cur_source , cur_target]['weight'] += " + 1 " 
                            else:
                                sfg.graph.add_edge(cur_source , cur_target , weight = "+ 1 " )
                    elif isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentCurrentSource):
                        """
                        currently, only works for grounded transistor -> doesn't consider the other direction
                        sol:
                            - check if one terminal of transistor (VDCS) is grounded
                            - if yes:
                                    only need one instance of the vdcs
                                    ex: gm * vd 
                            - if no:
                                    need a two instances, one for each end
                                    ex: gm * vds => gm * vd and -gm * vs (in opposite direction

                           n -> Vs1
                        g = VoltageDependentCurrentSource(
                            f'G_{self.name}',
                            self.source,
                            self.drain,
                            self.gate,
                            self.source,
                            g_m
                        )
                    class VoltageDependentVoltageSource(Component, TwoTerminal):
                        _prefix = 'e'
                        def __init__(self, name: str,
                                    pos_node: str,
                                    neg_node: str,
                                    pos_input_node: str,
                                    neg_input_node: str,
                                    gain: Union[str, float]):
""" 
            
                        # pass A
                        cur_target = "Isc" + n[1:].lower() if n.startswith("V") else "Isc" + n.lower() 
                        pos_input_node = circuit.multigraph.edges[n,ne,k]['component'].pos_input_node
                        neg_input_node = circuit.multigraph.edges[n,ne,k]['component'].neg_input_node
                        cur_source_1 = "V" + pos_input_node.lower() if not pos_input_node.startswith("V") else pos_input_node
                        if sfg.graph.has_edge(cur_source_1, cur_target):
                            sfg.graph.edges[cur_source_1, cur_target]['weight'] += (" - " if n == circuit.multigraph.edges[n,ne,k]['component'].neg_node else " + ") +  str(circuit.multigraph.edges[n,ne,k]['component'].name)
                        else:
                            sfg.graph.add_edge( cur_source_1, cur_target , weight = (" - " if n == circuit.multigraph.edges[n,ne,k]['component'].neg_node else " + ")  + str(circuit.multigraph.edges[n,ne,k]['component'].name))

                        # try adding edge from neg_input node to cur_target -> swapping positive node and negative to get the second pass
                        # pass B   
                        cur_source_2 =    "V" + neg_input_node.lower() if not neg_input_node.startswith("V") else neg_input_node
                        if sfg.graph.has_edge(cur_source_2, cur_target):
                            sfg.graph.edges[cur_source_2, cur_target]['weight'] += (" - " if n == circuit.multigraph.edges[n,ne,k]['component'].pos_node else " + ") +  str(circuit.multigraph.edges[n,ne,k]['component'].name)
                        else:
                            sfg.graph.add_edge( cur_source_2, cur_target , weight = (" - " if n == circuit.multigraph.edges[n,ne,k]['component'].pos_node else " + ")  + str(circuit.multigraph.edges[n,ne,k]['component'].name))

                        
                    elif isinstance(circuit.multigraph.edges[n,ne,k]['component'] , cir.VoltageDependentVoltageSource):
                        cur_target = "V" + n[1:].lower() if n.startswith("V") else "V" + n.lower()
                        pos_input_node = circuit.multigraph.edges[n,ne,k]['component'].pos_input_node
                        neg_input_node = circuit.multigraph.edges[n,ne,k]['component'].neg_input_node
                        
                        if pos_input_node != "0":
                            cur_source_1 = "V" + pos_input_node.lower() if not pos_input_node.startswith("V") else pos_input_node
                            if sfg.graph.has_edge(cur_source_1, cur_target):
                                sfg.graph.edges[cur_source_1, cur_target]['weight'] += (" + " if n == circuit.multigraph.edges[n,ne,k]['component'].pos_node else " - ") +  str(circuit.multigraph.edges[n,ne,k]['component'].name)
                            else:
                                sfg.graph.add_edge( cur_source_1, cur_target , weight = (" + " if n == circuit.multigraph.edges[n,ne,k]['component'].pos_node else " - ") +  str(circuit.multigraph.edges[n,ne,k]['component'].name))
                        if neg_input_node != "0":
                            cur_source_2 = "V" + neg_input_node.lower() if not neg_input_node.startswith("V") else neg_input_node
                            if sfg.graph.has_edge(cur_source_2, cur_target):
                                sfg.graph.edges[cur_source_2, cur_target]['weight'] += ((" - " if n == circuit.multigraph.edges[n,ne,k]['component'].pos_node else " + ") +  str(circuit.multigraph.edges[n,ne,k]['component'].name))
                            else:
                                sfg.graph.add_edge( cur_source_2, cur_target , weight = (" - " if n == circuit.multigraph.edges[n,ne,k]['component'].pos_node else " + ") +  str(circuit.multigraph.edges[n,ne,k]['component'].name))


        if impedance == 0:
            continue
        if impedance != "1/(":
            impedance += ")"
        else:
            impedance = "1"
        #print(impedance)
        impedance_list.append(impedance)
        source = "Isc" + n[1:].lower() if n.startswith("V") else "Isc" + n.lower()
        target = "V" + n.lower() if not n.startswith("V") else n
        sfg.graph.add_edge(  source , target , weight = impedance )         
        
    for e in sfg.graph.edges:
        split_ = sfg.graph.get_edge_data(*e)['weight'].split(" ")
        if len(split_) > 2 and split_[2].startswith("E"):
            sfg.graph.get_edge_data(*e)['weight'] = sy.sympify( sfg.graph.get_edge_data(*e)['weight'] , locals = {split_[2]: sy.Symbol(split_[2])})
        else:
            sfg.graph.get_edge_data(*e)['weight'] = sy.sympify( sfg.graph.get_edge_data(*e)['weight'] )
    # for e in sfg.graph.edges:
    #     print("weight information:",sfg.graph.get_edge_data(*e))
    # print("nodes:")
    # for n in sfg.graph.nodes:
    #     print(n)
    
    # reorder edges to have sources in the beginning of list
    ordered_edges = []
    for e in sfg.graph.edges:
        source = e[0]
        target = e[1]
        ordered_edges.append((source, target, sfg.graph.get_edge_data(*e).get('weight')))

    input_nodes = []
    other_nodes = []
    output_nodes = []
    for n in sfg.graph.nodes:
        if n.endswith("s") or n.endswith("g") or n.endswith("in") or n.endswith("i"):
            input_nodes.append(n)
        elif n.endswith("o") or n.endswith("out"):
            output_nodes.append(n)
        else:
            other_nodes.append(n)
    ordered_nodes = input_nodes + other_nodes + output_nodes
    
    sfg.graph.clear()

    for on in ordered_nodes:
        sfg.graph.add_node(on)
    
    for oe in ordered_edges:
        sfg.graph.add_edge(oe[0], oe[1], weight = oe[2])

    # for e in sfg.graph.edges:
    #     print("edge:(source , target)",e)
    #     print("weight information:",sfg.graph.get_edge_data(*e))
    #     print("\n")
    # print("nodes:")
    # for n in sfg.graph.nodes:
    #     print(n)

    # print('PATHS')
    # breakpoint()
    # print(nx.shortest_path(sfg.graph,'I_in', 'Vout'))
    # print(nx.shortest_path(sfg.graph,'Iscin', 'Vout'))
    # print(nx.shortest_path(sfg.graph,'Vin', 'Vout'))
    #breakpoint()
    
    return sfg




class SFGraph(object):
    
    def __init__(self , nodes_list):
        self.nodes_list = nodes_list
        self.short_circuit_nodes = {}
        self.edge_list = []
        self.adjacency = defaultdict(list)
        self.nodes_name_map = {}
        self.vertex = []
        
        
        
        pass
    
    def add_edge(self , source , target , weight):
        print("in add edge")
        #print(type(source))
        source_node = Node( node_name = str(source) , is_ground = False )
        target_node = Node( node_name = str(target) , is_ground = False )
        self.edge_list.append( Edge( source_node.node_name , target_node.node_name , weight ) )
        if target_node.node_name not in self.nodes_name_map:
            #if str(target) not in self.nodes_name_map:
                #flag = True
            
            self.nodes_name_map.update( { target_node.node_name : target_node } )
            self.nodes_name_map[target_node.node_name].node_number = target
            #if flag:
            self.vertex.append(self.nodes_name_map[target_node.node_name])
        
        
        if source_node.node_name not in self.nodes_name_map:
            
            self.nodes_name_map.update( { source_node.node_name : source_node } )
            self.nodes_name_map[ source_node.node_name ].node_number = source
            self.vertex.append(self.nodes_name_map[ source_node.node_name ])
            
        self.nodes_name_map[source_node.node_name].adj_nodes.append(self.nodes_name_map[ target_node.node_name ])
            
                
        
        self.vertex.sort(reverse = False , key = lambda x : x.node_number)
    
    def generate_adjacent(self):
        
       
        self.nodes_name_map.update(self.nodes_list)
        self.nodes_name_map.update(self.short_circuit_nodes)
        index = 0
        self.nodes_name_map.pop("V0")
        for k in self.nodes_name_map.keys():
            self.nodes_name_map[k].node_number = index
            self.vertex.append(self.nodes_name_map[k])
            index += 1
            
        #print(self.vertex)
        
        #self.graph_nodes.pop("0")
        for edge in self.edge_list:
            if self.nodes_name_map[edge.target].node_number not in self.adjacency[self.nodes_name_map[edge.source].node_number]:
                self.adjacency[self.nodes_name_map[edge.source].node_number].append(self.nodes_name_map[edge.target].node_number)
        for i in range(len(self.vertex)):
            for v_number in self.adjacency[self.vertex[i].node_number]:
                self.vertex[i].adj_nodes.append( self.vertex[ v_number ] )
            #print("vertex: " + str(self.vertex[i].node_number))
            #print(self.vertex[i].adj_nodes)
        
        
    def arrange_attr(self):
        # this part depends on the parser output
        pass
    def generate(self):
        
        for k , v in self.nodes_list.items():
            if v.voltage != 0:
                name = "Isc" + k[1:]
                self.short_circuit_nodes[name] = Node(node_name = name , is_ground = False )
                self.edge_list.append(Edge(source = name , target = k , weight = v.DPImpedence))
                current_list = v.short_circuit_I.split(" + ")
                if len(current_list) != 0 and current_list[0] == "":
                    current_list = current_list[1:]
                for i in range(len(current_list)):
                    if not current_list[i].startswith("V"):
                        control_current = current_list[i].split("*")
                        gain = control_current[0]
                        control_current[1] = control_current[1].split("-")
                        node1 , node2 = control_current[1][0] , control_current[1][1]
                        while not node2[-1].isalpha():
                            node2 = node2[:-1]
                        while not node1[0].isalpha():
                            node1 = node1[1:]
                        while gain.startswith(" "):
                            gain = gain[1:]
                        nega_gain = ( gain[1:] if gain.startswith("-") else "-" + gain)
                        
                        
                        self.edge_list.append(Edge(source = node1 , target = name , weight = gain))
                        self.edge_list.append(Edge(source = node2 , target = name , weight = nega_gain))
                    else:
                        from_node, index = "", 0
                        while current_list[i][index] != "/":
                            from_node += current_list[i][index]
                            index += 1
                        gain = "1" + current_list[i][index:]
                        self.edge_list.append(Edge(source = from_node , target = name , weight = gain))
                        
        print(self.short_circuit_nodes)
        for ele in self.edge_list:
            print(ele)
        pass
            
    def process_nodeList(self):
        for key , each_node in self.nodes_list.items():
            each_node.DPI_analysis()
        pass
    def __repr__(self):
        #result = []
        #for each_node in self.nodes_list:
            #result.append(each_node.__repr__())
        #return '\n'.join(result)
        result = []
        for e in self.edge_list:
            result.append(e.__repr__())
        return "graph edges: \n" + '\n'.join(result)
    #def __getattr__( self, name ):
     #   return getattr(self.nodes_list , name)
    
class Edge:
    def __init__(self, source , target , weight):
        self.source = source
        self.target = target
        self.weight = weight
    def __repr__(self):
        return f"{self.source}->{self.target} : {self.weight}"


class Node:
    def __init__(self, **kwargs):
        # name of this node
        self.components = {}
        self.adj_nodes = []
        self.node_number = 0
        self.voltage = 0 if kwargs["is_ground"] is True else "V" + kwargs["node_name"].lower() if not kwargs["node_name"].startswith("V") else kwargs["node_name"]
        self.short_circuit_I = "0"
        self.DPImpedence = "0"
        self.node_name =  "V" + kwargs["node_name"].lower() if not kwargs["node_name"].startswith("V") and not kwargs["node_name"].startswith("I") else kwargs["node_name"]
        if self.voltage == 0:
            return
        
        
        
        # components is a dictionary stores the information between this node and each of its neighbors. We can access the components between node 1 and node 2 using components["node2"] and returns a list of component objects in between
        if "components" in kwargs:
            self.components = kwargs["components"]
        
   
        
    
    def add_components(self, input_list):
        self.components.update(input_list)
    
    def __repr__(self):
        if self.voltage == 0:
            return "ground"
        return " NodeInfor: node_id " + str(self.node_number) + " node_name " + self.node_name #+" voltage: " + self.voltage + "\n short circuit current: "+ self.short_circuit_I + "\n  driving point impedence:" + self.DPImpedence
    
    def in_parallel(self, r1 , r2):
        return 1 / ( 1/r1 + 1/r2 )


    #this is a sketch of structure of what the algorithm will look like
    def DPI_analysis(self):
        #compute impedence of this node
        if self.voltage == 0:
            return
        impedence = ""
        for component, node in self.components.items():
            if not isinstance(component , VoltageSource) and not isinstance(component , CurrentSource):
                impedence +=  ( ( ("(1/s" + component.name + ")") if isinstance( component , Capacitor) else component.name) + "//")
                
        impedence = impedence[:-2]
        # dpi * short_circuit crruent
        # compute the current flow in or out on each branch connected to this node
            # need further polish
        current_Isc = ""
        for component , node in self.components.items():
            
                # if they are connected by a current source it is complicated.
            if isinstance( component , CurrentSource):
                current_Isc += ( component.direction )
                current_Isc += ( component.current )
                # if they are connected by resistors simply add 1/R to the current list
            elif node.voltage != 0:
                print("node.voltage:")
                print(node.voltage)
                current_Isc += ( " + " + node.voltage + '/' + component.name + " " )
        #current_Isc = current_Isc[:-1]
        if current_Isc == "":
            current_Isc = "0"
        if impedence == "":
            impedence = "0"
        #print("here")
        self.short_circuit_I = current_Isc
        self.DPImpedence = impedence

def construct_graph( circuit : cir.Circuit ):
    circuit_components = {}
    circuit_nodes = {}
    graph = SFGraph(dict())
    for node , neighbors in circuit.multigraph.adjacency():
        if node not in circuit_nodes:
            ground = True if node == "0" else False
            node_name =  "V" + node.lower() if not node.startswith("V") else node
            circuit_nodes[ node ] = Node( node_name = node, is_ground = ground )
            graph.nodes_list.update( {node_name: circuit_nodes[ node ]} )
            
    print(circuit_nodes)
    for edge in circuit.multigraph.edges(keys=True, data='component'):
        src_node, dst_node, component_name, component_object = edge
        if isinstance(component_object, cir.Resistor):
            cur_resistor = Resistor( name = component_name, value = component_object.value )
            circuit_components[component_name] = cur_resistor
        elif isinstance(component_object, cir.VoltageSource):
            cur_v = VoltageSource( name = component_name, voltage = component_object.voltage )
            circuit_components[component_name] = cur_v
        elif isinstance(component_object, cir.VoltageDependentCurrentSource):
            c = "" + component_object.gain + "*(" + component_object.pos_input_node + "-" + component_object.neg_input_node+") "
            cur_i = CurrentSource( name = component_name, current = c , direc = "+ " )
            cur_o = CurrentSource( name = component_name, current = c , direc = "- " )
            positive_node = src_node if component_object.neg_input_node == src_node else dst_node
            negative_node = src_node if component_object.pos_input_node == src_node else dst_node
            circuit_nodes[positive_node].add_components({cur_i : circuit_nodes[negative_node]})
            circuit_nodes[negative_node].add_components({cur_o : circuit_nodes[positive_node]})
            continue
        elif isinstance(component_object, cir.Capacitor):
            circuit_components[component_name] = Capacitor( name = component_name , capacitance = component_object.capacitance )
        
        circuit_nodes[src_node].add_components({circuit_components[component_name] : circuit_nodes[dst_node]})
        circuit_nodes[dst_node].add_components({circuit_components[component_name] : circuit_nodes[src_node]})
    graph.process_nodeList()
    graph.generate()
    graph.generate_adjacent()
    return graph
                

    
    
    
