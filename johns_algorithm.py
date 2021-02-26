from dpi import *
from copy import *


class Strongly_connected_components:

    def DFS_scc(self, vertex, visited, stack):
        # print("in DFS", vertex)
        visited.add(vertex)
        for v in vertex.adj_nodes:
            # print("neighbor:" , v)
            # print(v in visited)
            if v in visited:
                continue
            self.DFS_scc(v, visited, stack)
        # print("finishing vertex:" , vertex)
        stack.append(vertex)

    def reverse_graph(self, graph):
        reversed_graph = SFGraph(dict())

        for edge in graph.edge_list:
            reversed_graph.add_edge(graph.nodes_name_map[edge.target].node_number,
                                    graph.nodes_name_map[edge.target].node_number, edge.weight)

        return reversed_graph

    def DFS_scc_reverse(self, vertex, visited, vertex_set):
        visited.add(vertex)
        vertex_set.add(vertex)
        for v in vertex.adj_nodes:
            if v in visited:
                continue
            self.DFS_scc_reverse(v, visited, vertex_set)

    def scc(self, graph):

        # print("in scc")
        # for v in graph.vertex:
        # print(type(v.node_number))
        stack = []
        visited = set()
        for i in range(len(graph.vertex)):
            if graph.vertex[i] in visited:
                continue
            self.DFS_scc(graph.vertex[i], visited, stack)
        # print("visited:",visited)
        # reversed_graph = copy(graph)
        # print("before reverse:", graph)
        reversed_graph = self.reverse_graph(graph)
        # print("after reverse:", graph)

        visited.clear()
        result = []
        # print("visited:",visited)
        # print("stack:",stack)
        while (len(stack)):
            vertex = stack.pop()
            if vertex in visited:
                continue
            cur_scc_set = set()
            self.DFS_scc_reverse(vertex, visited, cur_scc_set)
            result.append(cur_scc_set)

        return result


class Cycle_finding:
    def __init__(self):
        # print("in finding init")
        self.blocked_set = set()
        self.blocked_map = defaultdict(set)
        self.stack = list()
        self.all_cycles = list()
        pass

    def create_subgraph(self, start_index, graph):
        subgraph = SFGraph(dict())
        # print(graph.edge_list)

        for edge in graph.edge_list:
            # print(type(edge.source), type(start_index))
            if graph.nodes_name_map[edge.source].node_number >= start_index and graph.nodes_name_map[
                edge.target].node_number >= start_index:
                subgraph.add_edge(graph.nodes_name_map[edge.source].node_number,
                                  graph.nodes_name_map[edge.target].node_number, edge.weight)
        return subgraph

    def get_least_index_scc(self, sccs, subgraph):
        import sys
        min_index = sys.maxsize
        min_vertex = None
        min_scc = None
        for scc in sccs:
            if len(scc) == 1:
                continue
            for v in scc:
                if v.node_number < min_index:
                    min_index, min_vertex, min_scc = v.node_number, v, scc
        # print("min_index: ", min_index, "min_scc: ", min_scc)
        if min_scc is None:
            return -1, min_vertex

        graph_scc = SFGraph(dict())
        new_scc = set()
        for v in min_scc:
            new_scc.add(subgraph.nodes_name_map[v.node_name])
        min_scc = new_scc
        for edge in subgraph.edge_list:
            # print("in loop sub: ",subgraph.nodes_name_map[edge.source] , subgraph.nodes_name_map[edge.target], min_scc)
            # print(subgraph.nodes_name_map[edge.source] in min_scc and subgraph.nodes_name_map[edge.target] in min_scc)
            # print(type(min_scc))
            if subgraph.nodes_name_map[edge.source] in min_scc and subgraph.nodes_name_map[edge.target] in min_scc:
                graph_scc.add_edge(edge.source, edge.target, edge.weight)

        # print("scc graph: ", graph_scc)
        # print(min_vertex.node_name , graph_scc.nodes_name_map)
        # print(min_vertex.node_name not in graph_scc.nodes_name_map)
        # print("min_index: ", min_index, "min_scc: ", min_scc)
        if min_vertex.node_name not in graph_scc.nodes_name_map:
            return -1, min_vertex
        return min_index, min_vertex

    def unblock(self, vertex):
        # print("in  unblock: unblocking ", vertex)
        # print(self.blocked_set)
        # print("unblock map for current node:")
        # print(self.blocked_map[vertex])
        if vertex not in self.blocked_set:
            return
        self.blocked_set.remove(vertex)
        if len(self.blocked_map[vertex]) > 0:
            for v in self.blocked_map[vertex]:
                self.unblock(v)
            del self.blocked_map[vertex]

    def find_cycles_in_scc(self, start_vertex, current_vertex):
        self.stack.append(current_vertex)
        self.blocked_set.add(current_vertex)
        found_cycle = False
        got_cycle = False
        # print("at the beginning of algorithm, current_vertex: ",current_vertex)
        for neighbor in current_vertex.adj_nodes:
            if neighbor is start_vertex:
                self.stack.append(start_vertex)
                cycle = copy(self.stack)
                cycle.reverse()
                self.stack.pop()
                self.all_cycles.append(cycle)
                # print("find cycle")
                found_cycle = True
            elif neighbor not in self.blocked_set:
                got_cycle = self.find_cycles_in_scc(start_vertex, neighbor)
                found_cycle = (found_cycle or got_cycle)

        if found_cycle:
            self.unblock(current_vertex)
        else:
            for neighbor in current_vertex.adj_nodes:
                self.blocked_map[neighbor].add(current_vertex)

        self.stack.pop()
        return found_cycle

    def simple_cycles(self, graph):
        start_index = 0
        SCC = Strongly_connected_components()
        # print("algorithm begins",len(graph.vertex))
        while start_index <= len(graph.vertex):
            # print("in loop , start index",start_index)
            subGraph = self.create_subgraph(start_index, graph)
            sccs = SCC.scc(subGraph)
            # print("sccs: ", sccs)
            # print("subgraph:" , subGraph)
            maybe_least_index = self.get_least_index_scc(sccs, subGraph)
            # print("least index: ", maybe_least_index)
            if maybe_least_index[0] >= start_index:
                least_vertex = maybe_least_index[1]
                self.blocked_map.clear()
                self.blocked_set.clear()
                self.find_cycles_in_scc(least_vertex, least_vertex)
                start_index = least_vertex.node_number + 1
            else:
                break
        return self.all_cycles





