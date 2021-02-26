from dpi import *
import circuit
import json
import johns_algorithm as ja
import time
import mason


def convert_to_JSON(graph):
    preprocess = {}
    for key, value in graph.nodes_list.items():
        print(value.node_name)
        preprocess.update({key: {"id": value.node_name, "name": value.node_name, "value": ""}})
    edge_process = {}
    index = 0
    for i in range(len(graph.edge_list)):
        edge_process.update({i: {"src": graph.edge_list[i].source, "dst": graph.edge_list[i].target,
                                 "weight": graph.edge_list[i].weight}})

    with open("result_circuit.json", "w") as outfile:
        json.dump(preprocess, outfile)
    with open("result_edge_list.json", "w") as outfile:
        json.dump(edge_process, outfile)


def run_test1():
    print("test case 1:")
    r0 = Resistor("r0", 10)
    print(r0)
    # ground node
    ground = Node(node_name="0", is_ground=True)
    print(ground)
    ground.DPI_analysis()
    # control source
    Cgs_in = CurrentSource("c0", "gmVgs", "+")
    Cgs_out = CurrentSource("c0", "gmVgs", "-")
    print(Cgs_in)
    print(Cgs_out)
    # rd
    Rd = Resistor("Rd", 20)
    print(Rd)
    # rs
    Rs = Resistor("Rs", 20)
    print(Rs)
    # input voltage source
    Vi = VoltageSource("Vi", 10)

    Nd = Node(node_name="Nd", components={Rd: ground, r0: None, Cgs_out: None}, neighbors=[ground], is_ground=False)
    Ns = Node(node_name="Ns", components={Rs: ground, r0: Nd, Cgs_in: Nd}, neighbors=[ground, Nd], is_ground=False)
    Nd.components[r0], Nd.components[Cgs_out] = Ns, Ns
    # Nd.neighbors.append(Ns)
    Ng = Node(node_name="Ng", components={Vi: ground}, neighbors=[ground], is_ground=False)

    graph = SFGraph({"Nd": Nd, "Ns": Ns, "Ng": Ng})
    graph.process_nodeList()
    print(graph)


def run_test2():
    print("test case 2:")
    Rd1 = Resistor("Rd1", 10)
    Cgs1_in = CurrentSource("c0", "gm1Vgs1", "+")
    Cgs1_out = CurrentSource("c0", "gm1Vgs1", "-")
    Vi = VoltageSource("Vi", 10)
    R1 = Resistor("R1", 10)
    R2 = Resistor("R2", 10)
    Rd2 = Resistor("Rd2", 10)
    Cgs2_out = CurrentSource("c1", "gm2Vd1", "-")
    ground = Node(node_name="0", is_ground=True)
    Ng = Node(node_name="Ng", components={Vi: ground}, neighbors=[ground], is_ground=False)
    Nd1 = Node(node_name="Nd1", components={Cgs1_out: None, Rd1: ground}, is_ground=False)
    Ns1 = Node(node_name="Ns1", components={Cgs1_in: Nd1, R1: ground, R2: None}, is_ground=False)
    Nd2 = Node(node_name="Nd2", components={Cgs2_out: ground, Rd2: ground, R2: Ns1}, is_ground=False)
    Nd1.components[Cgs1_out] = Ns1
    # Nd1.neighbors.append(Ns1)
    Ns1.components[R2] = Nd2
    # Ns1.neighbors.append(Nd2)

    graph = SFGraph({"Ng": Ng, "Nd1": Nd1, "Ns1": Ns1, "Nd2": Nd2})
    graph.process_nodeList()
    print(graph)


def test3():
    from os import path
    print("here")
    test_data_dir = path.join(path.dirname(__file__), 'test_data')

    netlist_file = path.join(test_data_dir, 'npn_ce.cir')
    log_file = path.join(test_data_dir, 'npn_ce.log')
    c_in = circuit.Circuit.from_ltspice(netlist_file, log_file)
    graph = construct_graph(c_in)
    print(graph.nodes_list)
    print("nodes:")
    for k, v in graph.nodes_list.items():
        print(k)
        print(v.components)
        print(v.voltage)
        print("=================")

    print("after dpi:")
    for k, v in graph.nodes_list.items():
        print(k + ":")
        print("short circuit current: " + v.short_circuit_I)
        print("DPImpedence: " + v.DPImpedence)
    # graph.generate()
    print("edge list:")
    print(graph.edge_list)
    print("voltage node list:")
    print(graph.nodes_list)
    print("short circuit node list:")
    print(graph.short_circuit_nodes)
    # graph.generate_adjacent()
    print(graph.adjacency)
    node = Node(node_name="shit", is_ground=False)
    print(node)
    convert_to_JSON(graph)

    SCC = ja.Strongly_connected_components()
    r_graph = SCC.reverse_graph(graph)

    print(r_graph)
    print(r_graph.vertex)

    print("graph node name map:")
    print(graph.nodes_name_map)
    print("graph vertex")
    print(graph.vertex)
    for v in graph.vertex:
        print(graph.nodes_name_map[v.node_name])

    result = SCC.scc(graph)
    print("result of strongly connected components:")
    print(result)

    start_time = time.time()
    John = ja.Cycle_finding()
    result_c = John.simple_cycles(graph)
    print("all cycles : ", result_c)
    end_time = time.time()
    print("time elipse: ", end_time - start_time)


def test_john():
    graph = SFGraph(dict())
    graph.add_edge(0, 1, 1)
    graph.add_edge(1, 2, 1)
    graph.add_edge(2, 0, 1)
    graph.add_edge(1, 3, 1)
    graph.add_edge(3, 4, 1)
    graph.add_edge(4, 5, 1)
    graph.add_edge(5, 3, 1)
    graph.add_edge(5, 6, 1)
    print(graph.nodes_name_map)
    print(graph.vertex)
    # SCC = ja.Strongly_connected_components()
    # result = SCC.scc(graph)
    # print()
    # print(result)
    # print(len(result))
    start_time = time.time()
    John = ja.Cycle_finding()
    result_c = John.simple_cycles(graph)
    print("all cycles : ", result_c)
    end_time = time.time()
    print("time elipse: ", end_time - start_time)
    # print(graph.nodes_name_map.values())
    # print(graph.vertex[0] in graph.nodes_name_map.values())
    # print(graph.vertex[0] is graph.nodes_name_map[graph.vertex[0].node_name])
    # print(len(graph.vertex))


def test4():
    from os import path
    test_data_dir = path.join(path.dirname(__file__), 'test_data')

    netlist_file = path.join(test_data_dir, 'npn_ce.cir')
    log_file = path.join(test_data_dir, 'npn_ce.log')
    with open(netlist_file) as f:
        netlist = f.read()

    with open(log_file) as f:
        log = f.read()
    c_in = circuit.Circuit.from_ltspice(netlist, log)
    for n in c_in.multigraph.nodes:
        print("node:")
        print(n)
        print("neighbors:")
        for ne in c_in.multigraph.neighbors(n):
            print("neighbor_node")
            print(ne)
            print("edges:")
            for k in c_in.multigraph.get_edge_data(n, ne):
                print(k)
                print(c_in.multigraph.edges[n, ne, k])
                print(c_in.multigraph.edges[n, ne, k]["component"].name)
                if isinstance(c_in.multigraph.edges[n, ne, k]["component"], circuit.VoltageDependentCurrentSource):
                    print("type of pos node")
                    print(type(c_in.multigraph.edges[n, ne, k]["component"].pos_node))
    for edge in c_in.multigraph.edges(data="component"):
        print(edge)
    sfg = DPI_algorithm(c_in)
    h = mason.transfer_function(sfg.graph, 'Vn001', 'Vn002')
    mason.sp.pprint(h.factor(), use_unicode=True)

    # print(h)
    # source, target , weight_name , component = edge
    # print(source , target , weight_name , component)
    # print(edge.weight)
    # print(e.component_object)


if __name__ == "__main__":
    test4()
    # test3()
    # run_test1()
    # run_test2()
    # test_john()



