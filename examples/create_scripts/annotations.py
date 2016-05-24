#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as ut


"""
Create and store experiment annotations

Annotations are text strings that mark specific times in an 
experiment, for example "rat placed in enclosure" or "observed
start of seizure activity".
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
settings["identifier"] = ut.create_identifier("annotation example")

# indicate that it's OK to overwrite exting file
settings["mode"] = "w"

# specify the start time of the experiment. all times in the NWB file
#   are relative to experiment start time
# if the start time is not specified the present time will be used

settings["start_time"] = "Sat Jul 04 2015 3:14:16"
# provide one or two sentences that describe the experiment and what
#   data is in the file
settings["description"] = "Test file demonstrating use of the AbstractFeatureSeries"

# create the NWB file object. this manages the file
print("Creating " + settings["file_name"])
f = nwb_file.open(**settings)

########################################################################
# create an AnnotationSeries
# this will be stored in 'acquisiiton' as annotations are an
#   observation or a record of something else that happened.
# this means that it will be stored in the following location in the hdf5
#   file: acquisition/timeseries
annot = f.make_group("<AnnotationSeries>", "notes", path="/acquisition/timeseries")
annot.set_attr("description", "This is an AnnotationSeries with sample data")
annot.set_attr("comments", "The comment and description fields can store arbitrary human-readable data")
annot.set_attr("source", "Observation of Dr. J Doe")

# store pretend data
# all time is stored as seconds
andata = []
andata.append(("Rat in bed, beginning sleep 1", 15.0))
andata.append(("Rat placed in enclosure, start run 1", 933.0))
andata.append(("Rat taken out of enclosure, end run 1", 1456.0))
andata.append(("Rat in bed, start sleep 2", 1461.0))
andata.append(("Rat placed in enclosure, start run 2", 2401.0))
andata.append(("Rat taken out of enclosure, end run 2", 3210.0))
andata.append(("Rat in bed, start sleep 3", 3218.0))
andata.append(("End sleep 3", 4193.0))
# convert the data to an array of annotations and times
annotations = [x[0] for x in andata]
times = [x[1] for x in andata]
# store the annotations and times in the AnnotationSeries
annot.set_dataset("data",annotations)
annot.set_dataset("timestamps", times)

# Ignore this block.  these were used for testing external links
# annot.set_dataset("data", "extlink:unknown_data_file,/path/to/data")
# annot.set_dataset("timestamps", "extlink:unknown file2\t/path/t,o/timestamps")
# num_samples must be explicitly set
# annot.set_dataset("num_samples", 0)

########################################################################
# it can sometimes be useful to import documenting data from a file
# in this case, we'll store this script in the metadata section of the
#   file, for a record of how the file was created

script_name = sys.argv[0]
f.set_dataset("source_script", ut.load_file(script_name), attrs= {
    "file_name": script_name})

# when all data is entered, close the file
f.close()

