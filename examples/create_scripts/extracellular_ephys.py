#!/usr/bin/python
import sys
import numpy as np
from nwb import nwb_file
from nwb import nwb_utils as ut

""" 
Store extracellular ephys data

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
settings["identifier"] = ut.create_identifier("extracellular ephys example")

# indicate that it's OK to overwrite exting file
settings["mode"] = "w"

# specify the start time of the experiment. all times in the NWB file
#   are relative to experiment start time
# if the start time is not specified the present time will be used
settings["start_time"] = "Sat Jul 04 2015 3:14:16"

# provide one or two sentences that describe the experiment and what
#   data is in the file
settings["description"] = "Test file demonstrating a simple extracellular ephys recording"

# create the NWB file object. this manages the file
print("Creating " + settings["file_name"])
f = nwb_file.open(**settings)

########################################################################
# create two electrical series, one with a single electrode and one with many
# then create a spike event series

# first describe the device(s).  Assume each probe is using a separate device
# names of devices are fictional
f.set_dataset("<device_X>", "Probe p0 device description", name="acme_model_23")
f.set_dataset("<device_X>", "Probe p1 device description", name="px_amp")

# create the electrode map
# example simulated recording is made from two 2-electrode probes named
#   'p0' and 'p1'. we need to define the locations of the electrodes
#   relative to each probe, and the location of the probes
# electrode coordinates are in meters and their positions 
#   are relative to each other. the location of the probe itself is
#   stored separately. using absolute coordinates here, if they are known, 
#   is still OK
electrode_map = [[0, 0, 0], [0, 1.5e-6, 0], [0, 0, 0], [0, 3.0e-5, 0]]
electrode_group = [ "p0", "p0", "p1", "p1" ]
#- neurodata.set_metadata(EXTRA_ELECTRODE_MAP, electrode_map)
#- neurodata.set_metadata(EXTRA_ELECTRODE_GROUP, electrode_group)

# make the group used to store extracellular ephys data.  This group
# will be created inside group /general
ex_ephys = f.make_group("extracellular_ephys")
# store the electrode_map and electrode_group inside the ex_ephys group
ex_ephys.set_dataset("electrode_map", electrode_map)
ex_ephys.set_dataset("electrode_group", electrode_group)
# set electrode impedances and describe filtering
# impedances are stored as text in case there is a range
ex_ephys.set_dataset("impedance", [ "1e6", "1.1e6", "1.2e6", "1.3e6" ])
ex_ephys.set_dataset("filtering", "description of filtering")

# specify the description, location and device for each probe
p0 = ex_ephys.make_group("<electrode_group_X>", "p0")
p0.set_dataset("description", "Description of p0")
p0.set_dataset("location", "CA1, left hemisphere, stereotactic coordinates xx, yy")
p0.set_dataset("device", "acme_model_23")
p1 = ex_ephys.make_group("<electrode_group_X>", "p1")
p1.set_dataset("description", "Description of p1")
p1.set_dataset("location", "CA3, left hemisphere, stereotactic coordinates xx, yy")
p1.set_dataset("device", "px_amp")


# define timestamp data (eg, 1 second at 10KHz)
timestamps = np.arange(10000) * 0.0001
# define data (here is all zeros -- real data will of course be different)
data = np.zeros(10000)

# the example is of two 2-electrode probes. the electrode data from these
#   probes can be stored individually, grouped as probes (eg, 2-electrode
#   pair) or all stored together. these approaches are all exampled here 

# create time series with single electrode
single = f.make_group("<ElectricalSeries>", "mono", path="/acquisition/timeseries")
single.set_attr("comments", "Data corresponds to recording from a single electrode")

# resolution is the magnitude distance between least-significant bits
#   (eg, volts-per-bit)
single.set_dataset("data", data, attrs={"resolution": 1.2345e-6})
times = single.set_dataset("timestamps", timestamps)

# indicate that we're recording from the first electrode defined in the
#   above map (electrode numbers start at zero, so electrodes are 
#   0, 1, 2 and 3
single.set_dataset("electrode_idx", [0])


########################################################################
# here is a time series storing data from a single probe (ie, 2 electrodes)
double = f.make_group("<ElectricalSeries>", "duo", path="/acquisition/timeseries")
double.set_attr("comments", "Data corresponds to two electrodes (one probe)")
double.set_dataset("data", np.zeros((10000, 2)), attrs={"resolution": 1.2345e-6})

# timestamps were already stored in the 'single' time series. we can link
#   to that instance, which saves space
double.set_dataset("timestamps", times)

# define the electrode mapping -- this is 'p0' which take slots 0 and 1
#   in the global electrode map
double.set_dataset("electrode_idx", [0, 1])


########################################################################
# here is a time series storing data from both probes together
quad = f.make_group("<ElectricalSeries>", "quad", path="/acquisition/timeseries")
quad.set_attr("comments", "Data corresponds to four electrodes (two probes)")
quad.set_dataset("data", np.zeros((10000, 4)), attrs={"resolution": 1.2345e-6})
quad.set_dataset("timestamps", times)
# indicate that we're recording from the first electrode defined in the
#   above map (electrode numbers start at zero, so electrodes are 
#   0, 1, 2 and 3
quad.set_dataset("electrode_idx", [0, 1, 2, 3])

# close file, otherwise it will fail to write properly
f.close()


