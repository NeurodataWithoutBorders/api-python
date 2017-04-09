# Utility routines for processing values.
# Routine "value_summary" creates 'summary' (printable representation of value)
# that is the same in Python 2 and Python 3, and includes a hash of the entire value
# if the value display is longer than a threshold length.
# Other routines are used to support this and for Python 2 / Python 3 string
# compatibility.

import json
import numpy as np
from sys import version_info
import zlib
import string
import h5py
import warnings

# py3, set unicode to str if using Python 3 (which does not have unicode class)
try:
    unicode
except NameError:
    unicode = str

# global variable, for checking if string is printable
printset = set(string.printable)

# convert an integer to an string of letters
# this done so hashes are all letters and thus not used by function combine_messages 
def int2alph(val):
    assert isinstance(val, int)
    alph = []
    num_chars = 52  # a-z, A-Z
    while val > 0:
        val, r = divmod(val, num_chars)
        new_char = chr(r + ord('a')) if r < 26 else chr(r - 26 + ord('A'))
        alph.append(new_char)
    strval = "".join(reversed(alph))
    return (strval)
     
# make a hash of value (must be bytes)
def hashval(val):
    crc = zlib.adler32(val) & 0xffffffff
    hash = int2alph(crc)
    return hash

def hash_str(val):
    # compute hash of a string (either unicode or bytes)
    if isinstance(val, unicode):
        hash = hashval(val.encode('utf-8'))
    elif isinstance(val, bytes):
        # already are bytes
        hash = hashval(val)
    else:
        sys.exit("value not unicode or bytes: %s" % type(val))
    return hash


## following are for Python 2 / Python 3 string compatibility

def make_str(val):
    base_v = base_val(val)
    if isinstance(base_v,  (bytes, unicode)):
        # convert ndarray to list, py2 strings to bytes, py3 strings to unicode
        val = make_str2(val)
    return val


def make_str2(val):
    """ Recursive convert everything from bytes to str (unicode) for Python 3
    convert numpy ndarray to list if has str as base_val even if python 2
    this done so output from python2 and python3 will be identical because
    str(numpy.ndarray) does not have commas in the generated string,
    while str(list) does"""
    if isinstance(val, (list, tuple, np.ndarray)) and len(val) > 0:
        return [make_str2(v) for v in val]
    elif isinstance(val, bytes) and version_info[0] > 2:
        try:
            uval = val.decode('utf-8')
        except UnicodeDecodeError as e:
            # value is a binary string.  Leave as bytes
            return val
        return uval
    elif isinstance(val, unicode) and version_info[0] < 3:
        return val.encode('utf-8')
    else:
        return val

def make_str3(val):
    """py3: convert bytes to str (unicode) if Python 3, or unicode to bytes if Python 2"""
    if isinstance(val, bytes) and version_info[0] > 2:
        return val.decode('utf-8')
    elif isinstance(val, unicode) and version_info[0] < 3:
        return val.encode('utf-8')
    else:
        return val


def base_val(val):
    """ get first scalar value from list or tuple, or value itself if not list or tuple"""
    if isinstance(val, (list, tuple, np.ndarray)) and len(val) > 0:
        return base_val(val[0])
    else:
        return val
 

## end routines for Python 2 / Python 3 string compatibility


# def is_str_type(val):
#     # Return True if val is a string type
#     return isinstance(val, (bytes, bytearray, unicode, np.string_, np.bytes_, np.unicode))

def values_match(x, y, xfileObj = None, yfileObj = None):
    """ Compare x and y.  This needed because the types are unpredictable and sometimes
    ValueError is thrown when trying to compare.  xfileObj and yfileObj are the h5py File
    objects for x and y.  They are needed if x & y might be region references."""
    # convert to matching types (unicode) if one is unicode and the other bytes
    x0 = base_val(x)  # type of value in array or scalar
    y0 = base_val(y)
    if isinstance(x0, bytes) and isinstance(y0, unicode):
        x = make_str2(x)
    elif isinstance(x0, unicode) and isinstance(y0, bytes):
        y = make_str2(y)
    # start comparisons
    if x is y:
        return True
    # explicit checks for None used to prevent warnings like:
    # FutureWarning: comparison to `None` will result in an elementwise object comparison in the future.
    # eq = x==y
    if x is None:
        if y is None:
            return True
        else:
            return False
    if y is None:
        return False
    # compare arrays so corresponding NaN values are treated as a match
    if (isinstance(x, np.ndarray) and isinstance(y, np.ndarray)
        and np.issubdtype(x.dtype, np.float) and np.issubdtype(y.dtype, np.float)):
        # from: http://stackoverflow.com/questions/10710328/comparing-numpy-arrays-containing-nan
        try:
            np.testing.assert_equal(x,y)
        except AssertionError:
            return False
        return True
    # check for two scalar NaN.  If found, treat as match
    if (np.issubdtype(type(x), np.float) and np.issubdtype(type(y), np.float)
        # and x.shape == () and y.shape == ()
        and np.isnan(x) and np.isnan(y)):
        return True
    # check for both region references.  if so, match if the value_summary of them match
    if isinstance(x0, h5py.h5r.RegionReference) and isinstance(y0, h5py.h5r.RegionReference):
        if xfileObj is None or yfileObj is None:
            raise ValueError('Input to values_match is Region Reference, but h5py File objects not provided.')
        return make_value_summary(x, xfileObj) == make_value_summary(y, yfileObj)
    # add explicit check for str to force mismatch is str compared to non-string
    # if not prevented by "with warning" (below), this can cause if one is str, other array
    # "FutureWarning: elementwise comparison failed; returning scalar instead
#     if ((isinstance(x, str) and not isinstance(y, str)) 
#         or (isinstance(y, str) and not isinstance(x, str))):
#         return False
    try:
        with warnings.catch_warnings():
            # Filter warnings to remove message:
            # "FutureWarning: elementwise comparison failed; returning scalar instead,
            #   but in the future will perform elementwise comparison"
            # In either case (scalar False, or elementwise with an element False will return
            # False vie either the eq bool value (scalar) or the eq.all()
            warnings.simplefilter("ignore")
            eq = x==y
    except ValueError:
        # ValueError: shape mismatch: objects cannot be broadcast to a single shape
        return False
    if isinstance(eq, bool):
        return eq
    if (isinstance(x, (np.string_, str)) and isinstance(y, np.ndarray)) or (
        isinstance(y, (np.string_, str)) and isinstance(x, np.ndarray)):
        # this added to force mismatch in Python 2, if:
        # x == '[]', type(x) == <type 'numpy.string_'> and
        # y == array([], dtype='|S1'), type(y) == <type 'numpy.ndarray'>.  Also:
        # x type np.ndarray, y type str.  These
        # match in Python 2. They do not match in python 3.  Not matching is desired result.
        return False

    return eq.all()


def make_value_summary(val, fileObj, max_summary_length = 50):
    """ return text summary of value.  fileObj is the h5py File object.
    Return is in tuple: (value_summary, vs_msg, vs_msg_type)
    If vs_msg is not None it is either a warning or error message.  vs_msg_type
    indicates which (either 'warning' or 'error')
    if error or warning are not None, then they are a text error or warning"""
    # vs_error stores error message, vs_warning, warning message
    global vs_msg, vs_msg_type
    # initialize to None (no warning or error)
    vs_msg = vs_msg_type = None
    prefix = get_prefix(val, fileObj, max_summary_length)
    if (len(prefix) < max_summary_length or isinstance(val, h5py.h5r.RegionReference)
        or (isinstance(val, np.ndarray) and len(val) > 0 and 
        isinstance(val[0], h5py.h5r.RegionReference))):
        # include full prefix if RegionReference
        return (prefix, vs_msg, vs_msg_type)
        # return prefix
    # too long to display, need to compute hash
    if isinstance(val, (list, tuple)):
        # convert list or tuple to numpy array to compute hash
        hash = hashval(np.array(val).view(np.byte))
    elif isinstance(val, np.ndarray):
        # already is numpy array, get hash directly
        try:
            # try used in case is array of objects --which fails with .view
            val_view = val.view(np.byte)
        except TypeError as e:
            # assume array of objects;  convert to list then back to numpy array and try again
            val_view = np.array(val.tolist()).view(np.byte)
        hash = hashval(val_view)
    elif isinstance(val, unicode):
        hash = hashval(val.encode('utf-8'))
    elif isinstance(val, bytes):
        # already are bytes
        hash = hashval(val)
    else:
        # import pdb; pdb.set_trace()
        raise ValueError("unknown type of val, did not make hash: %s" % type(val))
    val_str = prefix[0:max_summary_length - 9]
    val_str =  "%s...%s" % (val_str, hash)
    return (val_str, vs_msg, vs_msg_type)
    # return val_str


def get_prefix(val, fileObj, num_chars):
    # return printable prefix of value of length num_chars
    global printset
    global vs_msg, vs_msg_type
    if isinstance(val, (list, tuple, np.ndarray)):
        lvals = []
        ccount = 0
        for iv in range(len(val)):
            v = val[iv]
            vp = get_prefix(v, fileObj, num_chars - ccount)
            lvals.append(vp)
            ccount += len(vp) + 1  # add one for comma or opening [
            if ccount > num_chars:
                prefix = "[%s" % ",".join(lvals)
                # if included all the values, add in closing ']', otherwise '...'
                close_str = "]" if iv == len(val) - 1 else "..."
                prefix = "%s%s" % (prefix, close_str)
                return prefix
        prefix = "[%s]" % ",".join(lvals)
        return prefix
    elif isinstance(val, (unicode, bytes)):
        prefix = val[0:num_chars] if len(val) > num_chars else val
        # if needed, convert prefix to printable form
        if isinstance(val, bytes) and version_info[0] > 2:
            try:
                prefix = prefix.decode('utf-8')
            except UnicodeDecodeError as e:
                # value is a binary string.
                hash = hashval(val)
                bmsg = "<<binary, hash=%s>>" % hash
                return bmsg
        elif isinstance(val, unicode) and version_info[0] < 3:
            prefix = prefix.encode('utf-8')
        # check if all characters in prefix are printable
        if set(prefix).issubset(printset):
            # all characters are printable
            return "\"%s\"" % prefix
        else:
            # must get hash
            hash = hash_str(val)
            prefix = "<<binary, hash=%s>>" % hash
            return prefix
    elif isinstance(val, (float, np.float_, np.float32)):
        val = float(val)
        if val.is_integer():
            prefix = str(int(val))
        else:
            prefix = "%-.4g" % val
        return prefix
    elif isinstance(val, (int, np.int_, np.int8, np.int16, np.int32, np.uint8, np.uint16, np.uint32)):
        return str(val)
    elif isinstance(val, h5py.h5r.RegionReference):
        prefix = summarize_region_reference(val, fileObj)
        return prefix
    vs_msg = "Unknown type in value_summary.get_prefix, val=%s, type=%s" % (val, type(val))
    # vs_msg_type = "warning"
    # import pdb; pdb.set_trace()  
    raise SystemError(vs_msg)
    return str(val)

def summarize_region_reference(ref, fileObj):
    global vs_msg, vs_msg_type
    fid = fileObj.id
    refregion = h5py.h5r.get_region(ref, fid)
    refname = make_str(h5py.h5r.get_name(ref, fid))  # path to target of reference
    hash = hashval(refregion.encode())
    value_summary = "<Region Reference: target='%s', hash='%s'>" % (refname, hash)
    # store error, since region references not part of NWB specification
#     vs_msg = ("region reference, target='%s'; Region references are currently not allowed"
#         " because they require special code to read." % refname) 
#     vs_msg_type = "error" 
    return value_summary

#     reftype = h5py.h5r.get_obj_type(ref, fid)
#     assert reftype == h5py.h5g.DATASET
#     refname = h5py.h5r.get_name(ref, fid)  # path to target of reference
#     refds = f[refname]   # referenced dataset
#     val = refds[ref]     # get referenced region
#     return val



def test_value_summary():
    if version_info[0] > 2:
        # python 3 binary data
        binary_data = bytes([i for i in range(255)])
    else:
        # python 2 binary data
        binary_data = ''.join(chr(i) for i in range(255))
    # values to test with
    values = [
        "simple string",
        u"Unicode string",
        b"byte string",
        [ 1.2, 1.4, 1.5 ],
        [ 1, 2, 3],
        [ "simple", "strings"],
        [ u"unicode", u"strings"],
        [ b"byte", b"strings"],
        np.arange(1, 5, 1),
        np.arange(1.1, 6.0, 1.1),
        np.array(['numpy', 'bytes'], dtype=np.bytes_),
        np.array(['numpy', 'string'], dtype=np.string_),
        np.array(['numpy', 'unicode'], dtype=np.unicode_),
        np.arange(1000),
        np.arange(2500).reshape((50,50)),
        np.arange(1.0, 10.0, 0.01),
        [ "s%03i" % i for i in range(1000) ],
        [ u"u%03i" % i for i in range(1000) ],
        [ b"b%03i" % i for i in range(1000) ],
        binary_data,
    ]
    vsums=[]
    for val in values:
        vtype = type(val)
        dtype = val.dtype if isinstance(val, np.ndarray) else None
        val_summary = make_value_summary(val)
        print("type=%s, dtype=%s, val=%s" % (vtype, dtype, val_summary))
        vsums.append(val_summary)

    outfile = "vsums_py%s.txt" % version_info[0]
    fh = open(outfile, "w")
    fh.write("\n".join(vsums))
    fh.close()
    # To test, diff generated files for Python 2 and Python 3


if __name__ == "__main__":
    test_value_summary()