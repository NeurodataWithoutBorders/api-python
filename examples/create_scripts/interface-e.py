#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as utils

"""
Example extending the format: creating a new Interface.

This example uses two extensions defined in director "extensions"
  e-interface.py   - defines Interface extension
  e-timeseries.py  - defines a new timeseries type (MyNewTimeSeries)

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
settings["identifier"] = utils.create_identifier("MyNewInterface example")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating using a new Interface type using an extension"

# specify the extensions, two are used.
settings['extensions'] = ["extensions/e-timeseries.py", "extensions/e-interface.py"]
f = nwb_file.open(**settings)


########################################################################

# create a module for the interface

mod = f.make_group("<Module>", "my_module")

# create the interface inside the module

ig = mod.make_group("MyNewInterface", attrs={"source": "source of data for MyNewInterface"})


# set attribute and dataset in interface
ig.set_attr("foo", "MyNewInterface - foo attribute")
ig.set_dataset("bar", [1, 2, 3, 4, 5])


# Make some sample data for the MyNewTimeseries

data = [[1.2, 1.3, 1.4], [2.2, 2.3, 2.4], [3.2, 3.3, 3.4], [4.2, 4.3, 4.4], [5.2, 5.3, 5.4]]
times = [0.1, 0.2, 0.3, 0.4, 0.5]

# create the MyNewtimeseries inside the interface
nts = ig.make_group("<new_ts>", "my_new_ts", attrs={"source": "source of data for my_new_ts"})

nts.set_dataset("data", data, attrs={"conversion": 1.0, "resolution": 0.001, "unit": "--unit goes here--"})
nts.set_dataset("timestamps", times)

# specify metadata that is part of MyNewTimeSeries type
nts.set_attr("foo", "This added to attribute 'foo'")
nts.set_dataset("bar", [2, 4, 5, 6, 7])

# All done.  Close the file
f.close()

