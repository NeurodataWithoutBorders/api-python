#!/usr/bin/python
import sys
# import nwb
from nwb import nwb_file
from nwb import nwb_utils as utils
import numpy as np
import h5py
from sys import version_info
import re


# test creation of strings of different types.
# Passed values for strings, and the way they should be stored in hdf5 are:
#
# __Passed Value_______        __Stored type (in hdf5)_____________________
#
# - bytes, or unicode          - Fixed length ascii, if ascii, otherwise variable length utf-8
#
# - array of bytes or unicode  - Array of fixed length ascii, if ascii, 
#                                otherwise variable length utf-8
#
# - numpy array, with dtype=
#   h5py.special_dtype(vlen=unicode)  - Store as variable length utf-8
#
# Need to test for both attributes and data sets.
#

# set unicode to str if using Python 3 (which does not have unicode class)
try:
    unicode
except NameError:
    unicode = str


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
    settings["description"] = "Test file with different strings"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    return (f, fname)

# special h5py type for variable length strings
var_len_dt = h5py.special_dtype(vlen=unicode)

# tuples of: name, storage type (s - fixed string, v - variable), value
string_examples = [
    ("bytes", "s", "byte string"),
    (u"unicode %.,-\u00b5\u00ae", "v", u"Unicode, \u00ae\u0391\u0392\u0393\u00b5"),
    ("default", "s", "Default String Type"),
    ("numpyString", "s", np.string_("Numpy String")),
    ("numpyBytes", "s", np.bytes_("Numpy Bytes")),
    # lists
    ("byteList", "s", [b"Hello-", b"b-world"]),
    ("unicodeList", "v", [u"45 \u00b5Amps", u"unicode, u\u00ae\u0391\u0392\u0393\u00b5"]),
    ("defaultList", "s", ["hello","default"]),
    # 1-d numpy arrays
    ("numpyDefaultArray", "s", np.array(["Numpy", "default", "array"])),
    ("numpyStringArray", "s", np.array(["numpy","string", "array"], dtype=np.string_)),
    ("numpyBytesArray", "s", np.array([b"numpy",b"bytes", b"array"], dtype=np.bytes_)),
    ("numpyUnicodeArray", "v", np.array([u"numpy",u"unicode\u00ae\u0391\u0392\u0393\u00b5", u"array\u00ae\u0391\u0392\u0393\u00b5"])),
    # 2-d lists
    ("twoDdefaultList", "s", [["a","beta", "gam"], ["code", "d", "elph"]]),
    ("twoDbyteList", "s", [[b"a",b"beta", b"gam"], [b"code", b"d", b"elph"]]),
    ("twoDUnicodeList", "v", [[u"a\u00b5",u"beta\u00ae", u"gam"], [u"code", u"d\u00ae", u"elph"]]),
    # 2-d numpy arrays
    ("twoDnumpyDefault", "s", np.array([["a","beta", "gam"], ["code", "d", "elph"]])),
    ("twoDnumpyString", "s", np.array([["a","beta", "gam"], ["code", "d", "elph"]], dtype=np.string_)),
    ("twoDnumpyBytes", "s", np.array([[b"a",b"beta", b"gam"], [b"code", b"d", b"elph"]], dtype=np.bytes_)),
    ("twoDnumpyUnicode", "v", np.array([[u"a\u00b5",u"beta\u00ae", u"gam"], [u"code", u"d\u00ae", u"elph"]])),
    # Array of normal strings, but force storing as variable length using dtype
    ("forceVariableLength", "v", np.array(["short", "somewhat longer text"], dtype=var_len_dt))
    ]
  
def display_examples():
    global string_examples
    for example in string_examples:
        name, val = example
        print ("%s\t%s"% (name, val))

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

def get_h5type(val):
    # return type of value read from hdf5 file
    # return "v" for variable types (Unicode, numpy.ndarray objects
    # return "s" for fixed length types ('numpy.string_'
    val_type = str(type(val))
    if val_type in ("<type 'numpy.ndarray'>", "<class 'numpy.ndarray'>"):
        val_type = str(val.dtype)
    if re.match("^\|S\d+$", val_type) or val_type in ("<type 'numpy.string_'>",
        "<class 'numpy.bytes_'>"  # python 3
        ):
        h5type = "s"
    elif val_type in ("<type 'unicode'>", "object", 
        "<class 'str'>"  # python 3
        ):
        h5type = "v"
    else:
        sys.exit("Unexpected value type for %s, type=%s" % (val, val_type))
    return h5type

def test_strings():
    global string_examples
    f, fname = create_nwb_file()
    ang = f.make_group("analysis")
    stg = ang.make_custom_group("strings")
    for example in string_examples:
        name, stype, val = example
        assert stype in ("s", "v")
        # print("Setting %s attribute" % name)
        stg.set_attr(name, val)
        # print("Setting %s dataset" % name)
        stg.set_custom_dataset(name, val)
    f.close()
    # now read created file and verify values match
    f = h5py.File(fname, "r")
    stg = f["analysis/strings"]
    errors = []
    for example in string_examples:
        name,  stype, val = example
        # check attribute value
        aval = stg.attrs[name]
        if not values_match(val, aval):
            error = "attribute %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
                name, val, type(val), aval, type(aval))
            errors.append(error)
        # check dataset value
        dval = stg[name].value
        if not values_match(val, dval):
            error = "dataset %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
                name, val, type(val), aval, type(aval))
            errors.append(error)
        # check type of values stored.  Should be fixed except for unicode and
        # arrays of unicode, or forceVariableLength
        aval_type = get_h5type(aval)
        dval_type = get_h5type(dval)
        # print ("%s - %s, attribute type: %s, dataset type: %s" % (name, stype, aval_type, dval_type))
        if aval_type != stype:
            error = "attribute %s, read type expected = '%s', found='%s'" % (name, stype, aval_type)
            errors.append(error)
        if dval_type != stype:
            error = "dataset %s, read type expected = '%s', found='%s'" % (name, stype, dval_type)
            errors.append(error) 
    f.close()
    if len(errors) > 0:
        sys.exit("Errors found:\n%s" % "\n".join(errors))
    print("%s PASSED" % __file__)


# display_examples()
test_strings()

