#!/usr/bin/python
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils


# TESTS storage of reference image

def test_refimage_series():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name = "refimage"
    create_refimage(fname, name)
    val = ut.verify_present(fname, "acquisition/images/", name)
    #if len(val) != 6:
    if len(val) != 5:
        ut.error("Checking ref image contents", "wrong dimension")
    val = ut.verify_attribute_present(fname, "acquisition/images/"+name, "format")
    if not ut.strcmp(val, "raw"):
        ut.error("Checking ref image format", "Wrong value")
    val = ut.verify_attribute_present(fname, "acquisition/images/"+name, "description")
    if not ut.strcmp(val, "test"):
        ut.error("Checking ref image description", "Wrong value")

def create_refimage(fname, name):
    settings = {}
    settings["file_name"] = fname
    settings["start_time"] = "2008-09-15T15:53:00-08:00"
    settings["identifier"] = utils.create_identifier("reference image test")
    settings["mode"] = "w"
    settings["description"] = "reference image test"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
    # neurodata.create_reference_image([1,2,3,4,5], name, "raw", "test")
    f.set_dataset("<image_X>", [1,2,3,4,5], dtype="uint8", name=name, attrs={
        "description": "test", "format":"raw"})
        
    # neurodata.close()
    f.close()

test_refimage_series()
print("%s PASSED" % __file__)

