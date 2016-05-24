#!/usr/bin/python
import sys
from nwb import nwb_file
from nwb import nwb_utils as utils

"""
Example extending the format: adding metadata to intracellular recording data.

This example uses an extension to add metadata to time series storing
intracellular data.  Specifically, metadata fields are added to data types:
<VoltageClampSeries>/
<CurrentClampSeries>/
/stimulus/presentation/<CurrentClampStimulusSeries>/
/stimulus/presentation/<VoltageClampStimulusSeries>/

Metadata added to the later two are "anchored" to the location
"/stimulus/presentation/", which means that the metadata is added
to the <CurrentClampStimulusSeries>/ and /<VoltageClampStimulusSeries>/
located at /stimulus/presentation/, but not to those located elsewhere,
such as: /stimulus/templates/.

This example is based on metadata stored in the Allen Institute Cell Types
database NWB files.

"""
# create a new NWB file
OUTPUT_DIR = "../created_nwb_files/"
file_name = __file__[0:-3] + ".nwb"

settings = {}
settings["file_name"] = OUTPUT_DIR + file_name
settings["identifier"] = utils.create_identifier("MyNewInterface example")
settings["mode"] = "w"
settings["start_time"] = "2016-04-07T03:16:03.604121"
settings["description"] = "Test file demonstrating storing metadata for intracellular data using an extension"

# specify the extensions, two are used.
settings['extensions'] = ["extensions/e-intracellular.py"]
f = nwb_file.open(**settings)


########################################################################

# Store some example <CurrentClampSeries>/ in /acquisition/timeseries

# sample sweep data, use same data for all
data = [0.77, 0.77, 0.78, 0.77, 0.79, 0.75]
start_time = 1792.0
for i in range(1, 6):
    sweep_name = "Sweep_%03i" % i
    ccs = f.make_group("<CurrentClampSeries>",sweep_name, path="/acquisition/timeseries")
    # set normal metadata
    ccs.set_dataset("data", data, attrs={"conversion": 0.0010,
        "resolution": 0.0, "unit":"volt"})
    ccs.set_dataset("starting_time", start_time + i, attrs=
        {"rate": 200000.0, "unit": "second"})
    ccs.set_dataset("num_samples", len(data))
    ccs.set_dataset("bias_current",-3.4973694E-11)
    ccs.set_dataset("bridge_balance",1.0744811E7)
    ccs.set_dataset("capacitance_compensation",2.0002682E-12)
    ccs.set_dataset("electrode_name", "/general/intracellular_ephys/Electrode 1")
    ccs.set_dataset("gain",0.01)
    # ccs.set_dataset("initial_access_resistance",1.8170208E7)
    # ccs.set_dataset("seal",1.05968704E9)
    # set extension metadata
    ccs.set_dataset("aibs_stimulus_amplitude_pa",350.0)
    ccs.set_dataset("aibs_stimulus_description", "C2SSHM80FN141203[0]x3.5")
    ccs.set_dataset("aibs_stimulus_interval", 0.0)
    ccs.set_dataset("aibs_stimulus_name", "Short Square - Hold -80mV")

# Store some example <VoltageClampSeries>/ in /acquisition/timeseries

for i in range(6,10):
    sweep_name = "Sweep_%03i" % i
    ccs = f.make_group("<VoltageClampSeries>",sweep_name, path="/acquisition/timeseries")
    # set normal metadata
    ccs.set_dataset("data", data, attrs={"conversion": 0.0010,
        "resolution": 0.0, "unit":"amp"})
    ccs.set_dataset("starting_time", start_time + i, attrs=
        {"rate": 200000.0, "unit": "second"})
    ccs.set_dataset("num_samples", len(data))
    ccs.set_dataset("capacitance_fast",0.0)
    ccs.set_dataset("capacitance_slow",0.0)
    ccs.set_dataset("electrode_name", "/general/intracellular_ephys/Electrode 1")
    ccs.set_dataset("gain",0.01)
    # ccs.set_dataset("initial_access_resistance",1.8170208E7)
    ccs.set_dataset("resistance_comp_bandwidth",0.0)
    ccs.set_dataset("resistance_comp_correction",0.0)
    ccs.set_dataset("resistance_comp_prediction",0.0) 
    ccs.set_dataset("whole_cell_capacitance_comp", 0.0)
    ccs.set_dataset("whole_cell_series_resistance_comp", 0.0)
    # ccs.set_dataset("seal",1.05968704E9)
    # set extension metadata
    ccs.set_dataset("aibs_stimulus_amplitude_mv",10.0)
    ccs.set_dataset("aibs_stimulus_description", "EXTPCllATT141203[0]x1.0")
    ccs.set_dataset("aibs_stimulus_interval", 0.05)
    ccs.set_dataset("aibs_stimulus_name", "Test")
   

# store some example <CurrentClampStimulusSeries>/ in /stimulus/presentation/

for i in range(1,6):
    sweep_name = "Sweep_%03i" % i
    ccs = f.make_group("<CurrentClampStimulusSeries>",sweep_name, path="/stimulus/presentation")
    # set normal metadata
    ccs.set_dataset("data", data, attrs={"conversion": 0.0010,
        "resolution": 0.0, "unit":"amp"})
    ccs.set_dataset("starting_time", start_time + i, attrs=
        {"rate": 200000.0, "unit": "second"})
    ccs.set_dataset("num_samples", len(data))
    ccs.set_dataset("electrode_name", "/general/intracellular_ephys/Electrode 1")
    ccs.set_dataset("gain",0.01)
    # ccs.set_dataset("initial_access_resistance",1.8170208E7)
    # ccs.set_dataset("seal",1.05968704E9)
    # set extension metadata
    ccs.set_dataset("aibs_stimulus_amplitude_pa",350.0)
    ccs.set_dataset("aibs_stimulus_description", "C2SSHM80FN141203[0]x3.5")
    ccs.set_dataset("aibs_stimulus_interval", 0.0)
    ccs.set_dataset("aibs_stimulus_name", "Long Square")

# store some example <VoltageClampStimulusSeries>/ in /stimulus/presentation/

for i in range(6,10):
    sweep_name = "Sweep_%03i" % i
    ccs = f.make_group("<VoltageClampStimulusSeries>",sweep_name, path="/stimulus/presentation")
    # set normal metadata
    ccs.set_dataset("data", data, attrs={"conversion": 0.0010,
        "resolution": 0.0, "unit":"volt"})
    ccs.set_dataset("starting_time", start_time + i, attrs=
        {"rate": 200000.0, "unit": "second"})
    ccs.set_dataset("num_samples", len(data))
    ccs.set_dataset("electrode_name", "/general/intracellular_ephys/Electrode 1")
    ccs.set_dataset("gain",0.01)
    # ccs.set_dataset("initial_access_resistance",1.8170208E7)
    # ccs.set_dataset("seal",1.05968704E9)
    # set extension metadata
    ccs.set_dataset("aibs_stimulus_amplitude_mv",10.0)
    ccs.set_dataset("aibs_stimulus_description", "EXTPCllATT141203[0]x1.0")
    ccs.set_dataset("aibs_stimulus_interval", 0.05)
    ccs.set_dataset("aibs_stimulus_name", "Test")

# All done.  Close the file
f.close()

