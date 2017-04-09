#!/usr/bin/python
import sys
import os

from nwb import nwb_file
from nwb import nwb_utils as ut
import numpy as np

# dataset to use
#BASE = "ec013.156"
BASE = "ec013.157"

print ("Warning -- experiment time is hard-coded. Needs to be read from file")
if BASE == "ec013.156":
    DATE = "Sat Jul 08 2006 12:00:00"
else:   # ec013.157
    DATE = "Sat Jul 08 2006 12:30:00"

# paths to source files
SOURCE_DATA_DIR = "../source_data_2/crcns_hc-3/"
PATH = SOURCE_DATA_DIR + BASE

if not os.path.exists(PATH):
    print ("Source files for script '%s' not present" % os.path.basename(__file__))
    print ("Download and put them in the 'examples/source_data' directory as instructed")
    print ("in file examples/0_README.txt")
    sys.exit(1) 


# path to output directory
OUTPUT_DIR = "../created_nwb_files/crcns_hc-3/"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


# create nwb file
settings = {}
settings["file_name"] = OUTPUT_DIR + BASE + ".nwb"
settings["identifier"] = ut.create_identifier("buzsaki test")
settings["mode"] = "w"
settings["start_time"] = DATE
settings["description"] = "extracellular ephys CA1/MEC recordings in live behaving rat"
buz =  nwb_file.open(**settings)
########################################################################
# metadata section

buz.set_dataset("session_id", BASE)
buz.set_dataset("experimenter", "Kenji Mizuseki")
buz.set_dataset("institution", "Rutgers University")
buz.set_dataset("lab", "Gyuri Buzsaki")
buz.set_dataset("related_publications", ut.load_file(SOURCE_DATA_DIR + "bz_files/publications.txt"))
buz.set_dataset("notes", "Rat running on linear track. Electrode impedances between 1 and 3 MOhm")
buz.set_dataset("data_collection", ut.load_file(SOURCE_DATA_DIR + "bz_files/data_collection.txt"))

buz.set_dataset("pharmacology", "----")
buz.set_dataset("surgery", ut.load_file(SOURCE_DATA_DIR + "bz_files/surgery.txt"))
buz.set_dataset("protocol", "----")
buz.set_dataset("subject_id", "ec013")
sg = buz.make_group("subject", abort=False)
sg.set_dataset("description", "----")
sg.set_dataset("species", "Long Evans rat")
sg.set_dataset("genotype", "wt")
sg.set_dataset("sex", "male")
sg.set_dataset("age", "----")
sg.set_dataset("weight", "250-400 g")
buz.set_dataset("virus", "n/a")
buz.set_dataset("slices", "n/a")

print ("Warning -- electrode map is hard-coded. Needs to be read from XML")
electrode_map = [
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ],
    [     0, 0, 0 ], [ 20e-6, 0, 0 ], [ 40e-6, 0, 0 ], [ 60e-6, 0, 0 ],
    [ 80e-6, 0, 0 ], [100e-6, 0, 0 ], [120e-6, 0, 0 ], [140e-6, 0, 0 ]
]

electrode_group = [
    "p0", "p0", "p0", "p0", "p0", "p0", "p0", "p0", 
    "p1", "p1", "p1", "p1", "p1", "p1", "p1", "p1", 
    "p2", "p2", "p2", "p2", "p2", "p2", "p2", "p2", 
    "p3", "p3", "p3", "p3", "p3", "p3", "p3", "p3", 
    "p4", "p4", "p4", "p4", "p4", "p4", "p4", "p4", 
    "p5", "p5", "p5", "p5", "p5", "p5", "p5", "p5", 
    "p6", "p6", "p6", "p6", "p6", "p6", "p6", "p6", 
    "p7", "p7", "p7", "p7", "p7", "p7", "p7", "p7"
]


buz.set_dataset('electrode_map', electrode_map)
buz.set_dataset('electrode_group', electrode_group)

#impedance_map = []
#for i in range(len(electrode_map)):
#    impedance_map.append("1-3 MOhm")
#buz.set_metadata(EXTRA_IMPEDANCE, impedance_map)

def set_electrode_group(name, location):
    gx = buz.make_group("<electrode_group_X>", name)
    gx.set_dataset("location", location)

set_electrode_group("p0", "Entorhinal cortex, layer 3")
set_electrode_group("p1", "Entorhinal cortex, layer 4")
set_electrode_group("p2", "Entorhinal cortex, layer 5")
set_electrode_group("p3", "Entorhinal cortex, layer 5")
set_electrode_group("p4", "Hippocampal area CA1")
set_electrode_group("p5", "Hippocampal area CA1")
set_electrode_group("p6", "Hippocampal area CA1")
set_electrode_group("p7", "Hippocampal area CA1")

########################################################################
# data section

# table storing indices for electrodes per shank
script_elect_map = [
    [ 0 , 1 , 2 , 3 , 4 , 5 , 6 , 7   ],
    [ 8 , 9 , 10, 11, 12, 13, 14, 15  ],
    [ 16, 17, 18, 19, 20, 21, 22, 23  ],
    [     25, 26, 27, 28, 29, 30, 31  ],
    [ 32, 33, 34, 35, 36, 37, 38, 39  ],
    [ 40, 41, 42, 43, 44, 45, 46, 47  ],
    [ 48, 49, 50, 51, 52, 53, 54, 55  ],
    [ 56, 57, 58, 59, 60,     62, 63  ]
]

# EEG files looks to have 65 channels, based on repeat pattern in binary data
#   SAMPLES = <file bytes> / 65 channels / 2 bytes per channel
if BASE == "ec013.156":
    SAMPLES = 1279488 
elif BASE == "ec013.157":
    SAMPLES = 789000 
else:
    print ("Unrecognized file -- need to determine number of LFP samples")
    sys.exit(1)

lfp_t = np.arange(SAMPLES) / 1250.0

for i in range(8):
    try:
        fname = "%s/%s.fet.%d" % (PATH, BASE, i+1)
        f = open(fname, "r")
    except IOError:
        print ("Error reading " + fname)
        sys.exit(1)
    cnt = int(f.readline())
    num_electrodes = int((cnt - 5) / 3)  # py3 - added int function
    features = []
    times = []
    feature_types = [ "PC1", "PC2", "PC3" ]
    electrode_idx = script_elect_map[i]
    feat_vals = f.readline()
    while len(feat_vals) > 0:
        fet_arr = feat_vals.split(' ')
        times.append(float(fet_arr[-1]) / 20000.0)
        fet = np.asarray(fet_arr[:3*num_electrodes]).astype(np.float)
        fet = fet.reshape(num_electrodes, 3)
        features.append(fet)
        feat_vals = f.readline()
    f.close()

    # load LFP data
    lfp_data = np.zeros((SAMPLES, num_electrodes))
    try:
        fname = "%s/%s.eeg" % (PATH, BASE)
        f = open(fname, "rb")  # py3, was "r"
        # SAMPLES is pre-computed for each file
        # 65 channels of data seem to be in the file. there's no
        #   documentation saying what LFP channel maps to what electrode,
        #   so let's pretend that there's a 1:1 correspondence
        for k in range(SAMPLES):    
            x = np.fromstring(f.read(130), dtype=np.int16, count=65)
            for j in range(num_electrodes):
                lfp_data[k][j] = x[electrode_idx[j]]
        f.close()
    except IOError:
        print ("Error reading " + fname)
        sys.exit(1)
    lfp_data *= 3.052e-7    # volts per bit

    try:
        fname = "%s/%s.clu.%d" % (PATH, BASE, i+1)
        f = open(fname, "r")
    except IOError:
        print ("Error reading " + fname)
        sys.exit(1)
    clu_cnt = int(f.readline())    # pull number of clusters from head of file
    nums = []
    noise = np.zeros(clu_cnt)
    clu_vals = f.readline()
    while len(clu_vals) > 0:
        nums.append(int(clu_vals))
        clu_vals = f.readline()
    f.close()
    num_events = len(nums)

    n = num_electrodes
    spk_data = np.zeros((num_events, n, 32))
    try:
        fname = "%s/%s.spk.%d" % (PATH, BASE, i+1)
        f = open(fname, "rb")  # py3, was "r"
        for k in range(num_events):
            x = np.fromstring(f.read(32*n*2), dtype=np.int16, count=32*n)
            # TODO FIXME make sure alignment is correct
            # storage should be [sample][channel][time]
            y = np.reshape(x, (32, n))
            for tt in range(32):
                for cc in range(n):
                    spk_data[k][cc][tt] = y[tt][cc]
        f.close()
    except IOError:
        print ("Error reading " + fname)
        sys.exit(1)
    spk_data *= 3.052e-7

    try:
        fname = ("%s/%s.threshold.%d" % (PATH, BASE, i+1))
        f = open(fname, "rb")  # py3, was "r"
        thresh = float(f.readline())
        f.close()
    except IOError:
        print ("Error reading " + fname)
        sys.exit(1)

    ####################################################################
    mod_name = "shank_%d" % i
    print ("creating %s" % mod_name)
    mod = buz.make_group("<Module>", mod_name)
    fet_iface = mod.make_group("FeatureExtraction")
    fet_iface.set_dataset("times", times)
    fet_iface.set_dataset("features", features)
    fet_iface.set_dataset("description", feature_types)
    fet_iface.set_dataset("electrode_idx", script_elect_map[i])
    fet_iface.set_attr("source", "EventWaveform interface, this module")
    # fet_iface.finalize()
    #
    clu_iface = mod.make_group("Clustering")
    clu_iface.set_dataset("times", times)
    clu_iface.set_dataset("num", nums)
    clu_iface.set_dataset("peak_over_rms", noise)
    clu_iface.set_dataset("description", "Cluster #0 is electrical noise, #1 is multi-unit/unsorted, and higher numbers are unit clusters")
    clu_iface.set_attr("source","FeatureExtracetion interface, this module")
    # clu_iface.finalize()

    lfp_iface = mod.make_group("LFP")
    lfp = lfp_iface.make_group("<ElectricalSeries>", "LFP timeseries")
    lfp.set_dataset("electrode_idx", electrode_idx)
    lfp.set_attr("description", "LFP signals from electrodes on this shank")
    lfp.set_dataset("data", lfp_data, attrs={"resolution":3.052e-7})
    lfp.set_dataset("timestamps", lfp_t)
    lfp_iface.set_attr("source", "Data as reported in experiment files")
    # lfp_iface.finalize()

    spk_iface = mod.make_group("EventWaveform")
    spk = spk_iface.make_group("<SpikeEventSeries>", "waveform_timeseries")
    spk.set_custom_dataset("sample_length", 32)  # this used to be in the spec, now is custom
    spk.set_dataset("timestamps", times)
    spk.set_dataset("data", spk_data, attrs={"resolution": 3.052e-7})
    spk.set_dataset("electrode_idx", electrode_idx)
    spk.set_attr("source", "Data as reported in experiment files")
    spk.set_attr("description", "Thresold for event detection was %f" % thresh)
    # spk_iface.add_timeseries(spk)
    spk_iface.set_attr("source", "Data as reported in experiment files")
    #
    # make unit interface
    unit_list = []
    for j in range(clu_cnt):
        unit_list.append([])
    for j in range(len(nums)):
        unit_list[nums[j]].append(times[j])
    unit_iface = mod.make_group("UnitTimes")
    # unit_iface.set_dataset("source", "processing/" + mod_name)
    unit_iface.set_attr("source", "Clustering interface, this module")
    for j in range(clu_cnt):
        if len(unit_list[j]) > 0:
            desc = "unit %d" % j
            g = unit_iface.make_group("<unit_N>", "%d"%j)
            g.set_dataset("times", unit_list[j])
            g.set_dataset("unit_description", desc)
            g.set_dataset("source", "From klustakwik, curated with Klusters")
    #
    mod.set_custom_dataset("description", "Processed ephys data for shank %d" % i)
    # mod.finalize()
    break;

posticks = 0
pos_a = []
pos_atime = []
pos_b = []
pos_btime = []
pos = []
postime = []
try:
    fname = "%s/%s.whl" % (PATH, BASE)
    with open(fname, "r") as f:  #py3, was "r"
        for line in f:
            toks = line.split('\t')
            x0 = float(toks[0])
            y0 = float(toks[1])
            x1 = float(toks[2])
            y1 = float(toks[3])
            if x0 >= 0:
                pos_a.append([x0/100, y0/100])
                pos_atime.append(posticks / 39.06)
            if x1 >= 0:
                pos_b.append([x1/100, y1/100])
                pos_btime.append(posticks / 39.06)
            if x0 >= 0 and x1 >= 0:
                pos.append([(x0+x1)/2, (y0+y1)/2])
                postime.append(posticks / 39.06)
            posticks += 1
except IOError:
    print ("Error reading " + fname)
    sys.exit(1)


mod = buz.make_group("<Module>", "head_position")
iface = mod.make_group("Position")
iface.set_attr("source", "Data as reported in experiment files")

posa_ts = iface.make_group("<SpatialSeries>", "LED 1")
posa_ts.set_attr("description", "LED 1, as reported in original data. Physical position of LED (eg, left, front, etc) not known")
posa_ts.set_dataset("reference_frame", "Top or room, as seen from camera")
posa_ts.set_dataset("timestamps", pos_atime)
posa_ts.set_dataset("data", pos_a, attrs={"resolution": 0.001})
# iface.add_timeseries(posa_ts)

posb_ts = iface.make_group("<SpatialSeries>", "LED 2")
posb_ts.set_attr("description","LED 2, as reported in original data. Physical position of LED (eg, left, front, etc) not known")
posb_ts.set_dataset("reference_frame", "Top or room, as seen from camera")
posb_ts.set_dataset("timestamps", pos_btime)
posb_ts.set_dataset("data", pos_b, attrs={"resolution":0.001})
# iface.add_timeseries(posb_ts)

pos_ts = iface.make_group("<SpatialSeries>", "position")
pos_ts.set_attr("description","Position intermediate to LED1 and LED2")
pos_ts.set_dataset("reference_frame", "Top or room, as seen from camera")
pos_ts.set_dataset("timestamps", postime)
pos_ts.set_dataset("data", pos, attrs={"resolution": 0.001})
# iface.add_timeseries(pos_ts)
# mod.finalize();

epoch = ut.create_epoch(buz, "Linear track", 0.0, postime[-1]+60)
epoch.set_dataset("description", "This folder would normally be one of several (eg, sleep_1, enclosure_1, sleep_2, track_1, etc) and each would provide windows into the different acquisition and stimulus streams. Since only one epoch (linear track) was imported into the sample NWB file, the functionality of epochs is not visible")
# epoch.finalize()

buz.close()


