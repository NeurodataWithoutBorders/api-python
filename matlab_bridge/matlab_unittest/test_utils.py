import h5py
import numpy as np
import sys
import traceback
import inspect
# import nwb

def print_error(context, err_string):
    # func = traceback.extract_stack()[-3][2]
    print("----------------------------------------")
    print("**** Failed unit test %s" % inspect.stack()[0][1])
    # print("**** Error in function '%s'" % func)
    print("Context: " + context)
    print("Error: " + err_string)
    print("Stack:")
    traceback.print_stack()
    print("----------------------------------------")
    sys.exit(1)

def error(context, err_string):
    print_error(context, err_string)

def exc_error(context, exc):
    print_error(context, str(exc))

def search_for_string(h5_str, value):
    match = False
    if h5_str is not None:
        if isinstance(h5_str, (str, np.string_)):
            if h5_str == value:
                match = True
        elif isinstance(h5_str, (list, np.ndarray)):
            match = False
            for i in range(len(h5_str)):
                if h5_str[i] == value or h5_str[i] == np.bytes_(value):
                    match = True
                    break
    return match

def search_for_substring(h5_str, value):
    match = False
    if h5_str is not None:
        if isinstance(h5_str, (str, np.string_)):
            if str(h5_str).find(value) >= 0:
                match = True
        elif isinstance(h5_str, (list, np.ndarray)):
            match = False
            for i in range(len(h5_str)):
                if str(h5_str[i]).find(value) >= 0:
                    match = True
                    break
#    if not match and not isinstance(value, (np.bytes_)):
#        return search_for_substring(h5_str, np.bytes_(value))
    return match

def verify_timeseries(hfile, name, location, ts_type):
    """ verify that a time series is valid

        makes sure that the entity with this name at the specified path
        has the minimum required fields for being a time series,
        that it is labeled as one, and that its ancestry is correct

        Arguments:
            hfile (text) name of nwb file (include path)
            
            name (text) name of time series

            location (text) path in HDF5 file

            ts_type (text) class name of time series to check for
            (eg, AnnotationSeries)

        Returns:
            *nothing*
    """ 
    try:
        f = h5py.File(hfile, 'r')
    except IOError as e:
        exc_error("Opening file", e)
    try:
        g = f[location]
    except Exception as e:
        exc_error("Opening group", e)
    try:
        ts = g[name]
    except Exception as e:
        exc_error("Fetching time series", e)
    try:
        nd_type = ts.attrs["neurodata_type"]
    except Exception as e:
        exc_error("reading neurodata_type", e)
    if nd_type != b"TimeSeries" and nd_type != "TimeSeries":
        error("checking neurodata type", "Unexpectedly found type %s, expected 'TimeSeries'" % nd_type)
    try:
        anc = ts.attrs["ancestry"]
    except Exception as e:
        exc_error("Reading ancestry", e)
    if not search_for_string(anc, ts_type):
        print("ts_type is " + ts_type)
        error("Checking ancestry", "Time series is not of type " + ts_type)
    missing = None
    if "missing_fields" in ts.attrs:
        missing = ts.attrs["missing_fields"]
    try:
        samp = ts["num_samples"].value
    except Exception as e:
        if not search_for_substring(missing, "num_samples"):
            error("Reading number of samples", e)
    try:
        samp = ts["data"].value
    except Exception as e:
        if not search_for_substring(missing, "data"):
            exc_error("Reading data", e)
    try:
        samp = ts["timestamps"].value
    except Exception as e:
        if "starting_time" not in ts:
            if not search_for_substring(missing, "timestamps"):
                error("Reading timestamps", e)
    f.close()
            

def verify_present(hfile, group, field):
    """ verify that a field is present and returns its contents
    """ 
    try:
        f = h5py.File(hfile, 'r')
    except IOError as e:
        exc_error("Opening file", e)
    try:
        g = f[group]
    except Exception as e:
        exc_error("Opening group", e)
    if field not in g:
        error("Verifying presence of '"+field+"'", "Field absent")
    obj = g[field]
    if type(obj).__name__ == "Group":
        val = None
    else:
        val = obj.value
    f.close()
    return val

def verify_attribute_present(hfile, obj, field):
    """ verify that an attribute is present and returns its contents
    """ 
    try:
        f = h5py.File(hfile, 'r')
    except IOError as e:
        exc_error("Opening file", e)
    try:
        g = f[obj]
    except Exception as e:
        exc_error("Fetching object", e)
    if field not in g.attrs:
        error("Verifying presence of attribute '"+field+"'", "Field absent")
    val = g.attrs[field]
    f.close()
    return val

def verify_absent(hfile, group, field):
    """ verify that a field is not present
    """ 
    try:
        f = h5py.File(hfile, 'r')
    except IOError as e:
        exc_error("Opening file", e)
    try:
        g = f[group]
    except Exception as e:
        exc_error("Opening group", e)
    if field in g:
        error("Verifying absence of '"+field+"'", "Field exists")
    f.close()

def create_new_file(fname, identifier):
    settings = {}
    settings["filename"] = fname
    settings["identifier"] = nwb.create_identifier(identifier)
    settings["overwrite"] = True
    settings["description"] = "softlink test"
    return nwb.NWB(**settings)

def strcmp(s1, s2):
    if s1 == s2 or s1 == np.bytes_(s2):
        return True
    return False

