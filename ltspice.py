import os
import subprocess


LTSPICE_PATH = r'C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe'


def asc_to_netlist(asc_path: str) -> str:
    """
    Generates a netlist file from a circuit schematic.

    :param asc_path: path to a .asc schematic file
    :return: path to the netlist file
    """
    args = [LTSPICE_PATH, '-netlist', asc_path]
    subprocess.check_output(args)
    dir, name = os.path.split(asc_path)
    name, _ = os.path.splitext(name)
    netlist_path = os.path.join(dir, name + '.net')
    return netlist_path


def run_op_analysis(path: str) -> str:
    """
    Performs an operating point analysis and saves the log file.

    :param path: path to a .asc schematic file or .net netlist file
    :return: path to the operating point analysis log file
    """
    args = [LTSPICE_PATH, '-b', '-Run', path]
    subprocess.check_output(args)
    dir, name = os.path.split(path)
    name, _ = os.path.splitext(name)
    log_path = os.path.join(dir, name + '.log')
    return log_path


if __name__ == '__main__':
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
    asc_to_netlist(os.path.join(TEST_DATA_DIR, '2N3904_cascode.asc'))
    asc_to_netlist(os.path.join(TEST_DATA_DIR, '2N3904_common_emitter.asc'))