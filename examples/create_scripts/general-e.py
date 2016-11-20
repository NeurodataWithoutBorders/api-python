#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as utils

"""
Example using extension to add metadata to group /general

Group /general contains general metadata, i.e. metadata that
applies to the entire session.

This example uses the extension defined in extensions/e-general.py
to add new metadata to define then add new metadata to section
/general

"""
# create a new NWB file
OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"

settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = utils.create_identifier("add metadata to general")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating use of an extension for general"

# specify the extension (Could be more than one.  Only one used now).
settings['extensions'] = ["extensions/e-general.py"]
f = nwb_file.open(**settings)


########################################################################
# Specifier experimenter (this dataset is part of the core NWB format)
eds = f.set_dataset('experimenter', "Joseline Doe")

# specify attribute to experimenter, this defined in extension file.
# it is not part of the core NWB format
eds.set_attr("orcid_id", "7012023")

# Now add metadata that is defined by the extension
gri = f.make_group("rctn_info")
gri.set_dataset("seminars", ["Thom Smith", "Dwight Keenan", "Sue Trimble"])
gri.set_dataset("attendance", [23, 45, 33])
f.set_dataset("rctn:activity_level", '7')
f.set_dataset("rctn:time_since_fed", '6 hours 20 minutes')

f.set_dataset("notes", "some notes")

# also set extra metadata about subject
# these datasets are also defined in the extension
# dataset names and values are from a file in the AIBS cell types database
f.set_dataset("aibs_specimen_id",313862134)
f.set_dataset("aibs_specimen_name","Sst-IRES-Cre;Ai14(IVSCC)-167638.03.01.01")
f.set_dataset("aibs_dendrite_state","NA")
f.set_dataset("aibs_dendrite_type","aspiny")
f.set_dataset("aibs_cre_line","Sst-IRES-Cre")

# All done.  Close the file
f.close()

