# This script demonstrates creating documentation for the NWB format."
#
# Documentation may be created for the core format alone, or the"
# core format combined with one or more extensions."
#
# The documentation is generated from the format specifications."
# The format specifications can be in standalone '.py' files or"
# can be loaded from a created NWB file.  The latter method "
# is useful for generating documentaiton that is guaranteed to"
# describe a particular NWB file."


import sys
import glob
import os, fnmatch
from subprocess import check_output
from sys import version_info  # py3

# global constants
txt_output_dir="../text_output_files/doc"
nwb_dir="../created_nwb_files"


# py3: convert bytes to str (unicode) if Python 3   
def make_str3(val):
    if isinstance(val, bytes) and version_info[0] > 2:
        return val.decode('utf-8')
    else:
        return val


def do_command(cmd, output_file):
    """ execute command in cmd, write to output_file"""
    global txt_output_dir
    output_path = os.path.join(txt_output_dir, output_file)
    print ("doing: %s > %s" % (cmd, output_path))
    output = check_output(cmd.split(" "))
    with open(output_path, "w") as f:
        f.write(make_str3(output))


print ("documentation for core, e.g. file 'nwb_core.py'")
cmd = "python -m nwb.make_docs"
out =  "core_doc.html"
do_command(cmd, out)

print ("documentation using two external extensions")
cmd = ("python -m nwb.make_docs ../create_scripts/extensions/e-general.py,"
    "../create_scripts/extensions/e-intracellular.py")
out = "core_intra_gen.html"
do_command(cmd, out)

print ("documentation using schema's stored in created NWB files")
nwb_files = glob.glob(os.path.join(nwb_dir, "*-e.nwb"))
for file_path in nwb_files:
    base_name = os.path.basename(file_path)[0:-4]
    cmd = "python -m nwb.make_docs %s" % file_path
    out = "%s.html" % base_name
    do_command(cmd,out)

sys.exit()

