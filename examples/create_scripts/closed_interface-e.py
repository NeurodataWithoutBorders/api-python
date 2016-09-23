#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as utils

"""
Example extending the format: using new Interface which is specified
to be "closed" (does not allow any additional members).

The extension is specified in file "extensions/e-closed_interface.py".

The convention of having "e-" in front of the extension (and "-e" at the
end of the create script name) is only used for these examples.  Any name for the
create script and extension(s) can be used as long as the actual name of the
extension(s) are referenced by the create script and passed as parameters to
nwb_validate.py when validating NWB files created using one or more extensions.


"""
# create a new NWB file
OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"

settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = utils.create_identifier("MyClosedInterface example")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating using a new Interface which is closed"

# specify the extension
settings['extensions'] = ["extensions/e-closed_interface.py"]
f = nwb_file.open(**settings)


########################################################################

# create a module for the interface

mod = f.make_group("<Module>", "my_module")

# create the interface inside the module

ig = mod.make_group("MyClosedInterface", attrs={"source": "source of data for MyClosedInterface"})


# set attribute and dataset in interface
ig.set_attr("foo", "MyClosedInterface - foo attribute")
ig.set_dataset("bar", [1, 2, 3, 4, 5])

# add an additional data set.  This should generate an error on validation
ig.set_custom_dataset("baz", [4, 6, 7, 9])

# All done.  Close the file
f.close()

