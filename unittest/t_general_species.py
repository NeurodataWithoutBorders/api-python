#!/usr/bin/python
# import nwb
# from nwb.nwbco import *
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# TESTS fields stored in general/subject

def test_field(fname, name):
    val = ut.verify_present(fname, "general/subject/", name.lower())
    if not ut.strcmp(val, name):
        ut.error("Checking metadata", "field value incorrect")

def test_general_subject():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    create_general_subject(fname)
    val = ut.verify_present(fname, "general/subject/", "description")
    if not ut.strcmp(val, "SUBJECT"):
        ut.error("Checking metadata", "field value incorrect")
    test_field(fname, "SUBJECT_ID")
    test_field(fname, "SPECIES")
    test_field(fname, "GENOTYPE")
    test_field(fname, "SEX")
    test_field(fname, "AGE")
    test_field(fname, "WEIGHT")


def create_general_subject(fname):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("general top test")
    settings["mode"] = "w"
    settings["description"] = "test top-level elements in /general"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
    
    #
#     neurodata.set_metadata(SUBJECT, "SUBJECT")
#     neurodata.set_metadata(SUBJECT_ID, "SUBJECT_ID")
#     neurodata.set_metadata(SPECIES, "SPECIES")
#     neurodata.set_metadata(GENOTYPE, "GENOTYPE")
#     neurodata.set_metadata(SEX, "SEX")
#     neurodata.set_metadata(AGE, "AGE")
#     neurodata.set_metadata(WEIGHT, "WEIGHT")
    #
    
    g = f.make_group("subject")
    g.set_dataset("description", "SUBJECT")
    g.set_dataset("subject_id", "SUBJECT_ID")
    g.set_dataset("species", "SPECIES")
    g.set_dataset("genotype", "GENOTYPE")
    g.set_dataset("sex", "SEX")
    g.set_dataset("age", "AGE")
    g.set_dataset("weight", "WEIGHT")
    
    # neurodata.close()
    f.close()

test_general_subject()
print("%s PASSED" % __file__)

