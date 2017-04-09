#!/usr/bin/python
import sys
import numpy as np
from nwb import nwb_file
from nwb import nwb_utils as ut

""" 
Store the Salient Features of a Drifting Gratings Visual Stimulus

This example demonstrates how to use an AbstractFeatureSeries to store
data that can be summarized by certain high-level features, such as the 
salient features of a visual stimulus. The standard example of this is 
for drifting gratings -- the spatial frequency, orientation, phase, 
contrast and temporal frequency are the most important characteristics 
for analysis using drifting gratings, not necessarily the stack of all 
frames displayed by the graphics card.
"""

OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"
########################################################################
# create a new NWB file
# several settings are specified when doing so. these can be supplied within
#   the NWB constructor or defined in a dict, as in in this example
settings = {}
settings["file_name"] = OUTPUT_DIR + file_name

# each file should have a descriptive globally unique identifier 
#   that specifies the lab and this experiment session
# the function nwb_utils.create_identifier() is recommended to use as it takes
#   the string and appends the present date and time
settings["identifier"] = ut.create_identifier("abstract-feature example")

# indicate that it's OK to overwrite exting file.  The default mode
# ("w-") does not overwrite an existing file.
settings["mode"] = "w"

# specify the start time of the experiment. all times in the NWB file
#   are relative to experiment start time
# if the start time is not specified the present time will be used
settings["start_time"] = "Sat Jul 04 2015 3:14:16"

# provide one or two sentences that describe the experiment and what
#   data is in the file
settings["description"] = "Test file demonstrating use of the AbstractFeatureSeries"

# create the NWB File object. this manages the file
print("Creating " + settings["file_name"])
f = nwb_file.open(**settings)

########################################################################
# create an AbstractFeatureSeries
# this will be stored as a 'stimulus' in this example for this example. that
#   means that it will be stored in the following location in the hdf5
#   file: stimulus/presentation/

abs = f.make_group("<AbstractFeatureSeries>", "my_drifting_grating_features", path="/stimulus/presentation")
abs.set_attr("description", "This is a simulated visual stimulus that presents a moving grating")

# an AbstractFeatureSeries is an instance of a TimeSeries, with addition
#   of the following fields:
#       features -- describes the abstract features
#       feature_units -- the units that these features are measured in
# define the abstract features that we're storing, as well as the units
#   of those features (any number of features can be specified)
features = [ "orientation", "spatial frequency", "phase", "temporal frequency"]
units = [ "degrees", "Hz", "radians", "degrees"]
# store them
abs.set_dataset("features", features)
abs.set_dataset("feature_units", units)

# specify the source of the abstract features.  All TimeSeries types should have a
# source, description and comments specified; otherwise a warning is generated.
abs.set_attr("source", "Simulated data. Normally this would be the device presenting stimulus")

# create some pretend data
data = np.arange(4000, dtype=np.float32).reshape(1000, 4)

# add data to the time series. for now, ignore the last 3 parameters
t = np.arange(1000) * 0.001
abs.set_dataset("data", data)
abs.set_dataset("timestamps", t)


########################################################################
# it can sometimes be useful to import documenting data from a file
# in this case, we'll store this script in the metadata section of the
#   file, for a record of how the file was created
script_name = sys.argv[0]
f.set_dataset("source_script", ut.load_file(script_name), attrs= {
    "file_name": script_name})

# when all data is entered, close the file
f.close()


