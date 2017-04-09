#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as utils
from nwb import value_summary as vs
import numpy as np
import h5py
from sys import version_info
import re


# Test creation of region references
# Region references are references to regions in a dataset.  They can be
# stored in datasets or attributes.  If storing in a dataset, apparently
# region references must be stored in an array (an array of region references).
# i.e. it id not allowed to store a region reference in a dataset without
# it being in an array.

# The NWB format does not currently include region references as part
# of the standard.  The reason for this, is that reading region references
# requires a different procedure than reading data stored directly in
# datasets and attributes and this requires additional complexity
# in the software to read NWB files.

# Nevertheless, there maybe instances in which region references could be
# useful when organizing data in an NWB file.
# This script demonstrates how to create region references 
# using the h5py interface along with the NWB API and also reading region
# references.

def create_nwb_file():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("Region reference test")
    settings["mode"] = "w"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["description"] = "Test file with region reference"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    return (f, fname)


# return value referenced by region reference ref
# f is an h5py File object
def get_ref_value(ref, f):
    assert isinstance(f, h5py.File)
    assert isinstance(ref, h5py.h5r.RegionReference)
    fid = f.id
    reftype = h5py.h5r.get_obj_type(ref, fid)
    assert reftype == h5py.h5g.DATASET
    refname = h5py.h5r.get_name(ref, fid)  # path to target of reference
    refds = f[refname]   # referenced dataset
    val = refds[ref]     # get referenced region
    return val

# display information about region reference.  Used for development.
# ref is the region reference, f is the h5py File object
def show_ref_info(ref, f):
    fid = f.id
    reftype = h5py.h5r.get_obj_type(ref, fid)
    refregion = h5py.h5r.get_region(ref, fid)
    refname = h5py.h5r.get_name(ref, fid)
    refderef = h5py.h5r.dereference(ref, fid)
    assert reftype == h5py.h5g.DATASET
    print("reftype=%i, refregion=%s, refname=%s, refderef=%s" % (reftype, refregion, refname, refderef))
    refds = f[refname]
    refreg = refds[ref]
    refreg_shape = refreg.shape
    refreg_dype = refreg.dtype
    print("Referenced region, shape=%s, type=%s, val=" % (refreg_shape, refreg_dype))
    print("%s" % refreg)
    # make value summary
    hash = vs.hashval(refregion.encode())
    value_summary = "<Region Reference: target='%s', hash='%s'>" % (refname, hash)
    print("value_summary=%s" % value_summary)
    expected_value = np.arange(2., 14., 2.);  # [  2.   4.   6.   8.  10.  12.]
    if not values_match(expected_value, refreg):
        print("expected values NOT found")
        # raise SystemError("** Error: Unable to find object base type in %s or %s" %
#                         (base_type, type(val)))
    import pdb; pdb.set_trace()


def test_region_reference():
    f, fname = create_nwb_file()
    # make some fake raw data
    raw = f.make_group("<TimeSeries>", name="raw_data", path="/acquisition/timeseries/")
    raw_data = np.arange(0.0, 100.0, 0.5)
    rd = raw.set_dataset("data", raw_data, attrs={"unit": "watt", "conversion":1.0, "resolution": 0.1,
        "source": "microelectrodes"})
    raw.set_dataset("starting_time", 0.1, attrs={"rate":0.1})
    raw.set_dataset("num_samples", 1000)
    # create a TimeSeries which has data referencing the raw data using a region reference
    ag = f.make_group("analysis")
    ag2 = ag.make_custom_group("<TimeSeries>", name="regref_data", attrs={"unit": "watt",
        "conversion":1.0, "resolution": 0.1, "source": "raw_data"})
    # below used to set as link
    # ag2.set_dataset("data", rd, attrs={"unit": "watt", "conversion":1.0, "resolution": 0.1})
    # set as region reference
    rawds = f.file_pointer[rd.full_path]  # h5py dataset
    # create region reference
    raw_regref = rawds.regionref[4:26:4]
    # create 1-element array containing region_reference
    ref_dtype = h5py.special_dtype(ref=h5py.h5r.RegionReference)
    rrds = np.array([raw_regref,], dtype=ref_dtype)
    # get h5py parent group for the dataset that will have the region reference
    ag2_h5py = f.file_pointer[ag2.full_path]
    ag2ds = ag2_h5py.create_dataset("raw_rref", data=rrds)
    # set an attribute to the region reference
    ag2ds.attrs["raw_rref"] = raw_regref
    # add TimeSeries datasets.  Note, dataset 'data' is normally required, not currently
    # checked for since TimeSeries group (ag2) is a custom group
    ag2.set_dataset("starting_time", 0.1, attrs={"rate":0.1})
    ag2.set_dataset("num_samples", 10)
    f.close()
    # now try to read region references
    f = h5py.File(fname, "r")
    path = "/analysis/regref_data/raw_rref"
    rrds_in = f[path]
    val = rrds_in.value
    if not (isinstance(val, np.ndarray) and val.shape == (1,) and val.size == 1 and
        isinstance(val[0], h5py.h5r.RegionReference)):
        raise SystemError("Failed to read RegionReference, found val=%s, type=%s" % (val, type(val)))
    ref = val[0]
    # show_ref_info(ref, f)
    found = get_ref_value(ref, f)
    expected = np.arange(2., 14., 2.);  # [  2.   4.   6.   8.  10.  12.]
    errors = []
    if not values_match(expected, found):
        errors.append("Region Reference from dataset does not match.  Expected=%s, found=%s" % (
            expected, found))
    # attribute region reference
    aref = rrds_in.attrs["raw_rref"]
    found = get_ref_value(aref, f)
    if not values_match(expected, found):
        errors.append("Region Reference from attribute does not match.  Expected=%s, found=%s" % (
            expected, found))
    f.close()
    if len(errors) > 0:
         raise SystemError("Errors found:\n%s" % "\n".join(errors))
    print("%s PASSED" % __file__)
    
#     print ("Dataset ref info:")
#     show_ref_info(ref, f)
#     aref = rrds_in.attrs["raw_rref"]
#     print ("Attribute ref info:")
#     show_ref_info(aref, f)
#     # import pdb; pdb.set_trace()
#     f.close()


def vals_match(a, b):
    match = a == b
    if not isinstance(match, bool):
        match = match.all()
    return match

def make_str(val):
    # convert val from bytes to unicode string
    if isinstance(val, (list, tuple, np.ndarray)) and len(val) > 0:
        return [make_str(v) for v in val]
    elif isinstance(val, (bytes, np.bytes_)):
        return val.decode('utf-8')

def values_match(expected, found):
    match = vals_match(expected, found)
    if not match and version_info[0] > 2:
        # try matching after converting bytes to unicode (python 3 strings)
        # in python 3, default string type is unicode, but these are stored as
        # ascii bytes if possible in the hdf5 file, and read back as bytes
        # for match to work, they must be converted back to unicode strings
        match = vals_match(expected, make_str(found))
    return match

# display_examples()
test_region_reference()

