#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as ut


"""
Create a module that stores experimental intervals

Modules represent intermediate processing of experimental data,
something that must be done to the acquired data before it is 
ready for experimental analysis. Processing examples are spike 
clustering (ephys) and image segmentation (ophys). 

In this example, a processing module is created that stores 
intervals marking a particular behavior, and it is assumed that
this behavior is only determinable by post-processing of acquired
data.
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
settings["identifier"] = ut.create_identifier("behavioral interval example")

# indicate that it's OK to overwrite exting file
settings["mode"] = "w"

# specify the start time of the experiment. all times in the NWB file
#   are relative to experiment start time
# if the start time is not specified the present time will be used
settings["start_time"] = "Sat Jul 04 2015 3:14:16"

# provide one or two sentences that describe the experiment and what
#   data is in the file
settings["description"] = "Test file demonstrating use of the BehavioralEpochs module interface"

# create the NWB file object. this manages the file
print("Creating " + settings["file_name"])
f = nwb_file.open(**settings)

########################################################################
# processed information is stored in modules, with each module publishing
#   one or more 'interfaces'. an interface is like a contract, promising
#   that the module will provide a specific and defined set of data.
# this module will publish 'BehavioralEpochs' interface, which promises
#   that it will publish IntervalSeries (a type of time series storing
#   experimental intervals)
#
# create the module
#- mod = neurodata.create_module("my behavioral module")
mod = f.make_group("<Module>", "my behavioral module")
mod.set_attr("description", "sample module that stores behavioral interval data")

# add an interface
if1 = mod.make_group("BehavioralEpochs")
if1.set_attr("source", "a description of the original data that these intervals were calculated from ")

# interval data is stored in an interval time series -- IntervalSeries
# create it
interval = if1.make_group("<IntervalSeries>", "intervals")
interval.set_attr("description", "Sample interval series -- two series are overlaid here, one with a code '1' and another with the code '2'")
interval.set_attr("comments", "For example, '1' represents sound on(+1)/off(-1) and '2' represents light on(+2)/off(-2)")
# create 
evts = [ 1, -1, 2, -2, 1, -1, 2, 1, -1, -2, 1, 2, -1, -2 ]
interval.set_dataset("data", evts)

# note: some timestamps will be duplicated if two different events start 
#   and/or stop at the same time
t = [ 1, 2, 2, 3, 5, 6, 6, 7, 8, 8, 10, 10, 11, 15 ]
interval.set_dataset("timestamps", t)

# multiple interfaces can be added to a module, and multiple time series
#   can be added to an interface using the same approach. this example
#   only imports one


########################################################################
# it can sometimes be useful to import documenting data from a file
# in this case, we'll store this script in the metadata section of the
#   file, for a record of how the file was created
script_name = sys.argv[0]
f.set_dataset("source_script", ut.load_file(script_name), attrs= {
    "file_name": script_name})

# when all data is entered, close the file
f.close()

