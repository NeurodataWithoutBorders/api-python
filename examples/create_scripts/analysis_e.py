#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as ut


"""
This example illustrates using an extension to store data in the the /analysis group.  
The /analysis group is reserved for results of lab-specific analysis.

The extension definition is in file "extensions/e-analysis.py".

The example is based on the contents of the Allen Institute for Brain Science
Cell Types database NWB files.

"""

OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"
########################################################################
# create a new NWB file
settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = ut.create_identifier("example /analysis group using extension.")
settings["mode"] = "w"
settings["start_time"] = "Sat Jul 04 2015 3:14:16"
settings["description"] = ("Test file demonstrating storing data in the /analysis group "
    "that is defined by an extension.")

# specify the extension (Could be more than one.  Only one used now).
settings['extensions'] = ["extensions/e-analysis.py"]

# create the NWB file object. this manages the file
print("Creating " + settings["file_name"])
f = nwb_file.open(**settings)

########################################################################
# This example, stores spike times for multiple sweeps
# create the group for the spike times
# The group ("aibs_spike_times") is defined in the extension

ast = f.make_group("aibs_spike_times")

# some sample data
times = [1.1, 1.2, 1.3, 1.4, 1.5]

# create some sample sweeps
for i in range(5):
    sweep_name = "sweep_%03i" % (i+1)
    ast.set_dataset("<aibs_sweep>", times, name=sweep_name)
    

# all done; close the file
f.close()

