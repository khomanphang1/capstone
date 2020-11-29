import unittest
import os

import spice

TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

"""
Test is currently outdated, will be updated soon

"""

class TestSmallSignal(unittest.TestCase):
    def test_npn_ce(self):
        with open(os.path.join(TEST_DIR, 'npn_ce.cir'), encoding='utf-8') as file:
            netlist = file.read()

        with open(os.path.join(TEST_DIR, 'npn_ce.log'), encoding='utf-8') as file:
            op_log = file.read()

        with open(os.path.join(TEST_DIR, 'npn_ce_small_signal.cir'), encoding='utf-8') as file:
            small_signal_netlist = sorted(file.read().split('\n'))

        output = spice.small_signal_netlist(netlist, op_log)
        self.assertEqual(sorted(output.split('\n')), small_signal_netlist)

    def test_npn_cascode(self):
        pass

if __name__ == '__main__':
    unittest.main()
