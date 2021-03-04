import os
import subprocess
import contextlib
import tempfile

LTSPICE_PATH = r'C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe'


@contextlib.contextmanager
def _temporary_filename(suffix=None):
    """Context that introduces a temporary file.

    Creates a temporary file, yields its name, and upon context exit, deletes it.
    (In contrast, tempfile.NamedTemporaryFile() provides a 'file' object and
    deletes the file as soon as that file object is closed, so the temporary file
    cannot be safely re-opened by another library or process.)

    Args:
        suffix: desired filename extension (e.g. '.mp4').

    Yields:
        The name of the temporary file.

    Notes:
        Taken from https://stackoverflow.com/questions/3924117/how-to-use-tempfile-namedtemporaryfile-in-python
    """
    try:
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_name = f.name
        f.close()
        yield tmp_name
    finally:
        os.unlink(tmp_name)


def _asc_to_netlist_file(schematic_path: str) -> str:
    """
    Generates a netlist file from a circuit schematic.

    :param schematic_path: path to a .asc schematic file
    :return: path to the netlist file
    """
    args = [LTSPICE_PATH, '-netlist', schematic_path]
    subprocess.check_output(args)
    dir, name = os.path.split(schematic_path)
    name, _ = os.path.splitext(name)
    netlist_path = os.path.join(dir, name + '.net')
    return netlist_path


def _save_op_point_log(path: str) -> str:
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


def asc_to_netlist(schematic: str) -> str:
    """Generates a netlist for the given schematic.

    Args:
        schematic: Content of a schematic file.

    Returns:
        The content of the netlist file.
    """
    with _temporary_filename() as schematic_file:

        with open(schematic_file, 'w') as f:
            f.write(schematic)

        netlist_file = _asc_to_netlist_file(schematic_file)

        with open(netlist_file, 'r') as f:
            netlist = f.read()

        os.unlink(netlist_file)
        return netlist


if __name__ == '__main__':
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
    schematic_file = os.path.join(TEST_DATA_DIR, 'common_source.asc')

    with open(schematic_file, 'r') as f:
        schematic = f.read()

    print(asc_to_netlist(schematic))