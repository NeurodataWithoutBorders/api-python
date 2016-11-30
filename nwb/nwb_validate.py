
# program to validate nwb files using specification language definition

import sys
import nwb.nwb_file as nwb_file


def validate_file(name, core_spec="nwb_core.py", extensions=None, verbosity="all"):
    """
    Parameters
    ----------
        name: string
        Name (including path) of file to be validated

        core_spec: string (default: 'nwb_core.py')
        Name of core specification file or '-' to load specification(s) from HDF5 file.
        
        extensions: array
        Array of extension files
        
        verbosity: string (default: 'all')
        Controls how much validation output is displayed.  Options are:
        'all', 'summary', and 'none'
        

    Returns
    -------
        validation_result: dict
        Result of validation.  Has keys: 'errors', 'warnings', 'added' which
        contain counts of errors, warnings and additions.  Additions are groups,
        datasets or attributes added which are not defined by the core_spec
        specification.
    """
    if extensions is None:
        extensions = []
    # to validate, open the file in read-only mode, then close it
    f = nwb_file.open(name, mode="r", core_spec=core_spec, extensions=extensions, verbosity=verbosity)
    validation_result = f.close()
    return validation_result


if __name__ == "__main__":

    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("format is:")
        print("python %s <file_name> [ <extensions> [<core_spec>] ]" % sys.argv[0])
        print("where:")
        print("<extensions> is a common separated list of extension files, or '-' for none")
        print("<core_spec> is the core format specification file.  Default is 'nwb_core.py'")
        print("Use two dashes, e.g. '- -' to load saved specifications from <file_name>")
        sys.exit(0)
    core_spec = 'nwb_core.py' if len(sys.argv) < 4 else sys.argv[3]
    extensions = [] if len(sys.argv) < 3 or sys.argv[2] == '-' else sys.argv[2].split(',')
    file_name = sys.argv[1]
    if extensions == [] and core_spec == "-":
        print("Loading specifications from file '%s'" % file_name)
    validate_file(file_name, core_spec=core_spec, extensions=extensions)


