#!/usr/bin/python
import nwb
# from nwb.nwbco import *
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# TESTS fields stored in general/optogenetics

def test_field(fname, name, subdir):
    val = ut.verify_present(fname, "general/optogenetics/"+subdir+"/", name.lower())
    if not ut.strcmp(val, name):
        ut.error("Checking metadata", "field value incorrect")

def test_general_optogen():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    create_general_optogen(fname)
    #
    val = ut.verify_present(fname, "general/optogenetics/", "optogen_custom")
    if not ut.strcmp(val, "OPTOGEN_CUSTOM"):
        ut.error("Checking custom", "Field value incorrect")
    #

    test_field(fname, "DESCRIPTION", "p1")
    #test_field(fname, "DESCRIPTIONx", "p1")
    #test_field(fname, "DESCRIPTION", "p1x")
    test_field(fname, "DEVICE", "p1")
#    test_field(fname, "LAMBDA", "p1")
    test_field(fname, "EXCITATION_LAMBDA", "p1")
    test_field(fname, "LOCATION", "p1")
    val = ut.verify_present(fname, "general/optogenetics/p1/", "optogen_site_custom") 
    if not ut.strcmp(val, "OPTOGEN_SITE_CUSTOM"):
        ut.error("Checking metadata", "field value incorrect")


def create_general_optogen(fname):
    settings = {}
    settings["start_time"] = "2008-09-15T15:53:00-08:00"
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("metadata optogenetic test")
    settings["mode"] = "w"
    settings["description"] = "test elements in /general/optogentics"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
    
#     neurodata.set_metadata(OPTOGEN_CUSTOM("optogen_custom"), "OPTOGEN_CUSTOM")
#     #
#     neurodata.set_metadata(OPTOGEN_SITE_DESCRIPTION("p1"), "DESCRIPTION")
#     neurodata.set_metadata(OPTOGEN_SITE_DEVICE("p1"), "DEVICE")
#     neurodata.set_metadata(OPTOGEN_SITE_LAMBDA("p1"), "LAMBDA")
#     neurodata.set_metadata(OPTOGEN_SITE_LOCATION("p1"), "LOCATION")
#     neurodata.set_metadata(OPTOGEN_SITE_CUSTOM("p1", "optogen_site_custom"), "OPTOGEN_SITE_CUSTOM")
    #
    
    g = f.make_group("optogenetics")
    g.set_custom_dataset("optogen_custom", "OPTOGEN_CUSTOM")
    
    p1 = g.make_group("<site_X>", "p1")
    p1.set_dataset("description","DESCRIPTION")
    p1.set_dataset("device", "DEVICE")
    p1.set_dataset("excitation_lambda","EXCITATION_LAMBDA")
    p1.set_dataset("location", "LOCATION")
    p1.set_custom_dataset("optogen_site_custom", "OPTOGEN_SITE_CUSTOM")
    
    # neurodata.close()
    f.close()

test_general_optogen()
print("%s PASSED" % __file__)

