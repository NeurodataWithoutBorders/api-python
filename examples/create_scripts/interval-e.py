#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as utils

"""
Create and store interval series

This is the same as example: interval.py, except that it uses
and extension (defined in extensions/e-interval.py) to add
a two new datasets:
 - "codes"
 - "code_descriptions"
to the IntervalSeries.  The codes data set lists the numeric codes used.
The "code_descriptions" data set, provides the description of each code.
"""
# create a new NWB file
OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"

settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = utils.create_identifier("extended interval example")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating use of an extended IntervalSeries"

# specify the extension (Could be more than one.  Only one used now).
settings['extensions'] = ["extensions/e-interval.py"]
f = nwb_file.open(**settings)


########################################################################
# Make some fake interval series data
# store in codes and times
event_codes = [
    7,  # 300 hz tone turned on at 
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

# create two arrays, one containing the codes, the other the corresponding
# descriptions
codes = [3, 4, 6, 7]
code_descriptions = ["blue light", "200 hz tone", "red light", "300 hz tone"]
    

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

# # Inside the group, create the data and timestamps datasets
g.set_dataset("data", event_codes)
g.set_dataset("timestamps", event_times)

# Now add the data sets defined in the extension
g.set_dataset("codes", codes)
g.set_dataset("code_descriptions", code_descriptions)


# All done.  Close the file
f.close()

