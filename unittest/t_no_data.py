#!/usr/bin/python
import sys
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# creates time series without 'data' field
# TESTS TimeSeries.ignore_data()

def test_nodata_series():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name = "nodata"
    # create_nodata_series(fname, name, "acquisition")
    create_nodata_series(fname, name, "/acquisition/timeseries")
    ut.verify_timeseries(fname, name, "acquisition/timeseries", "TimeSeries")
    ut.verify_absent(fname, "acquisition/timeseries/"+name, "data")

def create_nodata_series(fname, name, target):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("nodata example")
    settings["mode"] = "w"
    settings["description"] = "time series no data test"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
    
    #
#     nodata = neurodata.create_timeseries("TimeSeries", name, target)
#     nodata.ignore_data()
#     nodata.set_time([0])

    nodata = f.make_group("<TimeSeries>", name, path=target)
    nodata.set_dataset("timestamps", [0])
    #
    # nodata.finalize()
    # neurodata.close()
    f.close()

test_nodata_series()
print("%s PASSED" % __file__)

