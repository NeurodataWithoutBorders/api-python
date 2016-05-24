#!/usr/bin/env python
# encoding: utf-8

import sys 
import os

from nwb import nwb_file
from nwb import nwb_utils as ut

import h5py
import datetime
import getpass
import numpy as np
from sets import Set

# paths to source files
SOURCE_DATA_DIR = "../source_data/crcns_alm-1/"
INFILE = SOURCE_DATA_DIR + "data_structure_NL_example20140905_ANM219037_20131117.h5"
META = SOURCE_DATA_DIR + "meta_data_NL_example20140905_ANM219037_20131117.h5"

if not os.path.exists(INFILE) or not os.path.exists(META):
    print "Source files for script '%s' not present" % os.path.basename(__file__)
    print "Download and put them in the 'examples/source_data' directory as instructed"
    print "in file examples/0_README.txt"
    sys.exit(1) 


OUTPUT_DIR = "../created_nwb_files/crcns_alm-1/"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def find_exp_time(ifile):
    d = ifile['dateOfExperiment']["dateOfExperiment"].value[0]
    t = ifile['timeOfExperiment']["timeOfExperiment"].value[0]
    dt=datetime.datetime.strptime(d+t, "%Y%m%d%H%M%S")
    return dt.strftime("%a %b %d %Y %H:%M:%S")

def check_entry(file_name,obj):
    try:
        return file_name[obj]
    except KeyError:
        print str(obj) +" does not exist"
        return []

def parse_h5_obj(obj, level = 0, output = []):
    if level == 0:
        output = []
    try:
        if isinstance(obj, h5py.highlevel.Dataset):
            level = level+1
            if obj.value.any():
                output.append(obj.value)
            else:
                full_name = obj.name.split("/")
                output.append(full_name[-1])
        elif isinstance(obj, h5py.highlevel.Group):
            level = level+1
            if not obj.keys():
                output.append([])
            else:
                for key in obj.keys():
                    parse_h5_obj(obj[key], level, output)
        else:
            output.append([])
    except KeyError:
        print "Can't find" + str(obj)
        output.append([])
    return output


# initialize trials with basic fields and behavioral data    
def create_trials(orig_h5, nuo):
    trial_id = orig_h5["trialIds/trialIds"].value
    trial_t = orig_h5["trialStartTimes/trialStartTimes"].value
    good_trials = orig_h5['trialPropertiesHash/value/4/4'].value
    ignore_ivals_start = [time for (time, good_trial) in zip(trial_t,good_trials) if good_trial == 0]
    # trial stop isn't stored. assume that it's twice the duration of other
    #   trials -- padding on the high side shouldn't matter
    ival = (trial_t[-1] - trial_t[0]) / (len(trial_t) - 1)
    trial_t = np.append(trial_t, trial_t[-1] + 2*ival)
    ignore_ivals_stop = [time for (time, good_trial) in zip(trial_t[1:],good_trials) if good_trial == 0]
    ignore_intervals = [ignore_ivals_start, ignore_ivals_stop]
    # for i in range(10):  # version for only five epoch's to reduce time
    for i in range(len(trial_id)):  # use: in range(5): to reduce run time
        tid = trial_id[i]
        trial = "Trial_%d%d%d" % (int(tid/100), int(tid/10)%10, tid%10)
        # print trial # DEBUG
        start = trial_t[i]
        stop = trial_t[i+1]
        epoch = ut.create_epoch(nuo, trial, start, stop)
        tags = []
        if good_trials[i] == 0:
            tags.append("Good trial")
        else:
            tags.append("Non-performing")
        for j in range(len(epoch_tags[trial])):
            tags.append(epoch_tags[trial][j])
        epoch.set_dataset("tags", tags)
        # keep with tradition and create a units field, even if it's empty
        if trial not in epoch_units:
            units = []
        else:
            units = epoch_units[trial]
        epoch.set_custom_dataset("units", units)
        # raw data path
        raw_path = "descrHash/value/%d" % (trial_id[i])
        # try:
        raw_file = parse_h5_obj(orig_h5[raw_path])[0]
        if len(raw_file) == 1:
            raw_file = 'na'
        else:
            raw_file = str(raw_file)
        # except KeyError:
        #         raw_path = "descrHash/value/%d/" %(trial_id[i])
        #         try:
        #             raw_file_1 = parse_h5_obj(orig_h5[raw_path + "/1"])[0]
        #         except IndexError:
        #             raw_file_1 = ''
        #         try:
        #             raw_file_2 = parse_h5_obj(orig_h5[raw_path + "/2"])[0]
        #         except IndexError:
        #             raw_file_2 = ''
        #         raw_file = str(raw_file_1) + " and " + str(raw_file_2)
        #     except IndexError:
        #         raw_file = ''
        epoch.set_dataset("description", "Raw Voltage trace data files used to acuqire spike times data: " + raw_file + "\n\
ignore intervals: mark start and stop times of bad trials when mice are not performing")
        #epoch.set_ignore_intervals(ignore_intervals)
        # collect behavioral data
        ts = "/stimulus/presentation/auditory_cue"
        ut.add_epoch_ts(epoch, start, stop, "auditory_cue", ts)
        ts = "/stimulus/presentation/pole_in"
        ut.add_epoch_ts(epoch, start, stop, "pole_in", ts)
        ts = "/stimulus/presentation/pole_out"
        ut.add_epoch_ts(epoch, start, stop, "pole_out", ts)
        ts = "/acquisition/timeseries/lick_trace"
        ut.add_epoch_ts(epoch, start, stop,"lick_trace", ts)
        ts = "/stimulus/presentation/aom_input_trace"
        ut.add_epoch_ts(epoch, start, stop,"aom_input_trace", ts)
        ts = "/stimulus/presentation/simple_optogentic_stimuli"
        #ts = "/stimulus/presentation/laser_power"
# DEBUG -- don't add this right now -- too many smaples make building file take too long
        #epoch.add_timeseries("laser_power", ts)
        ut.add_epoch_ts(epoch, start, stop, "simple_optogentic_stimuli", ts)
        # TODO epoch.add_ignore_intervals(...)
        # epoch.finalize()

# add trial types to epoch for indexing
epoch_tags = {}
def get_trial_types(orig_h5, nuo):
    # fp = nuo.file_pointer
    trial_id = orig_h5["trialIds/trialIds"].value
    trial_types_all = []
    trial_type_strings = parse_h5_obj(orig_h5['trialTypeStr'])[0]
    photostim_types = parse_h5_obj(orig_h5['trialPropertiesHash/value/5'])[0]
    # collect all trials (strings)
    for i in range(8):
        trial_types_all.append(str(trial_type_strings[i]))
    # write specific entries for the given trial
    for i in range(len(trial_id)):
        tid = trial_id[i]
        trial_name = "Trial_%d%d%d" % (int(tid/100), int(tid/10)%10, tid%10)
        epoch_tags[trial_name] = []
        trial_types = []
        trial_type_mat = parse_h5_obj(orig_h5['trialTypeMat'])[0]
        for j in range(8):
            if trial_type_mat[j,i] == 1:
                epoch_tags[trial_name].append(trial_types_all[j])
                #trial_types.append(trial_types_all[j])
        ps_type_value = photostim_types[i]
        if ps_type_value == 0:
            photostim_type = "non-stimulation trial"
        elif ps_type_value == 1:
            photostim_type = "PT axonal stimulation"
        elif ps_type_value == 2:
            photostim_type = "IT axonal stimulation"
        else:
            photostim_type = "discard"
        epoch_tags[trial_name].append(photostim_type)


# collect unit information for a given trial        
epoch_units = {}
def get_trial_units(orig_h5, nuo, unit_num):
    # fp = nuo.file_pointer
    for i in range(unit_num):
        i = i+1
        unit = "unit_%d%d" % (int(i/10), i%10)
        grp_name = "eventSeriesHash/value/%d" % i
        grp_top_folder = orig_h5[grp_name]
        trial_ids = grp_top_folder["eventTrials/eventTrials"].value
        trial_ids = Set(trial_ids)
        for trial_num in trial_ids:
            tid = trial_num
            trial_name = "Trial_%d%d%d" % (int(tid/100), int(tid/10)%10, tid%10)
            if trial_name not in epoch_units:
                epoch_units[trial_name] = []
            epoch_units[trial_name].append(unit)


###########################################################################
###########################################################################
###########################################################################

#ep.ts_self_check()
#sys.exit(0)

# prepare files
orig_h5 = h5py.File(INFILE, "r")
meta_h5 = h5py.File(META, "r")
ifile_name = INFILE.split('/')[-1]
session_id = ifile_name[15:-3]
bfile_name = ifile_name[15:-3] + ".nwb"
vargs = {}
vargs["start_time"] = find_exp_time(meta_h5)
vargs["identifier"] = ut.create_identifier(session_id)
vargs["mode"] = "w"
vargs["description"] = "Extracellular ephys recording of mouse doing discrimination task (lick left/right), with optogenetic stimulation plus pole and auditory stimulus"
vargs["file_name"] = OUTPUT_DIR + bfile_name
nuo = nwb_file.open(**vargs)

nuo.set_dataset("session_id", session_id)
print "Reading meta data"
#general
an_gene_copy = parse_h5_obj(meta_h5["animalGeneCopy"])[0][0]
an_gene_bg= parse_h5_obj(meta_h5["animalGeneticBackground"])[0]
an_gene_mod = parse_h5_obj(meta_h5["animalGeneticBackground"])[0]
an_gene = "Animal gene modification: " + an_gene_mod +\
";\nAnimal genetic background: " + an_gene_bg +\
";\nAnimal gene copy: " + str(an_gene_copy)
gg = nuo.make_group("general", abort=False)
s = gg.make_group('subject')
s.set_dataset("genotype", an_gene)  # jt - did require str
an_strain = parse_h5_obj(meta_h5["animalStrain"])[0]
an_source = parse_h5_obj(meta_h5["animalSource"])[0]
date_of_birth = meta_h5["dateOfBirth"]["dateOfBirth"].value
subject = "Animal Strain: " + an_strain + \
";\nAnimal source: " + an_source + \
";\nDate of birth: " + date_of_birth
nuo.set_dataset("description", subject)  # jt - did require str
citation = parse_h5_obj(meta_h5["citation"])[0]
nuo.set_dataset('related_publications', citation)
exp_type = map(str, parse_h5_obj(meta_h5["experimentType"])[0])
exp_type_desc = "Experiment type: "
for i in range(len(exp_type)):
    exp_type_desc += exp_type[i] + ", "
exp_type_desc = exp_type_desc[:-2]  # strip out last ", "
nuo.set_dataset('notes', exp_type_desc)
experimenters = parse_h5_obj(meta_h5["experimenters"])[0]
nuo.set_dataset('experimenter', experimenters)
ref_atlas = parse_h5_obj(meta_h5["referenceAtlas"])[0]
nuo.set_custom_dataset("reference_atlas", ref_atlas)
sex = parse_h5_obj(meta_h5["sex"])[0]
s.set_dataset("sex", sex)
s.set_dataset("age", ">P60")
species = parse_h5_obj(meta_h5["species"])[0]
s.set_dataset("species", species)
#surgical_man = meta_h5["surgicalManipulation"]["surgicalManipulation"].value
gg.set_dataset("surgery", ut.load_file(SOURCE_DATA_DIR + "surgery.txt"))
gg.set_dataset("data_collection", ut.load_file(SOURCE_DATA_DIR + "data_collection.txt"))
gg.set_dataset("experiment_description", ut.load_file(SOURCE_DATA_DIR + "experiment_description.txt"))
#nuo.set_dataset("surgery", surgical_man)
#weight_after = meta_h5["weightAfter"].value
#weight_before = meta_h5["weightBefore"].value
#weight = "Weight after: " + weight_after +\
# "; weight before: " + weight_before
# metadata file incomplete here. pulled data from pdf file
s.set_dataset("weight", "Before: 20, After: 21")
whisker_config = parse_h5_obj(meta_h5["whiskerConfig"])[0]
nuo.set_custom_dataset("whisker_configuration", whisker_config)

probe = []
sites = parse_h5_obj(check_entry(meta_h5, "extracellular/siteLocations"))
assert len(sites) == 32, "Expected 32 electrode locations, found %d"%len(sites)
for i in range(len(sites)):
    probe.append(sites[i])
    probe[-1] = probe[-1] * 1.0e-6
probe = np.asarray(probe)

shank = []
for i in range(8): shank.append("shank0")
for i in range(8): shank.append("shank1")
for i in range(8): shank.append("shank2")
for i in range(8): shank.append("shank3")

ee = gg.make_group("extracellular_ephys")
ee.set_dataset('electrode_map', probe)
ee.set_dataset('electrode_group', shank)
ee.set_dataset('filtering', "Bandpass filtered 300-6K Hz")

#add empty ElectricalSeries to acquisition
def create_empty_acquisition_series(name, num):
    #- vs = nuo.create_timeseries("ElectricalSeries", name, "acquisition")
    vs = nuo.make_group("<ElectricalSeries>", name, path="/acquisition/timeseries")
    data = [0]
    vs.set_attr("comments","Acquired at 19531.25Hz")
    vs.set_attr("source", "Device 'ephys-acquisition'")
    vs.set_dataset("data", data, attrs={"unit": "none", "conversion": 1.0, "resolution": float('nan')})
    timestamps = [0]
    vs.set_dataset("timestamps", timestamps)
    el_idx = 8 * num + np.arange(8)
    vs.set_dataset("electrode_idx", el_idx) 
    vs.set_attr("description", "Place-holder time series to represent ephys recording. Raw ephys data not stored in file")
    # vs.finalize()
    
ephys_device_txt = "32-electrode NeuroNexus silicon probes recorded on a PCI6133 National Instrimunts board. See 'general/experiment_description' for more information"
nuo.set_dataset("<device_X>", ephys_device_txt, name="ephys-acquisition")
nuo.set_dataset("<device_X>", "Stimulating laser at 473 nm", name="optogenetic-laser")

def create_electrode_group_location(name, location):
    global ee  # /general/extracellular_ephys group
    eg = ee.make_group("<electrode_group_X>", name)
    eg.set_dataset("location", location)
    
# TODO fix location info. also check electrode coordinates
# nuo.set_dataset(EXTRA_SHANK_LOCATION("shank0"), "P: 2.5, Lat:-1.2. vS1, C2, Paxinos. Recording marker DiI")
create_electrode_group_location("shank0", "P: 2.5, Lat:-1.2. vS1, C2, Paxinos. Recording marker DiI")
create_empty_acquisition_series("shank0", 0)
create_electrode_group_location("shank1", "P: 2.5, Lat:-1.4. vS1, C2, Paxinos. Recording marker DiI")
create_empty_acquisition_series("shank1", 1)
create_electrode_group_location("shank2", "P: 2.5, Lat:-1.6. vS1, C2, Paxinos. Recording marker DiI")
create_empty_acquisition_series("shank2", 2)
create_electrode_group_location("shank3", "P: 2.5, Lat:-1.8. vS1, C2, Paxinos. Recording marker DiI")
create_empty_acquisition_series("shank3", 3)

# behavior
task_kw = map(str,parse_h5_obj(meta_h5["behavior/task_keyword"])[0])
nuo.set_custom_dataset("task_keyword", task_kw)

#virus
inf_coord = parse_h5_obj(meta_h5["virus/infectionCoordinates"])[0]
inf_loc = parse_h5_obj(meta_h5["virus/infectionLocation"])[0]
inj_date = parse_h5_obj(meta_h5["virus/injectionDate"])[0]
inj_volume = parse_h5_obj(meta_h5["virus/injectionVolume"])[0]
virus_id = parse_h5_obj(meta_h5["virus/virusID"])[0]
virus_lotNr = parse_h5_obj(meta_h5["virus/virusLotNumber"])[0]
virus_src = parse_h5_obj(meta_h5["virus/virusSource"])[0]
virus_tit = parse_h5_obj(meta_h5["virus/virusTiter"])[0]

virus_text = " Infection Coordinates: " + str(inf_coord) +\
"\nInfection Location: " + inf_loc +\
"\nInjection Date: " + inj_date +\
"\nInjection Volume: "  + str(inj_volume) +\
"\nVirus ID: " + virus_id +\
"\nVirus Lot Number: " + virus_lotNr +\
"\nVirus Source: " + virus_src +\
"\nVirus Titer: " + str(virus_tit)

nuo.set_dataset("virus", virus_text)

#fiber
ident_meth = parse_h5_obj(check_entry(meta_h5, "photostim/identificationMethod"))
ident_text = ""
if len(ident_meth) > 0:
    for i in range(len(ident_meth[0])):
        if i == 0:
            ident_text = ident_meth[0][i]
        else:
            ident_text += ", " + ident_meth[0][i]
    ident_text = "Identification method: " + ident_text
location = parse_h5_obj(check_entry(meta_h5, "photostim/photostimLocation"))
loc_text = ""
if len(location) > 0:
    for i in range(len(location[0])):
        if i == 0:
            loc_text = location[0][i]
        else:
            loc_text += ", " + location[0][i]
    loc_text = "Location: " + loc_text




opto = nuo.make_group("optogenetics")
s1 = opto.make_group("<site_X>", "site 1")
s1.set_dataset("description", loc_text+"\n"+ident_text)
stim_loc = parse_h5_obj(check_entry(meta_h5,"photostim/photostimLocation"))[0]
stim_coord = parse_h5_obj(check_entry(meta_h5,"photostim/photostimCoordinates"))[1]
stim_lambda = parse_h5_obj(check_entry(meta_h5,"photostim/photostimWavelength"))[0]
stim_text = "Stim location: %s\nStim coordinates: %s" % (str(stim_loc), str(stim_coord))
s1.set_dataset("location", str(stim_text))
s1.set_dataset("excitation_lambda", str(stim_lambda[0])+" nm")
s1.set_dataset("device", "optogenetic-laser")

# try:
#     impl_date = parse_h5_obj(meta_h5["fiber/implantDate"])[0]
#     tip_coord = parse_h5_obj(meta_h5["fiber/tipCoordinates"])[0]
#     tip_loc   = parse_h5_obj(meta_h5["fiber/tipLocation"])[0]
# 
#     fiber_text = "Implant Date: " + impl_date +\
#     "\nTip Coordinates: " + str(tip_coord) +\
#     "\nTip Location: " + str(tip_loc)
#     nuo.set_custom_metadata("fiber", fiber_text)
# except KeyError:
#     print "Can't find fiber data"    



#photostim
phst_id_method = parse_h5_obj(meta_h5["photostim/identificationMethod"])[0]
phst_coord = parse_h5_obj(meta_h5["photostim/photostimCoordinates"])[0]
phst_loc = parse_h5_obj(meta_h5["photostim/photostimLocation"])[0]
phst_wavelength = parse_h5_obj(meta_h5["photostim/photostimWavelength"])[0][0]
stim_method = parse_h5_obj(meta_h5["photostim/stimulationMethod"])[0]

photostim_text = "Identification Method: " + phst_id_method +\
"\nPhotostimulation Coordinates: " + str(phst_coord) +\
"\nPhotostimulation Location: " + phst_loc +\
"\nPhotostimulation Wavelength: " + str(phst_wavelength) +\
"\nStimulation Method: " + stim_method

nuo.set_dataset("stimulus", str(photostim_text))  # jt - had to add str, this is a 2-element array

#extracellular
ad_unit = parse_h5_obj(meta_h5["extracellular/ADunit"])[0]
ampl_rolloff = parse_h5_obj(meta_h5["extracellular/amplifierRolloff"])[0]
cell_type = parse_h5_obj(meta_h5["extracellular/cellType"])[0]
ec_data_type = parse_h5_obj(meta_h5["extracellular/extracellularDataType"])[0]
ground_coord = parse_h5_obj(meta_h5["extracellular/groundCoordinates"])[0]
id_method = parse_h5_obj(meta_h5["extracellular/identificationMethod"])[0]
penetration_n = parse_h5_obj(meta_h5["extracellular/penetrationN"])[0]
probe_src = parse_h5_obj(meta_h5["extracellular/probeSource"])[0]
probe_type = parse_h5_obj(meta_h5["extracellular/probeType"])[0]
rec_coord = parse_h5_obj(meta_h5["extracellular/recordingCoordinates"])[0]
rec_loc = parse_h5_obj(meta_h5["extracellular/recordingLocation"])[0]
rec_marker = parse_h5_obj(meta_h5["extracellular/recordingMarker"])[0]
rec_type = parse_h5_obj(meta_h5["extracellular/recordingType"])[0]
ref_coord = parse_h5_obj(meta_h5["extracellular/referenceCoordinates"])[0]
site_loc = parse_h5_obj(meta_h5["extracellular/siteLocations"])[0]
spk_sorting = parse_h5_obj(meta_h5["extracellular/spikeSorting"])[0]

# raw data section
# lick trace is stored in acquisition
# photostimulation wave forms is stored in stimulus/processing
print "Reading raw data"
# get times
grp_name = "timeSeriesArrayHash/value/time/time"
timestamps = orig_h5[grp_name].value
# get data
grp_name = "timeSeriesArrayHash/value/valueMatrix/valueMatrix"
lick_trace = orig_h5[grp_name][:,0]
aom_input_trace = orig_h5[grp_name][:,1]
laser_power = orig_h5[grp_name][:,2]
# get descriptions
comment1 = parse_h5_obj(orig_h5["timeSeriesArrayHash/keyNames"])[0]
comment2 = parse_h5_obj(orig_h5["timeSeriesArrayHash/descr"])[0]
comments = comment1 + ": " + comment2
grp_name = "timeSeriesArrayHash/value/idStrDetailed"
descr = parse_h5_obj(orig_h5[grp_name])[0]
# create timeseries
#create_aq_ts(nuo, "lick_trace", "acquisition",timestamps, rate, lick_trace, comments, descr[0])
lick_ts = nuo.make_group("<TimeSeries>", "lick_trace", path="/acquisition/timeseries")
lick_ts.set_dataset("data", lick_trace, attrs={"conversion":1.0, "unit":"unknown", "resolution":float('nan')})
lick_trace_len = len(lick_trace)
lick_ts.set_attr("comments", comments)
lick_ts.set_attr("description", descr[0])
lick_ts_time = lick_ts.set_dataset("timestamps", timestamps)
# lick_ts.finalize()

#create_aq_ts(nuo, "laser_power", "acquisition", "acquisition/timeseries/lick_trace/",\
# rate, laser_power, comments, descr[2], 1)
laser_ts = nuo.make_group("<OptogeneticSeries>", "simple_optogentic_stimuli", path="/stimulus/presentation")
laser_ts.set_dataset("data", laser_power, attrs={"resolution":float('nan'), "unit":"Watts", "conversion":1000.0})
laser_ts.set_attr("comments", comments)
laser_ts.set_dataset("site", "site 1")
laser_ts.set_attr("description", descr[2])
laser_ts.set_dataset("timestamps", lick_ts_time)
# laser_ts.set_value("num_samples", lick_trace_len)
# laser_ts.finalize()
#create_aq_ts(nuo, "aom_input_trace", "stimulus", "acquisition/timeseries/lick_trace/",\
# rate, aom_input_trace,comments, descr[1], 1)
aom_ts = nuo.make_group("<TimeSeries>", "aom_input_trace", path="/stimulus/presentation")
aom_ts.set_dataset("data", lick_trace, attrs={"resolution":float('nan'), "unit":"Volts", "conversion":1.0})
aom_ts.set_attr("comments", comments)
aom_ts.set_attr("description", descr[1])
aom_ts.set_dataset("timestamps", "link:/acquisition/timeseries/lick_trace/timestamps")
# aom_ts.set_value("num_samples", lick_trace_len)
# aom_ts.finalize()

trial_start_times = orig_h5["trialStartTimes/trialStartTimes"].value
grp = orig_h5["trialPropertiesHash/value/"]
description = parse_h5_obj(orig_h5['trialPropertiesHash/keyNames'])[0]
comments = parse_h5_obj(orig_h5['trialPropertiesHash/descr'])[0]


pole_in_ts = nuo.make_group("<TimeSeries>", "pole_in", path="/stimulus/presentation")
time = grp["1/1"].value
pole_in_timestamps = time + trial_start_times
# create dummy data: 1 for 'on', -1 for 'off'
pole_in_data = [1]*len(pole_in_timestamps)
pole_in_ts.set_dataset("data", pole_in_data, attrs={"resolution":float('nan'),"unit":"unknown","conversion":1.0})
pole_in_ts.set_attr("comments", comments[0])
pole_in_ts.set_attr("description", description[0])
pole_in_ts.set_dataset("timestamps", pole_in_timestamps)
pole_in_ts.set_attr("source", "Times and intervals are as reported in Nuo's data file, but relative to session start")
# pole_in_ts.finalize()

pole_out_ts = nuo.make_group("<TimeSeries>", "pole_out", path="/stimulus/presentation")
time = grp["2/2"].value
pole_out_timestamps = time + trial_start_times
# create dummy data: 1 for 'on', -1 for 'off'
pole_out_data = [1]*len(pole_out_timestamps)
pole_out_ts.set_dataset("data", pole_out_data, attrs={"resolution":float('nan'),"unit":"unknown","conversion":1.0})
pole_out_ts.set_attr("comments", comments[1])
pole_out_ts.set_attr("description", description[1])
pole_out_ts.set_dataset("timestamps", pole_out_timestamps)
pole_out_ts.set_attr("source", "Times and intervals are as reported in Nuo's data file, but relative to session start")
# pole_out_ts.finalize()

aud_cue_ts = nuo.make_group("<TimeSeries>", "auditory_cue", path="/stimulus/presentation")
time = grp["3/3"].value
cue_timestamps = time + trial_start_times
# create dummy data: 1 for 'on', -1 for 'off'
cue_data = [1]*len(cue_timestamps)
aud_cue_ts.set_dataset("data", cue_data, attrs={"resolution":float('nan'),"unit":"unknown","conversion":1.0})
aud_cue_ts.set_attr("comments", comments[2])
aud_cue_ts.set_attr("description", description[2])
aud_cue_ts.set_dataset("timestamps", cue_timestamps)
aud_cue_ts.set_attr("source", "Times are as reported in Nuo's data file, but relative to session time")
# aud_cue_ts.finalize()

# Create module 'Units' for ephys data
# Interface 'UnitTimes' contains spike times for the individual units
# Interface 'EventWaveform' contains waveform data and electrode information
# Electrode depths and cell types are collected in string arrays at the top level
# of the module
print "Reading Event Series Data"
# create module unit
mod_name = "Units"
mod = nuo.make_group("<Module>", mod_name)
mod.set_custom_dataset('description', 'Spike times and waveforms')
# create interfaces
spk_waves_iface = mod.make_group("EventWaveform")
spk_waves_iface.set_attr("source", "Data as reported in Nuo's file")
spk_times_iface = mod.make_group("UnitTimes")
spk_times_iface.set_attr("source", "EventWaveform in this module")
#spk_times_iface.set_value("source", "EventWaveform")
# top level folder
grp_name = "eventSeriesHash/value"
# determine number of units
unit_num = len(orig_h5[grp_name].keys())
# initialize cell_types and electrode_depth arrays with default values
cell_types = ['unclassified']*unit_num
n = max(range(unit_num)) + 1
electrode_depths = np.zeros(n)
#electrode_depths = [float('NaN')]*unit_num
unit_descr = parse_h5_obj(orig_h5['eventSeriesHash/descr'])[0]
# process units
for i in range(unit_num):
    i = i+1
    unit = "unit_%d%d" % (int(i/10), i%10)
    # initialize timeseries
    spk = spk_waves_iface.make_group("<SpikeEventSeries>", unit)
    # get data
    grp_name = "eventSeriesHash/value/%d" % i
    grp_top_folder = orig_h5[grp_name]
    timestamps = grp_top_folder["eventTimes/eventTimes"].value
    trial_ids = grp_top_folder["eventTrials/eventTrials"].value
    waveforms = grp_top_folder["waveforms/waveforms"]
    sample_length = waveforms.shape[1]
    channel = grp_top_folder["channel/channel"].value
    # read in cell types and update cell_type array
    cell_type = parse_h5_obj(grp_top_folder["cellType"])[0]
    if  'numpy' in str(type(cell_type)):
        cells_conc = ' and '.join(map(str, cell_type))
        cell_type = cells_conc
    else:
        cell_type = str(cell_type)
    # try:
    #         cell_type = grp_top_folder["cellType/cellType"][0,0]
    #     except KeyError:
    #         cell_type_1 = grp_top_folder["cellType/1/1"][0,0]
    #         cell_type_2 = grp_top_folder["cellType/2/2"][0,0]
    #         cell_type = cell_type_1 + " and " + cell_type_2
    cell_types[i-1] = unit + " - " + cell_type
    # read in electrode depths and update electrode_depths array
    depth = parse_h5_obj(grp_top_folder["depth"])[0]
    # depth = grp_top_folder["depth/depth"][0,0]
    electrode_depths[i-1] = 0.001 * depth
    # fill in values for the timeseries
    spk.set_custom_dataset("sample_length", sample_length)
    spk.set_attr("source", "---")
    spk.set_dataset("timestamps", timestamps)
    spk.set_dataset("data", waveforms, attrs={"resolution":float('nan'), "unit":"Volts", "conversion":0.1})
    spk.set_dataset("electrode_idx", [channel[0]])
    spk.set_attr("description", cell_type)
    # spk_waves_iface.add_timeseries(spk)
    # add spk to interface
    #description = unit_descr[i-1] + " -- " + cell_type
    # spk_times_iface.add_unit(unit, timestamps, cell_type, "Data from processed matlab file")
    ug = spk_times_iface.make_group("<unit_N>", unit)
    ug.set_dataset("times", timestamps)
    ug.set_dataset("source", "Data from processed matlab file")
    ug.set_dataset("unit_description", cell_type)
    # spk_times_iface.append_unit_data(unit, "trial_ids", trial_ids)
    ug.set_custom_dataset("trial_ids", trial_ids)
# spk_times_iface.set_value("CellTypes", cell_types)
spk_times_iface.set_custom_dataset("CellTypes", cell_types)
spk_times_iface.set_custom_dataset("ElectrodeDepths", electrode_depths)
# mod.finalize()

# print "Reading Behavior time series"
# read_pole_position(orig_h5, nuo)
# read_cue(orig_h5, nuo)

print "Creating epochs"
get_trial_types(orig_h5, nuo)
get_trial_units(orig_h5, nuo, unit_num)
create_trials(orig_h5, nuo)

print "Collecting Analysis Information"
trial_start_times = orig_h5["trialStartTimes/trialStartTimes"].value
trial_types_all = []
trial_type_strings = parse_h5_obj(orig_h5['trialTypeStr'])[0]
# collect all trials (strings)
for i in range(8):
    trial_types_all.append(str(trial_type_strings[i]))
# trial_type_strings = orig_h5["trialTypeStr"]
# trial_types_all = []
# for i in range(8):
#     trial_types_all.append(trial_type_strings["%d/%d" %(i+1,i+1)].value[0,0])
trial_type_mat = orig_h5['trialTypeMat/trialTypeMat'].value
good_trials = orig_h5['trialPropertiesHash/value/4/4'].value
grp = nuo.make_group("analysis", abort=False)
grp.set_custom_dataset("trial_start_times", trial_start_times)
grp.set_custom_dataset("trial_type_string", trial_types_all)
grp.set_custom_dataset("trial_type_mat", trial_type_mat)
grp.set_custom_dataset("good_trials", good_trials)

print "Closing file"

nuo.close()
print "Done"

