#!/usr/bin/python
# import nwb
import numpy as np
# from nwb.nwbco import *
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils


# TESTS top-level fields stored in general
# TESTS storing metadata from file
# TESTS 'Custom' tagging on custom attributes

def test_field(fname, name):
    val = ut.verify_present(fname, "general/", name.lower())
    if val != name and val != np.bytes_(name):
        ut.error("Checking metadata", "field value incorrect")

def test_general_top():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    create_general_top(fname)
    test_field(fname, "DATA_COLLECTION")
    test_field(fname, "EXPERIMENT_DESCRIPTION")
    test_field(fname, "EXPERIMENTER")
    test_field(fname, "INSTITUTION")
    test_field(fname, "LAB")
    test_field(fname, "NOTES")
    test_field(fname, "PROTOCOL")
    test_field(fname, "PHARMACOLOGY")
    test_field(fname, "RELATED_PUBLICATIONS")
    test_field(fname, "SESSION_ID")
    test_field(fname, "SLICES")
    test_field(fname, "STIMULUS")
    test_field(fname, "SURGERY")
    test_field(fname, "VIRUS")
    val = ut.verify_present(fname, "general/", "source_script")
    if len(val) < 1000:
        ut.error("Checking metadata_from_file", "unexpected field size")
        
    # removing test for neurodata_type attribute custom on general/source_script, since its
    # not custom anymore
#     val = ut.verify_attribute_present(fname, "general/source_script", "neurodata_type")
#     if val != "Custom" and val != b"Custom":
#         ut.error("Checking custom tag", "neurodata_type incorrect")


def create_general_top(fname):
    settings = {}    
    settings["file_name"] = fname
    settings["start_time"] = "2008-09-15T15:53:00-08:00"
    settings["identifier"] = utils.create_identifier("general top test")
    settings["mode"] = "w"
    settings["description"] = "test top-level elements in /general"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
    
    #
#     neurodata.set_metadata(DATA_COLLECTION, "DATA_COLLECTION")
#     neurodata.set_metadata(EXPERIMENT_DESCRIPTION, "EXPERIMENT_DESCRIPTION")
#     neurodata.set_metadata(EXPERIMENTER, "EXPERIMENTER")
#     neurodata.set_metadata(INSTITUTION, "INSTITUTION")
#     neurodata.set_metadata(LAB, "LAB")
#     neurodata.set_metadata(NOTES, "NOTES")
#     neurodata.set_metadata(PROTOCOL, "PROTOCOL")
#     neurodata.set_metadata(PHARMACOLOGY, "PHARMACOLOGY")
#     neurodata.set_metadata(RELATED_PUBLICATIONS, "RELATED_PUBLICATIONS")
#     neurodata.set_metadata(SESSION_ID, "SESSION_ID")
#     neurodata.set_metadata(SLICES, "SLICES")
#     neurodata.set_metadata(STIMULUS, "STIMULUS")
#     neurodata.set_metadata(SURGERY, "SURGERY")
#     neurodata.set_metadata(VIRUS, "VIRUS")
#     #
#     neurodata.set_metadata_from_file("source_script", __file__)
    #
    
    f.set_dataset("data_collection","DATA_COLLECTION")
    f.set_dataset("experiment_description","EXPERIMENT_DESCRIPTION")    
    f.set_dataset("experimenter","EXPERIMENTER")
    f.set_dataset("institution","INSTITUTION")     
    f.set_dataset("lab","LAB")
    f.set_dataset("notes","NOTES")    
    f.set_dataset("protocol","PROTOCOL")
    f.set_dataset("pharmacology","PHARMACOLOGY")
    f.set_dataset("related_publications", "RELATED_PUBLICATIONS")
    f.set_dataset("session_id","SESSION_ID")    
    f.set_dataset("slices","SLICES")
    f.set_dataset("stimulus","STIMULUS")     
    f.set_dataset("surgery","SURGERY")
    f.set_dataset("virus", "VIRUS")
    
    # f.neurodata.set_metadata_from_file("source_script", __file__)
    f.set_dataset("source_script", utils.load_file(__file__))

       
    # neurodata.close()
    f.close()

test_general_top()
print("%s PASSED" % __file__)

