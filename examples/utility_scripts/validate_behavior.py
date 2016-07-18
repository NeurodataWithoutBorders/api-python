# script demonstrating use of validate_file routine called from Python.

from nwb import nwb_validate as nwbv

file = "../created_nwb_files/behavior.nwb"
validation_result = nwbv.validate_file(file, verbosity="none")

print "validated", file
print "validation_result=", validation_result
print "all done"

