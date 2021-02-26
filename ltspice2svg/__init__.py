import subprocess
import tempfile
import os
import contextlib


@contextlib.contextmanager
def temporary_filename(suffix=None):
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


def asc_to_svg(schematic: str) -> str:
    """Converts an LTSpice schematic to an XML SVG string.

    Args:
        schematic: A schematic string.

    Returns:
        An <svg> element as a string.
    """
    with temporary_filename() as asc_file, temporary_filename() as svg_file:
        # Create temporary files as the ltspice2svg library expects file names.

        with open(asc_file, 'w') as f:
            f.write(schematic)

        script_dir, _ = os.path.split(__file__)
        s = subprocess.check_output(['python',
                                     os.path.join(script_dir, '_asc_to_svg.py'),
                                     asc_file,
                                     svg_file])

        with open(svg_file, 'r') as f:
            # Skip one line for the SVG element.
            next(f)
            return f.read()
