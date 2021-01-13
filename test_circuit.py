import unittest
import os
import subprocess

from circuit import Circuit, VoltageSource


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
LTSPICE_PATH = "C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe"


def ltspice_generate_netlist(asc_file: str) -> str:
    """
    Generates a netlist file from a circuit schematic.

    :param asc_file: a schematic file
    :return: a netlist file
    """
    args = [LTSPICE_PATH, '-netlist', asc_file]
    subprocess.check_output(args)
    dir, name = os.path.split(asc_file)
    name, _ = os.path.splitext(name)
    netlist_file = os.path.join(dir, name + '.net')
    return netlist_file


def ltspice_run_analysis(file: str) -> str:
    """
    Performs an operating point analysis and saves the log file.

    :param file: a schematic or netlist file
    :return: an operating point analysis log file
    """
    args = [LTSPICE_PATH, '-b', '-Run', file]
    subprocess.check_output(args)
    dir, name = os.path.split(file)
    name, _ = os.path.splitext(name)
    log_file = os.path.join(dir, name + '.log')
    return log_file


def iter_netlist(file):
    with open(file, 'r', encoding='utf-8') as file:
        yield from (line.rstrip() for line in file)


class TestCircuit(unittest.TestCase):
    def test_2N3904_common_emitter(self):
        # Generate the netlist file and log file for input circuit.
        schematic_file = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.asc')
        netlist_file = ltspice_generate_netlist(schematic_file)
        log_file = ltspice_run_analysis(netlist_file)

        small_signal_netlist_file = os.path.join(TEST_DATA_DIR, '2N3904_common_emitter_small_signal.net')
        expected_netlist = sorted(iter_netlist(small_signal_netlist_file))

        # Instantiate circuit.
        circuit = Circuit.from_ltspice(netlist_file, log_file)
        actual_netlist = sorted(component.to_netlist_entry()
                                for _, _, component in circuit.iter_components())

        self.assertEqual(expected_netlist, actual_netlist)

    def test_2N3904_cascode(self):
        # Generate the netlist file and log file for input circuit.
        schematic_file = os.path.join(TEST_DATA_DIR, '2N3904_cascode.asc')
        netlist_file = ltspice_generate_netlist(schematic_file)
        log_file = ltspice_run_analysis(netlist_file)

        small_signal_netlist_file = os.path.join(TEST_DATA_DIR, '2N3904_cascode_small_signal.net')
        expected_netlist = sorted(iter_netlist(small_signal_netlist_file))

        # Instantiate circuit.
        circuit = Circuit.from_ltspice(netlist_file, log_file)
        actual_netlist = sorted(component.to_netlist_entry()
                                for _, _, component in circuit.iter_components())

        self.assertEqual(expected_netlist, actual_netlist)


if __name__ == '__main__':
    unittest.main(verbosity=2)
