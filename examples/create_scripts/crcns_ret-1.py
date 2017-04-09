#!/usr/bin/python

# script to convert Meister sample data sets to NWB format
# modified to use specification language

import glob
import sys
import os
import h5py
import datetime
import numpy as np
import scipy.io as sio

from nwb import nwb_file
from nwb import nwb_utils as ut


# directory for input data
SOURCE_DATA_DIR = "../source_data_2/crcns_ret-1/"
path = SOURCE_DATA_DIR + "Data/"

if not os.path.exists(path):
    print ("Source files for script '%s' not present." % os.path.basename(__file__))
    print ("Download and put them in the 'examples/source_data' directory as instructed")
    print ("in file examples/0_README.txt")
    sys.exit(1) 


file_list = glob.glob(path + "*.mat")
#file_list = [path+"20080516_R2.mat"]

if not file_list:
    print ("*** Error:")
    print ("No files found at '%s'.  Cannot run script %s." % (path, os.path.basename(__file__)))
    sys.exit(1)

# directory for created NWB files.  Must have a trailing slash.
OUTPUT_DIR = "../created_nwb_files/crcns_ret-1/"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# this directory for storing generated stimulus files (which are not NWB files).
STIM_LIBRARY_DIR = OUTPUT_DIR + "stim_library/"
if not os.path.exists(STIM_LIBRARY_DIR):
    os.makedirs(STIM_LIBRARY_DIR)


def find_exp_time(fname, data_info):
    try:
        d = data_info["date"][0]
    except IndexError:
        print ("Warning: Unable to read recording date from " + fname)
        return ""
    try:
        rst = data_info["RecStartTime"][0]
    except IndexError:
        print ("Warning: Unable to read recording start time from " + fname)
        return ""
    time = d + str(rst[3]) + str(rst[4]) + str(rst[5])
    dt=datetime.datetime.strptime((time), "%Y%m%d%H%M%S")
    return dt.strftime("%a %b %d %Y %H:%M:%S")
    
def find_stim_times(fname, data_info):
    try:
        d = data_info["date"][0]
    except IndexError:
        print ("Error: Unable to read recording date from " + fname)
        assert False
    try:
        rst = data_info['RecStartTime']
    except IndexError:
        print ("Error: Unable to read recording start time from " + fname)
        assert False
    dt = []
    for i in range(len(rst)):
        time = d + str(rst[i][3]) + str(rst[i][4]) + str(rst[i][5])
        dt.append(datetime.datetime.strptime((time), "%Y%m%d%H%M%S"))
    for i in range(1,len(rst)):
        dt[i] = (dt[i] - dt[0]).total_seconds()
    dt[0] = 0.0
    return dt

def create_stim_ident(x, y, dx, dy):
    return "%dx%d_%dx%d" % (x, y, dx, dy)

def create_stimulus_file(fname, seed, x, y, dx, dy):
    print ("Creating stimulus file " + fname)
    ident = create_stim_ident(x, y, dx, dy)
    n_pixels = stim_pixel_cnt[ident]
    data = np.zeros(n_pixels)
    with open(SOURCE_DATA_DIR + "ran1.bin", 'rb') as f:
        for i in range(int(n_pixels/8)):  #py3, added int
            byte = f.read(1)
            for j in reversed(range(8)):
                data[i*8+j] = 255*(ord(byte) >> j & 1)
            # for j in range(8):
            #     data[i*8+j] = 255 * ((ord(byte) >> (7-j)) & 1)
    nx = int(x/dx)  # py3, added int
    ny = int(y/dy)  # py3, added int
    n_frames = int(n_pixels / (nx * ny))  # py3, added int
    # reshape stimulus
    datar = np.reshape(data, (n_frames, ny, nx))
    h5 = h5py.File(fname, 'w')
    grp = h5.create_dataset("image_stack", data=datar, compression=True, dtype='uint8')
    grp.attrs["si_unit"] = "grayscale"
    grp.attrs["resolution"] = "1"
    grp.attrs["conversion"] = "1"
    h5.close()

def fetch_stimulus_link(seed, x, y, dx, dy):
    # see if stack already exists. if not, create it
    fname = STIM_LIBRARY_DIR + "%s_%d.h5" % (create_stim_ident(x, y, dx, dy), seed)
    if not os.path.isfile(fname):
        # need to create file
        create_stimulus_file(fname, seed, x, y, dx, dy)
    return fname, "image_stack"
    
    
electrode_map = []
# using 61-channel configuration from Mesiter et al., 1994
# NOTE: this is an estimate and is used for example purposes only
for i in range(5): electrode_map.append([(140+70*i),   0, 0])
for i in range(6): electrode_map.append([(105+70*i),  60, 0])
for i in range(7): electrode_map.append([( 70+70*i), 120, 0])
for i in range(8): electrode_map.append([( 30+70*i), 180, 0])
for i in range(9): electrode_map.append([(    70*i), 240, 0])
for i in range(8): electrode_map.append([( 30+70*i), 300, 0])
for i in range(7): electrode_map.append([( 70+70*i), 360, 0])
for i in range(6): electrode_map.append([(105+70*i), 420, 0])
for i in range(5): electrode_map.append([(140+70*i), 480, 0])
electrode_group = []
for i in range(len(electrode_map)):
    electrode_group.append("61-channel probe")

print ("Getting stimulus frame requirements")
stim_pixel_cnt = {}
for i in range(len(file_list)):
    fname = file_list[i][len(path):]
    mfile = sio.loadmat(file_list[i], struct_as_record=True)
    # prepare matlab data
    data_info = mfile['datainfo'][0,0]
    # 
    stim_offset = find_stim_times(fname, data_info)
    for i in range(len(stim_offset)):
        # create stimuli
        # read data from mat file
        stimulus = mfile["stimulus"][0,i]
        n_frames = stimulus["Nframes"][0,0]
        # figure out how many pixels per frame
        x = stimulus["param"]["x"][0,0][0,0]
        y = stimulus["param"]["y"][0,0][0,0]
        dx = stimulus["param"]["dx"][0,0][0,0]
        dy = stimulus["param"]["dy"][0,0][0,0]
        nx = int(x/dx)
        ny = int(y/dy)
        n_pix = n_frames * nx * ny
        # remember maximum pixel count for this stimulus type
        name = create_stim_ident(x, y, dx, dy)
        if name in stim_pixel_cnt:
            n = stim_pixel_cnt[name]
            if n_pix > n:
                stim_pixel_cnt[name] = n_pix
        else:
            stim_pixel_cnt[name] = n_pix

for i in range(len(file_list)):
    fname = file_list[i][len(path):]
    print ("Processing " + fname)
    mfile = sio.loadmat(file_list[i], struct_as_record=True)
    # prepare matlab data
    data_info = mfile['datainfo'][0,0]
    # prepare output file
    vargs = {}
    vargs["start_time"] = find_exp_time(fname, data_info)
    vargs["identifier"] = ut.create_identifier("Meister test data")
    vargs["mode"] = "w"
    vargs["description"] ="Optical stimulation and extracellular recording of retina"
    vargs["file_name"] = OUTPUT_DIR + fname[:-4]+".nwb"    
    bfile = nwb_file.open(**vargs)
    print ("Creating " + vargs["file_name"])
    # get stimulus offset times
    stim_offset = find_stim_times(fname, data_info)
    stim_end = []
    # 
    for i in range(len(stim_offset)):
        # create stimuli
        # read data from mat file
        stimulus = mfile["stimulus"][0,i]
        n_frames = stimulus["Nframes"][0,0]
        frame = stimulus["frame"][0,0]
        onset = stimulus["onset"][0,0]
        type_s = stimulus["type"][0]
        seed = stimulus["param"]["seed"][0,0][0,0]
        x = stimulus["param"]["x"][0,0][0,0]
        y = stimulus["param"]["y"][0,0][0,0]
        dx = stimulus["param"]["dx"][0,0][0,0]
        dy = stimulus["param"]["dy"][0,0][0,0]
        pixel_size = stimulus["pixelsize"][0,0]
        # reformmat for nwb
        timestamps = np.arange(n_frames) * frame + onset + stim_offset[i]
        rec_stim_name = "rec_stim_%d" % (i+1)
        # create stimulus
        img = bfile.make_group("<ImageSeries>", rec_stim_name, path="/stimulus/presentation")
        img.set_custom_dataset("pixel_size", pixel_size)
        img.set_custom_dataset("meister_dx", dx)
        img.set_custom_dataset("meister_dy", dy)
        img.set_custom_dataset("meister_x", x)
        img.set_custom_dataset("meister_y", y)
        img.set_dataset("timestamps", timestamps)
        img.set_dataset("num_samples", len(timestamps))
        file_name, dataset_name = fetch_stimulus_link(seed, x, y, dx, dy)
        file_name_base = file_name[len(OUTPUT_DIR):]  # strip OUTPUT_DIR from front of name
        #- img.set_data_as_remote_link(file_name, dataset_name)
        link_str = "extlink:%s,%s" % (file_name_base, dataset_name)
        img.set_dataset("data", link_str) # special string, causes creation of external link
        img.set_dataset("bits_per_pixel", 8)
        img.set_dataset("format", "raw")
        img.set_dataset("dimension", [int(x/dx), int(y/dy)])  # py3, force to be int
        img.set_attr("description", "type = " + str(type_s) + "; seed = " + str(seed))
        img.set_attr("comments", "Based on ran1.bin. Pixel values are 255 for light, 0 for dark")
        # create epoch
        stim_end = timestamps[-1] + 1
        epoch = ut.create_epoch(bfile, "stim_%d"%(i+1), stim_offset[i], stim_end)
        stim_start = stim_offset[i]
        ts_path = "/stimulus/presentation/"+img.name
        ut.add_epoch_ts(epoch, stim_start, stim_end, "stimulus", ts_path)

    # create module 'Cells' for the spikes    
    mod_name = "Cells"
    mod = bfile.make_group("<Module>", mod_name)
    mod.set_attr("description", "Spike times for the individual cells and stimuli")
    mod.set_attr("source", "Data as reported in the original file")
    # create interfaces
    spk_times_iface = mod.make_group("UnitTimes")
    spk_times_iface.set_attr("source", "Data as reported in the original crcns file")
    # determine number of cells
    spikes_mat = mfile["spikes"]
    num_cells = spikes_mat.shape[0]
    num_stims = spikes_mat.shape[1]
    # unit_list = []  ## Added for specification language conversion method
    for i in range(num_cells):
        cell_name = "cell_%d" %(i+1)
        # unit_list.append(cell_name)   ## Added for specification language conversion method
        cgrp = spk_times_iface.make_group("<unit_N>", cell_name)
        spike_list = []
        for j in range(num_stims):
            stim_name = "stim_%d" % (j+1)
            spikes = np.hstack(spikes_mat[i,j]) + stim_offset[j]
            spike_list.extend(spikes)
            cgrp.set_custom_dataset(stim_name, spikes)
        cgrp.set_dataset("times", spike_list)
        cgrp.set_dataset("unit_description", "none")       
    #- spk_times_iface.finalize()
    # spk_times_iface.set_dataset("unit_list", unit_list) ## Added for specification language conversion method
    #- mod.finalize()

    # write metadata
    rec_no = data_info["RecNo"][0]
    smpl_no = data_info["SmplNo"][0]
    animal = data_info["animal"][0]
    description = data_info["description"][0]
    session_id = "RecNo: " + str(rec_no) + "; SmplNo: " + str(smpl_no)
    bfile.set_dataset("session_id", session_id)
    bfile.set_dataset("experimenter", "Yifeng Zhang")    
    bfile.set_dataset("institution", "Harvard University")
    bfile.set_dataset("lab", "Markus Meister")
    bfile.set_dataset("related_publications", "Yi-Feng Zhang, Hiroki Asari, and Markus Meister (2014); Multi-electrode recordings from retinal ganglion cells. CRCNS.org. http://dx.doi.org/10.6080/K0RF5RZT")
    bfile.set_dataset("notes", str(description))
    bfile.set_dataset("species", "mouse")
    bfile.set_dataset("genotype", str(animal))
    bfile.set_custom_dataset("random_number_generation", "Reference: WH Press, et al. (1992) Numerical Recipes in C, 2nd ed.")
    # bfile.set_custom_metadata_by_file("random_number_generation_code", "ran1.m")
    bfile.set_dataset('electrode_map', electrode_map)
    bfile.set_dataset('electrode_group', electrode_group)
    g =  bfile.make_group('<electrode_group_X>', "61-channel_probe")
    g.set_dataset('description',"Approximation of electrode array used in experiment based on Mester, et. al., 1994 (DEMO DATA)")
    g.set_dataset('location',"Retina flatmount recording")
    g.set_dataset('device', "----")
    print ("\tdone")
    bfile.close()

