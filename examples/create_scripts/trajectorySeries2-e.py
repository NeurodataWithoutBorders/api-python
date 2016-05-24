#!/usr/bin/python 
import sys
import numpy as np
from nwb import nwb_file
from nwb import nwb_utils as utils

"""
Example of extending the format.

This example uses an extension specified in file "examples/e-trajectorySeries.py".
The extension specified in that file defines a new type of Timeseries
(named "TrajectorySeries", which stores the the trajectory of a hand
measured during a primate experiment with reaching behavior.

The trajectories are stored from four sensors and each sensor has
six degrees of freedom.

TrajectorySeries is an extension of the SpatialSeries. The
definition (i.e. extension) is in file extensions/e-trajectorySeries2.py.

This version specifies all the measurement units in advance in the extension.

"""
# create a new NWB file
OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"

settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = utils.create_identifier("trajectorySeries example")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating creating a new TimeSeries type using an extension"

# specify the extension (Could be more than one.  Only one used now).
settings['extensions'] = ["extensions/e-trajectorySeries2.py"]
f = nwb_file.open(**settings)


########################################################################
# Make some sample data

data = np.linspace(1., 100.0, 6*4*1000).reshape(24,1000)
times = np.linspace(0.0, 60.*2., 1000) 

# create an instance of MyNewTimeseries.  Name of group will be "my_new_timeseries
# it will be stored in /acquisition/timeseries

nts = f.make_group("<TrajectorySeries>", "hand_position", path="/acquisition/timeseries",
    attrs={"source": "source of data for my new timeseries"} )
nts.set_dataset("data", data, attrs={"conversion": 1.0, "resolution": 0.001, 
    "unit": "meter and radian; see definition of dimension trajectories in format specification"})
nts.set_dataset("timestamps", times)

# specify meaning of variables
reference_frame = ("Meaning of measurement values in array data, (e.g. sensor s1, s2, s3, s4; "
    "x, y, z, pitch, roll, yaw) should be described here")
nts.set_dataset("reference_frame", reference_frame)

# Add in sample epochs to specify the trials
trial_times = [ [0.5, 1.5], [2.5, 3.0], [3.5, 4.0]]

for trial_num in range(len(trial_times)):
    trial_name = "Trial_%03i" % (trial_num+1)
    start_time, stop_time = trial_times[trial_num]
    ep = utils.create_epoch(f, trial_name, start_time, stop_time)
    utils.add_epoch_ts(ep, start_time, stop_time, "hand_position", nts)


# All done.  Close the file
f.close()

