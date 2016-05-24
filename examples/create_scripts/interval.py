#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as ut

"""
Create and store interval series

Intervals in the data can be efficiently stored using the NWB IntervalSeries.

The timestamps field stores the beginning and end of intervals.
The data field stores whether the interval just started (>0 value) 
or ended (<0 value). Different interval types can be represented in the 
same series by using multiple key values (eg, 1 for feature A, 
2 for feature B, 3 for feature C, etc). The field data stores an 8-bit integer.
This is largely an alias of a standard TimeSeries but that is identifiable as
representing time intervals in a machine-readable way.
"""

# create a new NWB file
OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"
settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = ut.create_identifier("interval example")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating use of the IntervalSeries"
f = nwb_file.open(**settings)


########################################################################
# Make some fake interval series data
# store in codes and times
event_codes = [
    7,  # 300 hz tone turned on
    -7, # 300 hz tone turned off
    3,  # blue light turned on
    4,  # 200 hz tone turned on
    6,  # red light turned on
    -3, # blue light turned off
    -6, # red light turned off
    -4  # 200 hz tone turned off
    ]
# times - interval times (in seconds) corresponding to above codes
event_times = [1.1, 2.3, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8] 

########################################################################
# create an IntervalSeries
# All time series created at the "top level" in the file (e.g. not inside
# a defined structure in the format specification) are stored in
# one of three locations:
# /stimulus/presentation   - for presented stimuli data
# /stimulus/templates      - for templates for stimuli
# /acquisition/timeseries  - for acquired data  
#
# Store this interval series in /stimulus/presentation
# that is specified by the 'path' parameter in the call below

# create the group for the IntervalSeries.  Call returns group object
g = f.make_group("<IntervalSeries>", "tone_times", path="/stimulus/presentation")
g.set_attr("description", "Times for tone turning on/off.  data codes positive for on, negative for off")

# # Inside the group, create the data and timestamps datasets
g.set_dataset("data", event_codes)
g.set_dataset("timestamps", event_times)


# All done.  Close the file
f.close()

