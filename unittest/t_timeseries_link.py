#!/usr/bin/python
# import nwb
import test_utils as ut

from nwb import nwb_file
from nwb import nwb_utils as utils


# create multiple time series and link data and timestamps to between them
# TESTS hard linking of TimeSeries.data
# TESTS linked value in TimeSeries.data
# TESTS annotation of TimeSeries.data link
# TESTS hard linking of TimeSeries.timestamps
# TESTS linked value in TimeSeries.timestamps
# TESTS annotation of TimeSeries.timestamps link


def test_ts_link():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    root = "root"
    create_linked_series(fname, root)
    ut.verify_timeseries(fname, root+"1", "stimulus/templates", "TimeSeries")
    ut.verify_timeseries(fname, root+"2", "stimulus/presentation", "TimeSeries")
    ut.verify_timeseries(fname, root+"3", "acquisition/timeseries", "TimeSeries")
    ##################################################
    # make sure data is present in ts using link
    val = ut.verify_present(fname, "stimulus/presentation/root2", "data")
    if val[0] != 1:
        ut.error("Checking link content", "Incorrect value")
    # make sure link is documented
    val = ut.verify_attribute_present(fname, "stimulus/presentation/root2", "data_link")
    if not ut.search_for_substring(val, "root1"):
        ut.error("Checking attribute data_link", "Name missing")
    if not ut.search_for_substring(val, "root2"):
        ut.error("Checking attribute data_link", "Name missing")
    val = ut.verify_attribute_present(fname, "stimulus/templates/root1", "data_link")
    if not ut.search_for_substring(val, "root1"):
        ut.error("Checking attribute data_link", "Name missing")
    if not ut.search_for_substring(val, "root2"):
        ut.error("Checking attribute data_link", "Name missing")
    ##################################################
    # make sure timestamps is present in ts using link
    val = ut.verify_present(fname, "acquisition/timeseries/root3", "timestamps")
    if val[0] != 2:
        ut.error("Checking link content", "Incorrect value")
    # make sure link is documented
    val = ut.verify_attribute_present(fname, "stimulus/presentation/root2", "timestamp_link")
    if not ut.search_for_substring(val, "root2"):
        ut.error("Checking attribute timestamp_link", "Name missing")
    if not ut.search_for_substring(val, "root3"):
        ut.error("Checking attribute timestamp_link", "Name missing")
    val = ut.verify_attribute_present(fname, "acquisition/timeseries/root3", "timestamp_link")
    if not ut.search_for_substring(val, "root2"):
        ut.error("Checking attribute timestamp_link", "Name missing")
    if not ut.search_for_substring(val, "root3"):
        ut.error("Checking attribute timestamp_link", "Name missing")

def create_linked_series(fname, root):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("link test")
    settings["mode"] = "w"
    settings["description"] = "time series link test"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["verbosity"] = "none"
    # neurodata = nwb.NWB(**settings)
    f = nwb_file.open(**settings)
    #
#     first = neurodata.create_timeseries("TimeSeries", root+"1", "template")
#     first.ignore_time()
#     first.set_value("num_samples", 1)
#     first.set_data([1], unit="parsec", conversion=1, resolution=1e-12)
#     first.finalize()
    #
    
    first = f.make_group("<TimeSeries>", root+"1", path="/stimulus/templates")
    # first.ignore_time()
    # first.set_value("num_samples", 1)
    first.set_dataset("num_samples", 1)
    d1 = first.set_dataset("data", [1.0], attrs={"unit":"parsec", "conversion":1.0,
        "resolution":1e-12})
    # first.finalize()
    
#     second = neurodata.create_timeseries("TimeSeries", root+"2", "stimulus")
#     second.set_time([2])
#     second.set_value("num_samples", 1)
#     second.set_data_as_link(first)
#     second.finalize()
    #
    
    second = f.make_group("<TimeSeries>", root+"2", path="/stimulus/presentation")
    t2 = second.set_dataset("timestamps", [2.0])
    second.set_dataset("num_samples", 1)
    second.set_dataset("data", d1)    
    
#     third = neurodata.create_timeseries("TimeSeries", root+"3", "acquisition")
#     third.set_time_as_link(second)
#     third.set_value("num_samples", 1)
#     third.set_data([3], unit="parsec", conversion=1, resolution=1e-9)
#     third.finalize()

    third = f.make_group("<TimeSeries>", root+"3", path="/acquisition/timeseries")
    third.set_dataset("timestamps", t2)
    third.set_dataset("num_samples", 1)
    third.set_dataset("data", [3.0], attrs={"unit":"parsec", "conversion":1.0,
        "resolution":1e-9})

    #
    # neurodata.close()
    f.close()

test_ts_link()
print("%s PASSED" % __file__)

