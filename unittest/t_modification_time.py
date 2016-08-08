#!/usr/bin/python
import h5py
import sys
# import nwb
import test_utils as ut
import time

from nwb import nwb_file
from nwb import nwb_utils as utils

# creates file and modifies it multiple times

if __file__.startswith("./"):
    fname = "s" + __file__[3:-3] + ".nwb"
else:
    fname = "s" + __file__[1:-3] + ".nwb"

settings = {}
settings["file_name"] = fname
settings["identifier"] = utils.create_identifier("Modification example")
settings["mode"] = "w"
settings["description"] = "Modified empty file"
settings["start_time"] = "Sat Jul 04 2015 3:14:16"
settings["verbosity"] = "none"

f = nwb_file.open(**settings)
f.close()

#time.sleep(1)
settings = {}
settings["file_name"] = fname
settings["mode"] = "r+"
settings["verbosity"] = "none"
f = nwb_file.open(**settings)
# need to actually change the file for SLAPI to update file_create_date
f.set_dataset("species", "SPECIES")
f.close()

#time.sleep(1)
settings = {}
settings["file_name"] = fname
settings["mode"] = "r+"
settings["verbosity"] = "none"
f = nwb_file.open(**settings)
# need to actually change the file for SLAPI to update file_create_date
f.set_dataset("genotype", "GENOTYPE")
f.close()

f = h5py.File(fname)
dates = f["file_create_date"]
if len(dates) != 3:
    ut.error(__file__, "Expected 3 entries in file_create_date; found %d" % len(dates))

print("%s PASSED" % __file__)

