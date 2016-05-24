#!/usr/bin/python
import sys
import numpy as np
from nwb import nwb_file
from nwb import nwb_utils as ut

""" 
An example of using the MotionCorrection interface

Modules and interfaces address intermediate processing of experimental
data. Intermediate processing is processing that's necessary to
convert the acquired data into a form that scientific analysis can
be performed on. In this example, that process is motion-correcting
an image. 

Processing and storing data in modules will typically be done
by people writing software that perform the processing tasks. The
software writer is free to store whatever additional data they wish
to store in a module. All that's required is the minimum data
required by each interface is included.

The MotionCorrection interface stores an unregistered image,
the xy translation necessary to motion-correct it, and the
corrected image. In this example, a time series storing 2-photon
image data is created, as if it were the original image coming
from a 2-photon microscope. Another time series is created that stores
the XY delta for each imaging frame necessary to correct for motion.
A third time series is created pointing to the corrected image.
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
settings["identifier"] = ut.create_identifier("motion correction example")

# indicate that it's OK to overwrite exting file
settings["mode"] = "w"

# specify the start time of the experiment. all times in the NWB file
#   are relative to experiment start time
# if the start time is not specified the present time will be used
settings["start_time"] = "Sat Jul 04 2015 3:14:16"

# provide one or two sentences that describe the experiment and what
#   data is in the file
settings["description"] = "Test file demonstrating use of the MotionCorrection interface"

# create the NWB file object. this manages the file
print("Creating " + settings["file_name"])
f = nwb_file.open(**settings)

########################################################################
# this is a sample optophysiology dataset storing simulated 2-photon
#   image stacks. these must refer to an imaging plane that's defined
#   in the general metadata section. define that metadata here
# 
# define the recording device
#- neurodata.set_metadata(DEVICE("Acme 2-photon microscope"), "Information about device goes here")
# declare information about a particular site and/or imaging plane
#- neurodata.set_metadata(IMAGE_SITE_EXCITATION_LAMBDA("camera1"), "1000 nm") 
#- neurodata.set_metadata(IMAGE_SITE_INDICATOR("camera1"), "GCaMP6s") 
#- neurodata.set_metadata(IMAGE_SITE_DEVICE("camera1"), "Acme 2-photon microscope") 

f.set_dataset("<device_X>", "Information about device goes here", name="Acme 2-photon microscope")
op = f.make_group("optophysiology")
c1 = op.make_group("<imaging_plane_X>", "camera1")
c1.set_dataset("device", "Acme 2-photon microscope")
c1.set_dataset("excitation_lambda", "1000 nm")
c1.set_dataset("indicator", "GCaMP6s")


########################################################################
# create different examples of image series
# image can be stored directly, for example by reading a .tif file into
#   memory and storing this data as a byte stream in data[]
# most(all?) examples here will have the time series reference data
#   that is stored externally in the file system

# first, a simple image. this could be a simple ImageSeries. in this
#   example we're using a TwoPhotonSeries, which is an ImageSeries
#   with some extra data fields
#- orig = neurodata.create_timeseries("TwoPhotonSeries", "source image", "acquisition")
#- orig.set_description("Pointer to a 640x480 image stored in the file system")
#- orig.set_source("Data acquired from Acme 2-photon microscope")
# assume the file is stored externally in the file system
#- orig.set_value("format", "external")
# specify the file
#- orig.set_value("external_file", "/path/to/file/stack.tif")
# information about the image
#- orig.set_value("bits_per_pixel", 16)
#- orig.set_value("dimension", [640, 480])

orig = f.make_group("<TwoPhotonSeries>", "source image", path="/acquisition/timeseries")
orig.set_attr("description", "Pointer to a 640x480 image stored in the file system")
orig.set_attr("source", "Data acquired from Acme 2-photon microscope")
orig.set_dataset("format", "external")
orig.set_dataset("external_file", ["/path/to/file/stack.tif"], attrs={
    "starting_frame": [0]})
orig.set_dataset("bits_per_pixel", 16)
orig.set_dataset("dimension", [640, 480])



###########################
# TwoPhoton-specific fields
#- orig.set_value("pmt_gain", 1.0)
# field of view is in meters
#- orig.set_value("field_of_view", [0.0003, 0.0003])
# imaging plane value is the site/imaging-plane defined as metadata above
#- orig.set_value("imaging_plane", "camera1")
#- orig.set_value("scan_line_rate", 16000)

orig.set_dataset("pmt_gain", 1.0)
orig.set_dataset("field_of_view", [0.0003, 0.0003])
orig.set_dataset("imaging_plane", "camera1")
orig.set_dataset("scan_line_rate", 16000)


###########################
# store time -- this example has 3 frames
#- orig.set_time([0, 1, 2])
# there's no data to store in the NWB file as the data is in an image
#   file in the file system
#- orig.ignore_data()
# when we ignore data, we must explicitly set number of samples (this is
#   otherwise handled automatically)
#- orig.set_value("num_samples", 3)
# this is simulated acquired data
# finish the time series so data is written to disk
#- orig.finalize()

orig_times = orig.set_dataset("timestamps", [0, 1, 2])
# orig.set_dataset("num_samples", 3)



# this example is for storing motion corrected 2-photon images
# store the pixel delta for each frame in the source stack
#- xy = neurodata.create_timeseries("TimeSeries", "x,y adjustments")
#- xy.set_description("X,Y adjustments to original image necessary for registration")
#- xy.set_data([[1.23, -3.45], [3.14, 2.18], [-4.2, 1.35]], unit="pixels", conversion=1, resolution=1)
#- xy.set_time_as_link(orig)
# setting time as link also requires setting number of samples manually 
#   FIXME
# if you try to create a time series and a required field is absent, the
#   API will give an error about the missing field (try commenting out 
#   the line set_data(), set_time() or set_value("num_samples") to see this
#   behavior in action
#- xy.set_value("num_samples", 3)
# 'xy' is motion corrected data and is part of the processing module
# module time series are finalized by the module interface that they're
#   added to, so don't do it here

mod = f.make_group("<Module>", "my module")
mc = mod.make_group("MotionCorrection")
mc.set_attr("source", orig.full_path)
is2 = mc.make_group("<image stack name>", "2photon")

xy = is2.make_group("xy_translation")
xy.set_attr("description", "X,Y adjustments to original image necessary for registration")
xy.set_dataset("data", [[1.23, -3.45], [3.14, 2.18], [-4.2, 1.35]], attrs={ "unit":"pixels", 
    "conversion":1.0, "resolution":1.0})
xy.set_dataset("timestamps", orig_times)

#- xy.set_time_as_link(orig)


# the module interface also stores the corrected image. assume that
#   it's in the file system too
# NOTE the corrected image timeseries is added to the interface through
#   the call add_corrected_image() below
#- corr = neurodata.create_timeseries("ImageSeries", "corrected_image")
#- corr.set_description("Corrected image")
#- corr.set_comments("Motion correction calculated manually in photoshop")
#- corr.set_value("format", "external")
#- corr.set_value("external_file", "/path/to/file/corrected_stack.tif")
#- corr.set_value("bits_per_pixel", 16)
#- corr.set_value("dimension", [640, 480])
#- corr.set_time_as_link(orig)
#- corr.set_value("num_samples", 3)
#- corr.ignore_data()
#corr.finalize()    DO NOT finalize -- interface takes care of this


corr = is2.make_group("corrected")
corr.set_attr("description", "Corrected image")
corr.set_attr("comments", "Motion correction calculated manually in photoshop")
corr.set_dataset("format", "external")
corr.set_dataset("external_file", ["/path/to/file/corrected_stack.tif"], attrs={
    "starting_frame": [0]})
corr.set_dataset("bits_per_pixel", 16)
corr.set_dataset("dimension", [640, 480])
corr.set_dataset("timestamps", orig_times)
#- corr.set_value("num_samples", 3)

# set link to original
is2.make_group("original", orig)

# create the module and MotionCorrection interface
#- mod = neurodata.create_module("my module")
# the module can store as many interfaces as we like. in this case we 
#   only have one. create it
#- iface = mod.create_interface("MotionCorrection")
# add the time series to the interface
#- iface.add_corrected_image("2photon", orig, xy, corr)
# the time series can be added by providing the python object or 
#   by specifying the paths to these objects, whichever is more
#   convenient. the following calls are equivalent:
#iface.add_corrected_image("2photon", orig.full_path(), xy.full_path(), corr)
#iface.add_corrected_image("2photon", orig, xy, corr.full_path())
#   as would be specifying the paths to the time series manually 
#   (eg, as stored in a variable)

# provide information in the interface about the source of the data
#- iface.set_source(orig.full_path())
# is set automatically in official API

#- iface.set_value("random comment", "Note that the 'original' field under 2photon is an HDF5 link to the time series '/acquisition/timeseries/source image'")
is2.set_custom_dataset("random comment", "Note that the 'original' field under 2photon is an HDF5 link to the time series '/acquisition/timeseries/source image'")


# finish off the interface
#- iface.finalize()

# finish off the module
#- mod.finalize()

# when all data is entered, close the file
#- neurodata.close()
f.close()

