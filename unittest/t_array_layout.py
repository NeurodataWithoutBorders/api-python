#!/usr/bin/python
import sys
# import nwb
from nwb import nwb_file
from nwb import nwb_utils as utils
import numpy as np
import h5py
from sys import version_info
import re
import numpy as np


# test creation of arrays with different number of dimensions.
# This test made many to ensure consistency between data files
# created in matlab and python, since matlab stores arrays in
# column major order and python in row major order.  The
# nwb file created by the matlab version of this test should
# match that created by the python version (e.g. this test).


def create_nwb_file():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("String test")
    settings["mode"] = "w"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["description"] = "Test array layout storage"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    return (f, fname)

# special h5py type for variable length strings
# var_len_dt = h5py.special_dtype(vlen=unicode)

# tuples of: name, value
# make all of them int32 using numpy
array_examples = [
    ("oneD_range5", np.array([0, 1, 2, 3, 4], dtype='int32')),
    ("twoD_2rows_3cols", np.array([[ 0, 1, 2], [3, 4, 5]], dtype='int32')),
    ("threeD_2x2x3", np.array([[[1,2,3],[2,3,4]],[[3,4,5],[4,5,6]]], dtype='int32'))
    ]
  
def display_examples():
    global array_examples
    for example in array_examples:
        name, val = example
        print ("%s\t%s"% (name, val))

def vals_match(a, b):
    match = a == b
    if not isinstance(match, bool):
        match = match.all()
    return match


def values_match(expected, found):
    match = vals_match(expected, found)
    if not match and version_info[0] > 2:
        # try matching after converting bytes to unicode (python 3 strings)
        # in python 3, default string type is unicode, but these are stored as
        # ascii bytes if possible in the hdf5 file, and read back as bytes
        # for match to work, they must be converted back to unicode strings
        match = vals_match(expected, make_str(found))
    return match


def test_array_layout():
    global array_examples
    f, fname = create_nwb_file()
    ang = f.make_group("analysis")
    stg = ang.make_custom_group("arrays")
    for example in array_examples:
        name, val = example
        # print("Setting %s attribute" % name)
        # prepend 'ga_' on attribute name stored in group
        ga_name = "ga_%s" % name
        stg.set_attr(ga_name, val)
        # print("Setting %s dataset" % name)
        # also save attribute with same name
        # prepend 'da_' on attribute name stored with dataset
        da_name = "da_%s" % name      
        stg.set_custom_dataset(name, val, attrs={da_name: val})
    f.close()
    # now read created file and verify values match
    f = h5py.File(fname, "r")
    stg = f["analysis/arrays"]
    errors = []
    for example in array_examples:
        name,  val = example
        # check attribute value
        # prepend 'ga_' on attribute name stored in group
        ga_name = "ga_%s" % name
        aval = stg.attrs[ga_name]
        if not values_match(val, aval):
            error = "attribute %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
                ga_name, val, type(val), aval, type(aval))
            errors.append(error)
        # check dataset value
        dval = stg[name].value
        if not values_match(val, dval):
            error = "dataset %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
                name, val, type(val), aval, type(aval))
            errors.append(error)
        # check dataset attribute value
        # prepend 'da_' on attribute name stored with dataset
        da_name = "da_%s" % name       
        dsaval = stg[name].attrs[da_name]
        if not values_match(val, dsaval):
            error = "dataset %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
                da_name, val, type(val), aval, type(aval))
            errors.append(error)
                

    f.close()
    if len(errors) > 0:
        sys.exit("Errors found:\n%s" % "\n".join(errors))
    print("%s PASSED" % __file__)


# display_examples()
test_array_layout()

