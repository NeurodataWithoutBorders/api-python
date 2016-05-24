# program to validate nwb files using specification language definition

import sys
import nwb_file

if len(sys.argv) < 2 or len(sys.argv) > 4:
    print "format is:"
    print "python %s <file_name> [ <extensions> [<core_spec>] ]" % sys.argv[0]
    print "where:"
    print "<extensions> is a common separated list of extension files, or '-' for none"
    print "<core_spec> is the core format specification file.  Default is 'nwb_core.py'"
    print "Use two dashes, e.g. '- -' to load saved specifications from <file_name>"
    sys.exit(0)
core_spec = 'nwb_core.py' if len(sys.argv) < 4 else sys.argv[3]
extensions = [] if len(sys.argv) < 3 or sys.argv[2] == '-' else sys.argv[2].split(',')
file_name = sys.argv[1]
if extensions == [] and core_spec == "-":
    print "Loading specifications from file '%s'" % file_name

# to validate, open the file in read-only mode, then close it
f = nwb_file.open(file_name, mode="r", core_spec=core_spec, extensions=extensions)
f.close()

