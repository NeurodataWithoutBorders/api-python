#!/usr/bin/python
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# TESTS top-level datasets

def test_refimage_series():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name = "refimage"
    create_refimage(fname, name)
    val = ut.verify_present(fname, "/", "identifier")
    if not ut.strcmp(val, "vwx"):
        ut.error("Checking file idenfier", "wrong contents")
    val = ut.verify_present(fname, "/", "file_create_date")
    val = ut.verify_present(fname, "/", "session_start_time")
    if not ut.strcmp(val, "xyz"):
        ut.error("Checking session start time", "wrong contents")
    val = ut.verify_present(fname, "/", "session_description")
    if not ut.strcmp(val, "wxy"):
        ut.error("Checking session start time", "wrong contents")

def create_refimage(fname, name):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = "vwx"
    settings["mode"] = "w"
    settings["description"] = "wxy"
    settings["start_time"] = "xyz"
    # neurodata = nwb.NWB(**settings)
    f = nwb_file.open(**settings)
    # neurodata.close()
    f.close()

test_refimage_series()
print("%s PASSED" % __file__)

