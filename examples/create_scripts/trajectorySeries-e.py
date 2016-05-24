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

TrajectorySeries is an extension of the SpatialSeries.  The
definition (i.e. extension) is in file extensions/e-trajectorySeries.py.

This version uses datasets to specify the measurement names and values.
(These could also be specified as text using the SpatialSeries reference_frame,
dataset, but not in a defined, machine readable way).


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
settings['extensions'] = ["extensions/e-trajectorySeries.py"]
f = nwb_file.open(**settings)


########################################################################
# Make some sample data for the foo_timeseries

data = np.linspace(1., 100.0, 6*4*1000).reshape(24,1000)
times = np.linspace(0.0, 60.*2., 1000) 

# create an instance of MyNewTimeseries.  Name of group will be "my_new_timeseries
# it will be stored in /acquisition/timeseries

nts = f.make_group("<TrajectorySeries>", "hand_position", path="/acquisition/timeseries",
    attrs={"source": "source of data for my new timeseries"} )
nts.set_dataset("data", data, attrs={"conversion": 1.0, "resolution": 0.001, "unit": "see measurements"})
nts.set_dataset("timestamps", times)

# specify metadata that is part of MyNewTimeSeries type
measurement_names = ["s1_x", "s1_y", "s1_z", "s1_r", "s1_t", "s1_o",
    "s2_x", "s2_y", "s2_z", "s2_r", "s2_t", "s2_o",
    "s3_x", "s3_y", "s3_z", "s3_r", "s3_t", "s3_o"]

nts.set_attr("measurement_names", measurement_names)
measurement_units = ["meter", "meter", "meter", "radian", "radian", "radian",
    "meter", "meter", "meter", "radian", "radian", "radian",
    "meter", "meter", "meter", "radian", "radian", "radian"]

nts.set_attr("measurement_units", measurement_units)

# All done.  Close the file
f.close()

