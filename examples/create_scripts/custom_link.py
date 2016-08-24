#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as ut


"""
Test making a custom link to TimeSeries::data
"""


OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"
########################################################################
# create a new NWB file
# several settings are specified when doing so. these can be supplied within
#   the NWB constructor or defined in a dict, as in in this example
settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = ut.create_identifier("custom link example")
settings["mode"] = "w"
settings["start_time"] = "Aug 24, 2016"
settings["description"] = "Test creating custom link to TimeSeries::data"
f = nwb_file.open(**settings)

rss = f.make_group("<SpatialSeries>", "rat_position", path='/acquisition/timeseries')
rss_data = rss.set_dataset('data', [1.1, 1.2], attrs= {
    "conversion":1.0, "resolution":1.0, "unit":"meter"} )
rss.set_dataset('timestamps', [0.1, 0.2])

# make custom group
ag = f.make_group("analysis")
cg = ag.make_custom_group("lab_data")
ld = cg.set_custom_dataset("rat_position_data_link", rss_data)
f.close()

