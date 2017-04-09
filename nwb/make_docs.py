# program to generate documentation from specification language definition(s)

import sys
# h5gate validate script
from . import h5gate as g
from . import doc_tools as dt

# print "sys.argv=%s" % sys.argv

if len(sys.argv) < 1 or len(sys.argv) > 3:
    print ("format is:")
    print ("pyhton %s [ <extensions> [<core_spec>] ]" % sys.argv[0])
    print ("OR")
    print ("python %s <hdf5_file>")
    print ("where:")
    print ("<extensions> is a common separated list of extension files, or '-' for none")
    print ("<core_spec> is the core format specification file.  Default is 'nwb_core.py'")
    print ("<hdf5_file> is an hdf5 (extension not '.py') containing format specifications")
    sys.exit(0)
if len(sys.argv) == 2 and not sys.argv[1].endswith('.py'):
    # assume loading specifications from hdf5 file
    spec_files = []
    file_name = sys.argv[1]
else:
    core_spec = 'nwb_core.py' if len(sys.argv) < 3 else sys.argv[2]
    extensions = [] if len(sys.argv) < 2 or sys.argv[1] == '-' else sys.argv[1].split(',')
    spec_files = [core_spec] + extensions
    file_name = None
options={'mode':'no_file'}
f = g.File(file_name, spec_files, options=options)
# doc = dt.generate(f)
dt.build_node_tree(f)
html = dt.make_doc(f)
f.close()
print (html)

