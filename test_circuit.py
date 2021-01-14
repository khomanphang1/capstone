import unittest
import os
from circuit import Circuit


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


def iter_netlist(path):
    with open(path, 'r', encoding='utf-8') as f:
        yield from (line.rstrip() for line in f)


class TestCircuit(unittest.TestCase):
    def test_2N3904_common_emitter(self):
        netlist_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.net')
        with open(netlist_path, 'r') as f:
            netlist = f.read()

        op_log_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.log')
        with open(op_log_path, 'r') as f:
            op_log = f.read()

        small_signal_netlist_path = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter_small_signal.net')
        expected_netlist = sorted(iter_netlist(small_signal_netlist_path))

        circuit = Circuit.from_ltspice(netlist, op_log)
        actual_netlist = sorted(c.to_netlist_entry() for _, _, c in circuit.iter_components())

        self.assertEqual(expected_netlist, actual_netlist)

    def test_2N3904_cascode(self):
        netlist_path = os.path.join(TEST_DATA_DIR, '2N3904_cascode.net')
        with open(netlist_path, 'r') as f:
            netlist = f.read()

        op_log_path = os.path.join(TEST_DATA_DIR, '2N3904_cascode.log')
        with open(op_log_path, 'r') as f:
            op_log = f.read()

        small_signal_netlist_path = os.path.join(TEST_DATA_DIR, '2N3904_cascode_small_signal.net')
        expected_netlist = sorted(iter_netlist(small_signal_netlist_path))

        circuit = Circuit.from_ltspice(netlist, op_log)
        actual_netlist = sorted(c.to_netlist_entry() for _, _, c in circuit.iter_components())

        self.assertEqual(expected_netlist, actual_netlist)


if __name__ == '__main__':
    unittest.main(verbosity=2)
