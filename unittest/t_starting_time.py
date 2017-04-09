
#!/usr/bin/python
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# TESTS use of TimeSeries.starting_time

def test_nodata_series():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name = "starting_time"
    # create_startingtime_series(fname, name, "acquisition")
    create_startingtime_series(fname, name, "/acquisition/timeseries")
    ut.verify_timeseries(fname, name, "acquisition/timeseries", "TimeSeries")
    ut.verify_absent(fname, "acquisition/timeseries/"+name, "timestamps")
    val = ut.verify_present(fname, "acquisition/timeseries/"+name, "starting_time")
    if val != 0.125:
        ut.error("Checking start time", "Incorrect value")
    val = ut.verify_attribute_present(fname, "acquisition/timeseries/starting_time/"+name, "rate")
    if val != 2:
        ut.error("Checking rate", "Incorrect value")

def create_startingtime_series(fname, name, target):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("starting time test")
    settings["mode"] = "w"
    settings["description"] = "time series starting time test"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
    #
#     stime = neurodata.create_timeseries("TimeSeries", name, target)
#     stime.set_data([0, 1, 2, 3], unit="n/a", conversion=1, resolution=1)
#     stime.set_value("num_samples", 4)
#     stime.set_time_by_rate(0.125, 2)
    #
    
    stime = f.make_group("<TimeSeries>", name, path=target)
    stime.set_dataset("data", [0.0, 1.0, 2.0, 3.0], attrs={"unit": "n/a",
        "conversion":1.0, "resolution": 1.0})
    stime.set_dataset("num_samples", 4)
    
    # stime.set_time_by_rate(0.125, 2)
    stime.set_dataset("starting_time", 0.125, attrs={ "rate":2.0, "unit":"Seconds"})
#     stime.finalize()
#     neurodata.close()
    f.close()

test_nodata_series()
print("%s PASSED" % __file__)

