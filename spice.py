import re
from dataclasses import dataclass
from typing import List

'''
circ = Circuit(netlist)

circ = circ.small_signal_model()
circ.to_small_signal_model()

for node in circ.iter_nodes():
    for elem in node.iter_branches():
        if isinstance(elem, Transistor):
            elem.small_signal()
                        
        elif isinstance(elem, Voltage) or \ 
             isinstance(elem, Current) and \ 
             elem.is_dc():
            elem.zero()

'''


transistor_type = re.compile(r'^\s*--- ([A-Za-z]+) Transistors ---\s*$')


@dataclass()
class Bipolar:
    name: str
    g_m: str = None
    r_pi: str = None
    r_o: str = None

    def small_signal_model(self, collector: str, base: str, emitter: str) -> List[str]:
        return [
            f'rpi_{self.name} {base} {emitter} {self.r_pi}',
            f'ro_{self.name} {collector} {emitter} {self.r_o}',
            f'g_{self.name} {collector} {emitter} {base} {emitter} {self.g_m}'
        ]


def replace_transistors(netlist: List[str], transistors: List[Bipolar]):
    out = []
    replace_nodes = {}

    for branch in netlist:
        if branch[0].lower() == 'q':
            name = re.match(r'\S+', branch).group(0).lower()
            transistor = next((t for t in transistors if t.name.lower() == name), None)

            if not transistor: # No matching transistor found
                raise ValueError

            out.extend(transistor.small_signal_model(*branch.split(' ')[1:4]))

        elif branch[0].lower() == 'v':
            value = branch.split(' ', 3)[-1]
            if '(' in value:
                out.append(branch)
                continue
            else: # DC source


                # DC Voltage Source -> Short Circuit
                # Suppose Vx connected to N0 and N1
                # If one of N0 or N1 is GND, keep that node
                # Otherwise, keep lower numbered node
                # Then, convert all occurences of the other node to the kept node
                # Remove branch

                # This likely won't work if the same node is short circuited
                # with two different nodes! Need a more sophisicated algo

                nodes = branch.split(' ', 3)[1:3]
                keep = next((n for n in nodes if n == '0'), min(nodes))
                replace = next((n for n in nodes if n != keep), None)
                if replace:
                    replace_nodes[replace] = keep
                pass

        else:
            out.append(branch)

    for i in range(len(out)):
        for n in replace_nodes:
            out[i] = ' '.join(replace_nodes.get(x, x) for x in out[i].split(' '))

    netlist[:] = out


def extract_transistor_params(op_log: str) -> str:
    lines = iter(op_log.split('\n'))
    transistors = []
    params = {'Gm': 'g_m', 'Rpi': 'r_pi', 'Ro': 'r_o'}

    for line in lines:
        match = transistor_type.match(line)
        if match:
            type = match.group(1)
            assert type == 'Bipolar'

            # Construct transistor instances
            line = re.split('\s+', next(lines))
            assert line[0] == 'Name:'
            transistors.extend(Bipolar(name=name) for name in line[1:])

            # Extract small signal parameters
            while True:
                line = next(lines)
                if not line:
                    break

                line = re.split(r'\s+', line)
                attrib = params.get(line[0][:-1], None)
                if attrib:
                    for i, transistor in enumerate(transistors):
                        setattr(transistor, attrib, line[i + 1])

            # For now handle only one transistor type
            break

    return transistors


def small_signal_netlist(netlist: str, op_log: str) -> str:
    transistors = extract_transistor_params(op_log)
    netlist = [line for line in netlist.split('\n') if line[0] not in '.*']

    replace_transistors(netlist, transistors)
    for line in netlist: print(line)
    return '\n'.join(netlist)