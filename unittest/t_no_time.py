#!/usr/bin/python
import sys
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# creates time series without 'timestamps' or 'starting_time' fields
# TESTS TimeSeries.ignore_time()
# TESTS timeseries placement in acquisition, stimulus, templates

def test_notime_series():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name = "notime"
    # create_notime_series(fname, name, "acquisition")
    create_notime_series(fname, name, "/acquisition/timeseries")
    ut.verify_timeseries(fname, name, "acquisition/timeseries", "TimeSeries")
    ut.verify_absent(fname, "acquisition/timeseries/"+name, "timestamps")
    ut.verify_absent(fname, "acquisition/timeseries/"+name, "starting_time")

    # create_notime_series(fname, name, "stimulus")
    create_notime_series(fname, name, "/stimulus/presentation")
    ut.verify_timeseries(fname, name, "stimulus/presentation", "TimeSeries")
    # create_notime_series(fname, name, "template")
    create_notime_series(fname, name, "/stimulus/templates")
    ut.verify_timeseries(fname, name, "stimulus/templates", "TimeSeries")

def create_notime_series(fname, name, target):
    settings = {}
    # settings["filename"] = fname
    settings["file_name"] = fname
    # settings["identifier"] = nwb.create_identifier("notime example")
    settings["identifier"] = utils.create_identifier("notime example")
    # settings["overwrite"] = True
    settings["mode"] = "w"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["description"] = "Test no time"
    # neurodata = nwb.NWB(**settings)
    f = nwb_file.open(**settings)
    
    
    #
#     notime = neurodata.create_timeseries("TimeSeries", name, target)
#     notime.ignore_time()
#     notime.set_data([0], unit="n/a", conversion=1, resolution=1)

    notime = f.make_group("<TimeSeries>", name, path=target)
    # following used for testing more missing_fields
    # notime = f.make_group("<VoltageClampSeries>", name, path=target)
    notime.set_dataset("data", [0], attrs={"unit":"n/a",
        "conversion":1, "resolution":1})

    #
    # notime.finalize()
    # neurodata.close()
    f.close()

test_notime_series()
print("%s PASSED" % __file__)

