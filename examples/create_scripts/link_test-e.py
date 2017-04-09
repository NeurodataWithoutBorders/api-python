#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as ut


"""
Test extension defining a link

"""

OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"
########################################################################
# create a new NWB file
settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = ut.create_identifier("test link extension.")
settings["mode"] = "w"
settings["start_time"] = "Sat Jul 04 2015 3:14:16"
settings["description"] = ("Test making a link in the /analysis group "
    "that is defined by an extension.")

# specify the extension (Could be more than one.  Only one used now).
settings['extensions'] = ["extensions/e-link_test.py"]

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

#
pto = ast.set_dataset("pixel_time_offsets", times)

# now make the link
ptl = ast.set_dataset("pto_link", pto, attrs={"hello": "Natasha"})
ptl.set_attr("Mary", "bendrich")

# all done; close the file
f.close()

