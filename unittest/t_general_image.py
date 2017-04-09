#!/usr/bin/python
# import nwb
import numpy as np
# from nwb.nwbco import *
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# TESTS fields stored in general/optophysiology

def test_field(fname, name, subdir):
    val = ut.verify_present(fname, "general/optophysiology/"+subdir+"/", name.lower())
    if val != name and val != np.bytes_(name):
        ut.error("Checking metadata", "field value incorrect")

def test_general_intra():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    create_general_intra(fname)
    #
    val = ut.verify_present(fname, "general/optophysiology/", "image_custom")
    if not ut.strcmp(val, "IMAGE_CUSTOM"):
    #if val != "IMAGE_CUSTOM" and val != b"IMAGE_CUSTOM":
        ut.error("Checking custom", "Field value incorrect")
    #

    test_field(fname, "DESCRIPTION", "p1")
    test_field(fname, "DEVICE", "p1")
    test_field(fname, "EXCITATION_LAMBDA", "p1")
    test_field(fname, "IMAGE_SITE_CUSTOM", "p1")
    test_field(fname, "IMAGING_RATE", "p1")
    test_field(fname, "INDICATOR", "p1")
    test_field(fname, "LOCATION", "p1")
    val = ut.verify_present(fname, "general/optophysiology/p1/", "manifold")
    if len(val) != 2 or len(val[0]) != 2 or len(val[0][0]) != 3:
        ut.error("Checking manifold", "Incorrect dimensions")
    val = ut.verify_present(fname, "general/optophysiology/p1/red/", "description")
    if not ut.strcmp(val, "DESCRIPTION"):
        ut.error("Checking metadata", "field value incorrect")
    val = ut.verify_present(fname, "general/optophysiology/p1/green/", "description")
    if not ut.strcmp(val, "DESCRIPTION"):
        ut.error("Checking metadata", "field value incorrect")
    val = ut.verify_present(fname, "general/optophysiology/p1/red/", "emission_lambda")
    if not ut.strcmp(val, "CHANNEL_LAMBDA"):
        ut.error("Checking metadata", "field value incorrect")
    val = ut.verify_present(fname, "general/optophysiology/p1/green/", "emission_lambda")
    if not ut.strcmp(val, "CHANNEL_LAMBDA"):
        ut.error("Checking metadata", "field value incorrect")


def create_general_intra(fname):
    settings = {}
    settings["start_time"] = "2008-09-15T15:53:00-08:00"
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("general optophysiology test")
    settings["mode"] = "w"
    settings["description"] = "test elements in /general/optophysiology"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    #
    #neurodata.set_metadata(IMAGE_CUSTOM("image_custom"), "IMAGE_CUSTOM")
    g = f.make_group("optophysiology")
    g.set_custom_dataset("image_custom", "IMAGE_CUSTOM")
    #
    # neurodata.set_metadata(IMAGE_SITE_DESCRIPTION("p1"), "DESCRIPTION")
    p1 = g.make_group("<imaging_plane_X>", "p1")
    p1.set_dataset("description", "DESCRIPTION")
    
    # MANUAL CHECK
    # try storing string - -type system should balk
    #neurodata.set_metadata(IMAGE_SITE_MANIFOLD("p1"), "MANIFOLD")
    
    
    # neurodata.set_metadata(IMAGE_SITE_MANIFOLD("p1"), [[[1,2,3],[2,3,4]],[[3,4,5],[4,5,6]]])
#     neurodata.set_metadata(IMAGE_SITE_INDICATOR("p1"), "INDICATOR")
#     neurodata.set_metadata(IMAGE_SITE_EXCITATION_LAMBDA("p1"), "EXCITATION_LAMBDA")
#     neurodata.set_metadata(IMAGE_SITE_CHANNEL_LAMBDA("p1", "red"), "CHANNEL_LAMBDA")
#     neurodata.set_metadata(IMAGE_SITE_CHANNEL_DESCRIPTION("p1", "red"), "DESCRIPTION")
#     neurodata.set_metadata(IMAGE_SITE_CHANNEL_LAMBDA("p1", "green"), "CHANNEL_LAMBDA")
#     neurodata.set_metadata(IMAGE_SITE_CHANNEL_DESCRIPTION("p1", "green"), "DESCRIPTION")
#     neurodata.set_metadata(IMAGE_SITE_IMAGING_RATE("p1"), "IMAGING_RATE")
#     neurodata.set_metadata(IMAGE_SITE_LOCATION("p1"), "LOCATION")
#     neurodata.set_metadata(IMAGE_SITE_DEVICE("p1"), "DEVICE")
#     neurodata.set_metadata(IMAGE_SITE_CUSTOM("p1", "image_site_custom"), "IMAGE_SITE_CUSTOM")
    #
    
    p1.set_dataset("manifold", [[[1,2,3],[2,3,4]],[[3,4,5],[4,5,6]]])
    p1.set_dataset("indicator", "INDICATOR")
    p1.set_dataset("excitation_lambda","EXCITATION_LAMBDA")
    p1_red = p1.make_group("<channel_X>", "red")
    p1_red.set_dataset("emission_lambda","CHANNEL_LAMBDA")
    p1_red.set_dataset("description","DESCRIPTION")
    p1_green = p1.make_group("<channel_X>", "green")
    p1_green.set_dataset("emission_lambda","CHANNEL_LAMBDA")
    p1_green.set_dataset("description","DESCRIPTION")
    p1.set_dataset("imaging_rate", "IMAGING_RATE")
    p1.set_dataset("location", "LOCATION")
    p1.set_dataset("device", "DEVICE")
    p1.set_custom_dataset("image_site_custom", "IMAGE_SITE_CUSTOM")
   
    
    # neurodata.close()
    f.close()

test_general_intra()
print("%s PASSED" % __file__)

