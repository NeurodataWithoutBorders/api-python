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
# settings["filename"] = fname
settings["file_name"] = fname
# settings["identifier"] = nwb.create_identifier("Modification example")
settings["identifier"] = utils.create_identifier("Modification example")
# settings["overwrite"] = True
settings["mode"] = "w"
settings["description"] = "Modified empty file"
settings["start_time"] = "Sat Jul 04 2015 3:14:16"

# neurodata = nwb.NWB(**settings)
f = nwb_file.open(**settings)
# neurodata.close()
f.close()

#time.sleep(1)
settings = {}
# settings["filename"] = fname
settings["file_name"] = fname
# settings["overwrite"] = False
settings["mode"] = "r+"
# settings["modify"] = True
# neurodata = nwb.NWB(**settings)
f = nwb_file.open(**settings)
# need to actually change the file for SLAPI to update file_create_date
f.set_dataset("species", "SPECIES")
# neurodata.close()
f.close()

#time.sleep(1)
settings = {}
# settings["filename"] = fname
settings["file_name"] = fname
# settings["overwrite"] = False
settings["mode"] = "r+"
# settings["modify"] = True
# neurodata = nwb.NWB(**settings)
f = nwb_file.open(**settings)
# need to actually change the file for SLAPI to update file_create_date
f.set_dataset("genotype", "GENOTYPE")
# neurodata.close()
f.close()

f = h5py.File(fname)
dates = f["file_create_date"]
if len(dates) != 3:
    ut.error(__file__, "Expected 3 entries in file_create_date; found %d" % len(dates))

print("%s PASSED" % __file__)

