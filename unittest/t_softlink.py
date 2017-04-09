#!/usr/bin/python
import sys
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils

# creates time series without 'data' field
# TESTS softlink of TimeSeries.data

def test_softlink():
    if __file__.startswith("./"):
        fname1 = "s" + __file__[3:-3] + "1" + ".nwb"
        fname2 = "s" + __file__[3:-3] + "2" + ".nwb"
    else:
        fname1 = "s" + __file__[1:-3] + "1" + ".nwb"
        fname2 = "s" + __file__[1:-3] + "2" + ".nwb"
    name1 = "softlink_source"
    name2 = "softlink_reader"
#     create_softlink_source(fname1, name1, "acquisition")
#     create_softlink_reader(fname2, name2, fname1, name1, "acquisition")
    create_softlink_source(fname1, name1, "/acquisition/timeseries")
    create_softlink_reader(fname2, name2, fname1, name1, "/acquisition/timeseries")
    #
    ut.verify_timeseries(fname1, name1, "acquisition/timeseries", "TimeSeries")
    ut.verify_timeseries(fname2, name2, "acquisition/timeseries", "TimeSeries")
    ##
    val = ut.verify_present(fname2, "acquisition/timeseries/"+name2, "data")

def create_softlink_reader(fname, name, src_fname, src_name, target):
    settings = {}
    settings["file_name"] = fname
    settings["start_time"] = "2008-09-15T15:53:00-08:00"
    settings["identifier"] = utils.create_identifier("softlink reader")
    settings["mode"] = "w"
    settings["description"] = "softlink test"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    
#     source = neurodata.create_timeseries("TimeSeries", name, target)
#     source.set_data_as_remote_link(src_fname, "acquisition/timeseries/"+src_name+"/data")
#     source.set_time([345])
#     source.finalize()
#     neurodata.close()
    
    source = f.make_group("<TimeSeries>", name, path=target)
    # source.set_data_as_remote_link(src_fname, "acquisition/timeseries/"+src_name+"/data")
    extlink = "extlink:%s,%s" % (src_fname, "acquisition/timeseries/"+src_name+"/data")
    source.set_dataset("data", extlink)
    source.set_dataset("timestamps", [345])
#     source.finalize()
#     neurodata.close()
    f.close()

def create_softlink_source(fname, name, target):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("softlink source")
    settings["mode"] = "w"
    settings["description"] = "time series no data test"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["verbosity"] = "none"
    f = nwb_file.open(**settings)
    # source = neurodata.create_timeseries("TimeSeries", name, target)
    source = f.make_group("<TimeSeries>", name, path=target)
    # source.set_data([234], unit="parsec", conversion=1.0, resolution=1e-3)
    source.set_dataset("data", [234.0], attrs={"unit":"parsec", 
        "conversion":1.0, "resolution":1e-3})
    # source.set_time([123])
    source.set_dataset("timestamps", [123.0])
    # source.finalize()
    # neurodata.close()
    f.close()

test_softlink()
print("%s PASSED" % __file__)

