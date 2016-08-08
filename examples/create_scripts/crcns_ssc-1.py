#!/usr/bin/python
import sys
import glob 
from nwb import nwb_file
from nwb import nwb_utils as ut

import h5py
import getpass
import datetime
import os
import numpy as np
from sets import Set

# path to source files
path = "../source_data/crcns_ssc-1/"

if not os.path.exists(path):
    print "Source files for script '%s' not present" % os.path.basename(__file__)
    print "Download and put them in the 'examples/source_data' directory as instructed"
    print "in file examples/0_README.txt"
    sys.exit(1) 



file_list = glob.glob(path + "*session.h5")

OUTPUT_DIR = "../created_nwb_files/crcns_ssc-1/"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

if not file_list:
    print "*** Error:"
    print "No files found at '%s'.  Cannot run this script." % path
    sys.exit(1)

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


# each of simon's hdf5 files have imaging planes and subareas
#   labels consistent within the file, but inconsistent between
#   files. create a map between the h5 plane name and the 
#   identifier used between files
plane_map = {}
def add_plane_map_entry(h5_plane_name, filename):
    toks = filename.split("fov_")
    if len(toks) != 2:
        print "Error parsing %s for imaging plane name" % filename
        sys.exit(1)
    univ_name = "fov_" + toks[1][:5]
    if univ_name not in plane_map:
        #print filename + " -> " + univ_name
        plane_map[h5_plane_name] = univ_name
    return univ_name

def create_plane_map():
    num_subareas = len(orig_h5['timeSeriesArrayHash/descrHash'].keys()) - 1
    for subarea in range(num_subareas):
        # fetch time array
        grp = orig_h5['timeSeriesArrayHash/value/%d/imagingPlane' %(subarea + 2)]
        grp2 = orig_h5['timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)]
        if grp2.keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(grp2.keys())
        for plane in range(num_planes):
            # if num_planes == 1:
            #     pgrp = grp
            # else:
            #     pgrp = grp["%d"%(plane+1)]
            pgrp = grp["%d"%(plane+1)]
            old_name = "area%d_plane%d" % (subarea+1, plane+1)
            frame_idx = pgrp["sourceFileFrameIdx"]["sourceFileFrameIdx"].value
            # lst = pgrp["sourceFileList"]
            lst = parse_h5_obj(pgrp["sourceFileList"])[0]
            for k in lst:
                # srcfile = str(lst[k][k].value)
                srcfile = str(k)
                add_plane_map_entry(old_name, srcfile)
                break
                
# fetch start time/date of experiment
def find_exp_time(ifile):
    meta = parse_h5_obj(ifile['metaDataHash/value'])[0]
    d = meta[10]
    t = meta[11]
    # d = ifile['metaDataHash/value/11/11'][0][0]
    #    t = ifile['metaDataHash/value/12/12'][0][0]
    dt=datetime.datetime.strptime(d+t, "%Y%m%d%H%M%S")
    return dt.strftime("%a %b %d %Y %H:%M:%S")

# create 2-photon time series, pointing to specified filename
# use junk values for 2-photon metadata, for now at least
# This version no longer used.   It creates new timeseries for each file
# def create_2p_ts(simon, name, fname, stack_t, plane_name):
#     #- twop = simon.create_timeseries("TwoPhotonSeries", name, "acquisition")
#     twop = simon.make_group("<TwoPhotonSeries>", name, path='/acquisition/timeseries', attrs={
#         "source": "Device 'two-photon microscope'",
#         "description": "2P image stack, one of many sequential stacks for this field of view"})
#     twop.set_dataset("format", "external")
#     # need to convert name to utf8, otherwise error generated:
#     # TypeError: No conversion path for dtype: dtype('<U91').  Added by jt.
#     fname_utf =  fname.encode('utf8')
#     twop.set_dataset("external_file", [fname_utf], attrs={"starting_frame": [0]})
#     twop.set_dataset("dimension", [512, 512])
#     #twop.set_value("pmt_gain", 1.0)
#     twop.set_dataset("scan_line_rate", 16000.0)
#     twop.set_custom_dataset("channel_name", name+"_red and "+name+"_green")
#     twop.set_dataset("field_of_view", [ 600e-6, 600e-6 ])
#     twop.set_dataset("imaging_plane", plane_name)
#     twop.set_dataset("timestamps", stack_t)
#     # twop.set_dataset("data", np.zeros(1), attrs={
#     #    'unit': "None", 'conversion': 1.0, 'resolution': 1.0})
#     # twop.finalize()

# create 2-photon time series, with array of filenames in external_file    
def create_2p_tsa(simon, plane_name, external_file, starting_frame, timestamps):
    twop = simon.make_group("<TwoPhotonSeries>", nname, path='/acquisition/timeseries', attrs={
        "source": "Device 'two-photon microscope'",
        "description": "2P image stack, one of many sequential stacks for this field of view"})
    twop.set_dataset("format", "external")
    # need to convert name to utf8, otherwise error generated:
    # TypeError: No conversion path for dtype: dtype('<U91').  Added by jt.
    # fname_utf =  fname.encode('utf8')
    twop.set_dataset("external_file", external_file, attrs={"starting_frame": starting_frame})
    twop.set_dataset("dimension", [512, 512])
    #twop.set_value("pmt_gain", 1.0)
    twop.set_dataset("scan_line_rate", 16000.0)
    twop.set_custom_dataset("channel_name", name+"_red and "+name+"_green")
    twop.set_dataset("field_of_view", [ 600e-6, 600e-6 ])
    twop.set_dataset("imaging_plane", plane_name)
    twop.set_dataset("timestamps", timestamps)

# save frames for 2-photon series.  These are used in routine create_2p_tsa
def save_2p_frames(external_file, starting_frame, timestamps, fname, stack_t):
    starting_frame.append(len(timestamps))
    timestamps.extend(stack_t)
    external_file.append(fname.encode('utf8'))
    

# define generic manifold
manifold = np.zeros((512, 512, 3))
for i in range(512):
    for j in range(512):
        manifold[i][j][0] = 1.0 * i
        manifold[i][j][1] = 1.0 * j
        manifold[i][j][2] = 0.0

def define_imaging_plane_red(bfile, plane_name):
    name = plane_name + "_red"
    og = bfile.make_group("optophysiology", abort=False)
    ipr = og.make_group("<imaging_plane_X>", name)
    ipr.set_dataset("excitation_lambda", "1000 nm")
    ipr.set_dataset("indicator",  "GCaMP; BG22")
    ipr.set_dataset("imaging_rate", "16KHz (scan line rate)")
    ipr.set_dataset("manifold", manifold, attrs= { "note":
        "Manifold provided here is place-holder. Need to determine actual pixel location"})
    

def define_imaging_plane_green(bfile, plane_name):
    name = plane_name + "_green"
    og = bfile.make_group("optophysiology", abort=False)
    ipg = og.make_group("<imaging_plane_X>", name)
    ipg.set_dataset("excitation_lambda", "1000 nm")
    ipg.set_dataset("indicator",  "mCherry; 657/70 emission filter")
    ipg.set_dataset("imaging_rate", "16KHz (scan line rate)")
    ipg.set_dataset("manifold", manifold, attrs= { "note":
        "Manifold provided here is place-holder. Need to determine actual pixel location"})


# create raw data timeseries
# use junk values resolution for now
# def create_aq_ts(simon, name, modality, timestamps, rate, data, comments = '', descr = '', link = 0):
#     zab = simon.create_timeseries("TimeSeries", name, modality)
#     if link == 0:
#         zab.set_time(timestamps)
#     else:
#         zab.set_time_as_link(timestamps)
#     zab.set_data(data, "Zaber motor steps", 0.1, 1)
#     zab.set_comments(comments)
#     zab.set_description(descr)
#     zab.finalize()

# pull out masterImage arrays and create entries for each in
#   /acquisition/images
# masterImages are store in:
#        tsah::descrHash::[2-7]::value::1::[1-3]::masterImage
# each image has 2 color channels, green and red
reference_image_red = {}
reference_image_green = {}
def create_reference_image(orig_h5, simon, area, plane, num_plane = 3):
    area_grp = orig_h5["timeSeriesArrayHash/descrHash"]["%d"%(1+area)]
    if num_plane == 1:
        plane_grp = area_grp["value/1"]
    else:
        plane_grp = area_grp["value/1"]["%d"%(plane)]
    master = plane_grp["masterImage"]["masterImage"].value
    green = np.zeros((512, 512))
    red = np.zeros((512, 512))
    for i in range(512):
        for j in range(512):
            green[i][j] = master[i][j][0]
            red[i][j] = master[i][j][1]
    # convert from file-specific area/plane mapping to
    #   inter-session naming convention
    #image_plane = "area%d_plane%d" % (area, plane)
    oname = "area%d_plane%d" % (area, plane)
    image_plane = plane_map[oname]
    name = image_plane + "_0001"
    fmt = "raw"
    desc = "Master image (green channel), in 512x512, 8bit"
    #- simon.create_reference_image(green, name, fmt, desc, 'uint8')
    simon.set_dataset("<image_X>", green, name=name, dtype='uint8', attrs={
        'description':desc, 'format': fmt})
    reference_image_green[image_plane] = green
    name = image_plane + "_0002"
    desc = "Master image (red channel), in 512x512, 8bit"
    #- simon.create_reference_image(red, name, fmt, desc, 'uint8')
    simon.set_dataset("<image_X>", red, name=name, dtype='uint8', attrs={
        'description':desc, 'format': fmt})    
    reference_image_red[image_plane] = red

# pull out all ROI pixel maps for a particular subarea and imaging plane
#   and store these in the segmentation module
def fetch_rois(orig_h5, seg_iface, area, plane, num_planes=3):
    tsah = orig_h5["timeSeriesArrayHash"]
    # convert from file-specific area/plane mapping to
    #   inter-session naming convention
    #image_plane = "area%d_plane%d" % (area, plane)
    oname = "area%d_plane%d" % (area, plane)
    image_plane = plane_map[oname]
    #- seg_iface.create_imaging_plane(image_plane, image_plane)
    sip = seg_iface.make_group("<image_plane>", image_plane)
    sip.set_dataset("imaging_plane_name",  image_plane)
    sip.set_dataset("description",  image_plane)
    # first get the list of ROIs for this subarea and plane
    # if num_planes == 1:
    #         ids = tsah["value"]["%d"%(area+1)]["imagingPlane"]["ids"]
    #     else:
    #         ids = tsah["value"]["%d"%(area+1)]["imagingPlane"]["%d"%plane]["ids"]
    ids = tsah["value"]["%d"%(area+1)]["imagingPlane"]["%d"%plane]["ids"]
    roi_ids = ids["ids"].value
    lookup = tsah["value"]["%d"%(area+1)]["ids"]["ids"].value
    for i in range(len(roi_ids)):
        rid = roi_ids[i]
        if num_planes == 1:
            rois = tsah["descrHash"]["%d"%(area+1)]["value"]["1"]
        else:
            rois = tsah["descrHash"]["%d"%(area+1)]["value"]["1"]["%d"%plane]
        # make sure the ROI id is correct
        record = rois["rois"]["%s"%(1+i)]
        x = int(parse_h5_obj(record["id"])[0])
        assert x == int(rid)
        pix = parse_h5_obj(record["indicesWithinImage"])[0]
        # pix = record["indicesWithinImage/indicesWithinImage"].value
        pixmap = []
        for j in range(len(pix)):
            v = pix[j]
            px = int(v / 512)
            py = int(v) % 512
            pixmap.append([py,px])
        weight = np.zeros(len(pixmap)) + 1.0
        #- seg_iface.add_roi_mask_pixels(image_plane, "%d"%x, "ROI %d"%x, pixmap, weight, 512, 512)
        ut.add_roi_mask_pixels(seg_iface, image_plane, "%d"%x, "ROI %d"%x, pixmap, weight, 512, 512)


# map between ROI ID in imaging plane and dF/F row valueMatrix:
#        tsah::value::[2-7]::ids::ids
# map of ROI IDs per imaging plane:
#        tsah::value::[2-7]::imagingPlane::[1-3]::ids::ids
# time for dF/F samples
#        tsah::value::[2-7]::valueMatrix
def fetch_dff(orig_h5, dff_iface, seg_iface, area, plane, num_planes=3):
    area_grp = orig_h5["timeSeriesArrayHash/value"]["%d"%(area+1)]
    # if num_planes == 1:
    #         plane_ids = area_grp["imagingPlane"]["ids/ids"].value
    #     else:
    #         plane_ids = area_grp["imagingPlane"]["%d"%plane]["ids/ids"].value
    plane_ids = area_grp["imagingPlane"]["%d"%plane]["ids/ids"].value
    area_ids = area_grp["ids/ids"].value
    # store dff in matrix and supply that to time series
    dff_data = area_grp["valueMatrix/valueMatrix"].value
    # convert from file-specific area/plane mapping to
    #   inter-session naming convention
    oname = "area%d_plane%d" % (area, plane)
    image_plane = plane_map[oname]
    t = area_grp["time/time"].value * 0.001
    # create array of ROI names for each matrix row
    roi_names = []
    trial_ids = area_grp["trial/trial"].value
    # for each plane ID, find group idx. df/f is idx'd row in values
    for i in range(len(plane_ids)):
        roi_names.append("ROI%d"%plane_ids[i])
    dff_ts = dff_iface.make_group("<RoiResponseSeries>", image_plane)
    dff_ts.set_dataset("data", dff_data, attrs={"unit":"dF/F",
        "conversion": 1.0, "resolution":0.0})
    dff_ts.set_dataset("timestamps", t)
    dff_ts.set_dataset("roi_names", roi_names)
    #- dff_ts.set_value_as_link("segmentation_interface", seg_iface)
    dff_ts.make_group("segmentation_interface", seg_iface)
    trial_ids = area_grp["trial/trial"].value
    dff_ts.set_custom_dataset("trial_ids", trial_ids)
    #- dff_iface.add_timeseries(dff_ts)


# licks
# BehavioralEvent (lick_left)
# BehavioralEvent (lick_right)
def read_licks(orig_h5, simon):
    mod_name = "Licks"
    mod = simon.make_group("<Module>", mod_name)
    mod.set_custom_dataset("description", "Lickport contacts, right and left")
    lick_iface = mod.make_group("BehavioralEvents", attrs={
        "source": "Lick Times as reported in Simon's data file"})
    # left lick is H5 channel 3
    grp3 = orig_h5["eventSeriesArrayHash/value/3"]
    t = grp3["eventTimes/eventTimes"].value * 0.001
    # there's no meaningful entries to store in data[], as events are binary
    # store a 1
    ts_left = lick_iface.make_group("<TimeSeries>", "lick_left", attrs={
        "description": "Left lickport contact times (beam breaks left)",
        "source": "Times as reported in Simon's data file",
        "comments": "Timestamp array stores lick times"})
    data = np.zeros(len(t))
    data += 1
    ts_left.set_dataset("data", data, attrs={"unit":"Licks",
        "conversion": 1.0, "resolution": 1.0})
    ts_left.set_dataset("timestamps", t)
    # right lick is H5 channel 4
    grp4 = orig_h5["eventSeriesArrayHash/value/4"]
    t = grp4["eventTimes/eventTimes"].value * 0.001
    # there's no meaningful entries to store in data[], as events are binary
    # store a '1'
    ts_right = lick_iface.make_group("<TimeSeries>", "lick_right", attrs={
        "description": "Right lickport contact times (beam breaks right)",
        "source": "Times as reported in Simon's data file",
        "comments": "Timestamp array stores lick times"})
    data = np.zeros(len(t))
    data += 1
    ts_right.set_dataset("data", data, attrs={"unit":"Licks",
        "conversion": 1.0, "resolution": 1.0})
    ts_right.set_dataset("timestamps", t)

        

# time is stored in tsah::value::1::time::time
# angle is stored in tsah::value::1::valueMatrix::valueMatrix[0[
# curvature is stored in tsah::value::1::valueMatrix::valueMatrix[1[
def read_whisker(orig_h5, simon):
    grp = orig_h5["timeSeriesArrayHash/value/1"]
    t = grp["time/time"].value * 0.001
    val = grp["valueMatrix/valueMatrix"].value
    angle = val[0]
    curv = val[1]
    # create module
    mod_name = "Whisker"
    mod = simon.make_group("<Module>", mod_name)
    mod.set_custom_dataset("description", "Whisker angle and curvature (relative) of the whiskers and times when the pole was touched by whiskers")
#    mod.set_source("Data as reported in Simon's data file")
    whisker_iface = mod.make_group("BehavioralTimeSeries", attrs={
        "source": "Whisker data as reported in Simon's data file"})
    descr = parse_h5_obj(grp["idStrs"])[0]
    # added by jt to fix bug, with array being stored in descr
#     if isinstance(descr, (list, tuple, np.ndarray)):
#         descr = descr[0]
    # whisker angle
    ts_angle = whisker_iface.make_group("<TimeSeries>", "whisker_angle", attrs={
        "description": descr[0],
        "source": "Whisker angle as reported in Simon's data file"})
    ts_angle.set_dataset("data", angle, attrs={ "unit": "degrees",
        "conversion":1.0, "resolution":0.001})
    ts_angle.set_dataset("timestamps", t)
    # whisker curvature
    ts_curve = whisker_iface.make_group("<TimeSeries>", "whisker_curve", attrs={
        "description": descr[1], "source": "Curvature as reported in Simon's data file"})
    ts_curve.set_dataset("data", curv, attrs={"unit":"Unknown",
        "conversion": 1.0, "resolution": 1.0})
    ts_curve.set_dataset("timestamps", t)
    ####################################################################
    # extracted from read_pole_position
    # pole touch is H5 channel 2
    grp2 = orig_h5["eventSeriesArrayHash/value/2"]
    pole_iface = mod.make_group("BehavioralEpochs", attrs={
        "source": "Pole intervals as reported in Simon's data file"})
    # protraction touches
    t = grp2["eventTimes/1/1"].value * 0.001
    # times are stored as 'on' in even intervals, 'off' in odd intervals
    on_off = np.zeros(len(t))
    on_off += -1
    on_off[::2] *= -1
    pole_touch =  pole_iface.make_group("<IntervalSeries>", "pole_touch_protract")
    kappa_ma_path = "eventSeriesArrayHash/value/2/eventPropertiesHash/1/value/2/2"
    kappa_ma = orig_h5[kappa_ma_path].value
    pole_touch.set_custom_dataset("kappa_max_abs_over_touch", kappa_ma)
    pole_touch.set_dataset("timestamps", t)
    pole_touch.set_dataset("data", on_off)
    pole_touch.set_attr("description", "Intervals that whisker touches pole (protract)")
    pole_touch.set_attr("source", "Intervals are as reported in Simon's data file")
    # retraction touches
    t = grp2["eventTimes/2/2"].value * 0.001
    # times are stored as 'on' in even intervals, 'off' in odd intervals
    on_off = np.zeros(len(t))
    on_off += -1
    on_off[::2] *= -1
    pole_touch = pole_iface.make_group("<IntervalSeries>", "pole_touch_retract")
    kappa_ma_path = "eventSeriesArrayHash/value/2/eventPropertiesHash/2/value/2/2"
    kappa_ma = orig_h5[kappa_ma_path].value
    pole_touch.set_custom_dataset("kappa_max_abs_over_touch", kappa_ma)
    pole_touch.set_dataset("timestamps", t)
    pole_touch.set_dataset("data", on_off)
    pole_touch.set_attr("description", "Intervals that whisker touches pole (retract)")
    pole_touch.set_attr("source", "Intervals are as reported in Simon's data file")
    #- pole_iface.add_timeseries(pole_touch)
    #
    #-mod.finalize()

# trial start times are stored in: h5::trialStartTimes::trialStartTimes
def create_trials(orig_h5, simon):
    trial_id = orig_h5["trialIds/trialIds"].value
    trial_t = orig_h5["trialStartTimes/trialStartTimes"].value * 0.001
    # trial stop isn't stored. assume that it's twice the duration of other
    #   trials -- padding on the high side shouldn't matter
    ival = (trial_t[-1] - trial_t[0]) / (len(trial_t) - 1)
    trial_t = np.append(trial_t, trial_t[-1] + 2*ival)
    for i in range(len(trial_id)):
        tid = trial_id[i]
        trial = "Trial_%d%d%d" % (int(tid/100), int(tid/10)%10, tid%10)
        start = trial_t[i]
        stop = trial_t[i+1]
        #- epoch = simon.create_epoch(trial, start, stop)
        epoch = simon.make_group("<epoch_X>", trial)
        epoch.set_dataset("start_time", start)
        epoch.set_dataset("stop_time", stop)
        # pole_pos_path = "trialPropertiesHash/value/3/3"
        #         pole_pos = str(orig_h5[pole_pos_path].value[i])
        #         epoch.description = ("Stimulus position - in Zaber motor steps (approximately, 10,000 = 1 mm): " + pole_pos)
        if trial in epoch_roi_list:
            epoch.set_custom_dataset("ROIs", epoch_roi_list[trial])
            epoch.set_custom_dataset("ROI_planes", epoch_roi_planes[trial])
        tags = []
        if trial in epoch_trial_types:
            for j in range(len(epoch_trial_types[trial])):
                #- epoch.add_tag(epoch_trial_types[trial][j])
                tags.append(epoch_trial_types[trial][j])
        epoch.set_dataset("tags", tags)
        epoch.set_dataset("description", "Data that belong to " + trial)
        ts = "/processing/Licks/BehavioralEvents/lick_left"
        #- epoch.add_timeseries("lick_left", ts)
        ut.add_epoch_ts(epoch, start, stop, "lick_left", ts)
        ts = "/processing/Licks/BehavioralEvents/lick_right"
        ut.add_epoch_ts(epoch, start, stop, "lick_right", ts)
        ts = "/stimulus/presentation/water_left"
        ut.add_epoch_ts(epoch, start, stop, "water_left", ts)
        ts = "/stimulus/presentation/water_right"
        ut.add_epoch_ts(epoch, start, stop, "water_right", ts)
        ts = "/stimulus/presentation/pole_accessible"
        ut.add_epoch_ts(epoch, start, stop, "pole_accessible", ts)
        ts = "/processing/Whisker/BehavioralEpochs/pole_touch_protract"
        ut.add_epoch_ts(epoch, start, stop, "pole_touch_protract", ts)
        ts = "/processing/Whisker/BehavioralEpochs/pole_touch_retract"
        ut.add_epoch_ts(epoch, start, stop, "pole_touch_retract", ts)
        ts = "/stimulus/presentation/auditory_cue"
        ut.add_epoch_ts(epoch, start, stop, "auditory_cue", ts)
        ts = "/processing/Whisker/BehavioralTimeSeries/whisker_angle"
        ut.add_epoch_ts(epoch, start, stop, "whisker_angle", ts)
        ts = "/processing/Whisker/BehavioralTimeSeries/whisker_curve"
        ut.add_epoch_ts(epoch, start, stop, "whisker_curve", ts)
        #- epoch.finalize()

# each subarea has list of trials and ROI ids
# to parse, take each subarea, pull out trials
#   foeach trial, write ROI
#   to get plane, find ROI in imaging plane
# store list of ROIs and planes for later inclusion into epochs
epoch_roi_list = {}
epoch_roi_planes = {}
def create_trial_roi_map(orig_h5, simon):
    fp = simon.file_pointer
    num_subareas = len(orig_h5['timeSeriesArrayHash/descrHash'].keys()) - 1
    for i in range(num_subareas):
        area = i + 1
        grp_name = "timeSeriesArrayHash/value/%d" % (area + 1)
        block = orig_h5[grp_name]
        trials = block["trial/trial"].value
        ids = block["ids/ids"].value
        # create way to map ROI onto plane
        planemap = {}
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(area + 1)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for j in range(num_planes):
            plane = j + 1
            # if num_planes == 1:
            #                 grp_name = "imagingPlane/ids/ids" 
            #             else:
            #                 grp_name = "imagingPlane/%d/ids/ids" % plane
            grp_name = "imagingPlane/%d/ids/ids" % plane
            plane_id = block[grp_name].value
            for k in range(len(plane_id)):
                planemap["%d"%plane_id[k]] = "%d" % plane
        trial_list = {}
        for j in range(len(trials)):
            tid = trials[j]
            name = "Trial_%d%d%d" % (int(tid/100), int(tid/10)%10, tid%10)
            #name = "Trial_%d" % trials[j]
            if name not in trial_list:
                trial_list[name] = j
        for trial_name in trial_list.keys():
            roi_list = []
            plane_list = []
            valid_whisker = get_valid_trials(orig_h5, "whisker")
            valid_Ca = get_valid_trials(orig_h5, "Ca")
            for k in range(len(ids)):
                roi = "%d" % ids[k]
                plane = int(planemap[roi])
                # convert from file-specific area/plane mapping to
                #   inter-session naming convention
                #imaging_plane = "area%d_plane%d" % (area, plane)
                oname = "area%d_plane%d" % (area, plane)
                imaging_plane = plane_map[oname]
                roi_list.append(ids[k])
                plane_list.append(imaging_plane)
            epoch_roi_list[trial_name] = roi_list
            epoch_roi_planes[trial_name] = plane_list

epoch_trial_types = {}
def get_trial_types(orig_h5, simon):
    fp = simon.file_pointer
    trial_id = orig_h5["trialIds/trialIds"].value
    trial_types_all = []
    trial_type_strings = parse_h5_obj(orig_h5['trialTypeStr'])[0]
    valid_whisker = get_valid_trials(orig_h5, "whisker")
    valid_Ca = get_valid_trials(orig_h5, "Ca")
    # collect all trials (strings)
    for i in range(6):
        trial_types_all.append(str(trial_type_strings[i]))
    # write specific entries for the given trial
    for i in range(len(trial_id)):
        tid = trial_id[i]
        trial_name = "Trial_%d%d%d" % (int(tid/100), int(tid/10)%10, tid%10)
        #trial_name = 'Trial_%d' % trial_id[i]
        trial_types = []
        trial_type_mat = parse_h5_obj(orig_h5['trialTypeMat'])[0]
        for j in range(6):
            if trial_type_mat[j,i] == 1:
                trial_types.append(trial_types_all[j])
        if i in valid_whisker:
            trial_types.append("Valid whisker data")
        else:
            trial_types.append("Invalid whisker data")
        if i in valid_Ca:
            trial_types.append("Valid Ca data")
        else:
            trial_types.append("Invalid Ca data")
        epoch_trial_types[trial_name] = trial_types
        
        
def get_valid_trials(orig_h5, data):
    ts_path = "timeSeriesArrayHash/descrHash/"
    val = []
    num_subareas = len(orig_h5['timeSeriesArrayHash/descrHash'].keys()) - 1
    if data == "whisker":
        ids = parse_h5_obj(orig_h5[ts_path + '1/value'])[0]
        # ids = list(orig_h5[ts_path + "1/value/value"].value)
        val = val + list(ids)
        val = list(Set(val))
    if data == "Ca":
        for i in range(2,num_subareas+1):
            ids_path = ts_path + "%d/value/2" % i
            ids = parse_h5_obj(orig_h5[ids_path])[0]
            # ids = list(orig_h5[ids_path].value)
            val = val + list(ids)
        val = list(Set(val))
    return val
        

########################################################################
########################################################################
########################################################################

#ep.ts_self_check()
#sys.exit(0)

for i in range(len(file_list)):
    fname = file_list[i][len(path):]
    INFILE = file_list[i]
    print INFILE
    orig_h5 = h5py.File(INFILE, "r")
    session_id = fname[0:-3]

    # each of simon's hdf5 files have imaging planes and subareas
    #   labels consistent within the file, but inconsistent between
    #   files. create a map between the h5 plane name and the 
    #   identifier used between files
    plane_map = {}
    create_plane_map()

    # create output file
    file_name = OUTPUT_DIR + session_id + ".nwb"
    print file_name
    vargs = {}
    vargs["file_name"] = file_name
    vargs["start_time"] = find_exp_time(orig_h5)
    vargs["identifier"] = ut.create_identifier(session_id)
    vargs["description"] = "Two-photon imaging of mouse barrel cortex in discrimination task (lick left/right) using pole and auditory stimulus"
    vargs["mode"] = "w"
    #--  simon = nwb.NWB(**vargs)
    simon = nwb_file.open(**vargs)
   

    #- simon.set_metadata(SESSION_ID, session_id)
    #- simon.set_metadata(DEVICE("two-photon microscope"), "Custom two-photon microscope, see http://openwiki.janelia.org/wiki/display/shareddesigns/MIMMS. Images acquired using 16X 0.8 NA objective (Nikon)")

    gg = simon.make_group("general", abort=False)
    gg.set_dataset("session_id", session_id)
    gd = gg.make_group("devices")
    desc = "Custom two-photon microscope, see http://openwiki.janelia.org/wiki/display/shareddesigns/MIMMS. Images acquired using 16X 0.8 NA objective (Nikon)"
    gd.set_dataset("<device_X>", desc, name="two-photon microscope")
    sg = gg.make_group("subject")

    print "Reading meta data"
    meta = parse_h5_obj(orig_h5['metaDataHash/value'])[0]
    species = meta[0]
    # species = orig_h5["metaDataHash/value/1/1"].value[0,0]
    sg.set_dataset("species", species)
    exp_type = meta[1]
    # exp_type = orig_h5["metaDataHash/value/2/2"].value[0,0]
    gg.set_dataset("notes", exp_type)
    an_strain1 = meta[2]
    an_strain2 = meta[5]
    # an_strain1 = orig_h5["metaDataHash/value/3/3"].value[0,0]
    # an_strain2 = orig_h5["metaDataHash/value/6/6"].value[0,0]
    an_strain = "animalStrain1: " + an_strain1 + "; animalStrain2: " + an_strain2
    an_source1 = meta[3]
    an_source2 = meta[6]
    # an_source1 = orig_h5["metaDataHash/value/4/4"].value[0,0]
    # an_source2 = orig_h5["metaDataHash/value/7/7"].value[0,0]
    an_source = "animalSource1: " + an_source1 + "; animalSource2: " + an_source2
    subject = an_strain + ";\n" + an_source
    sg.set_dataset("description", subject)
    an_gene_mod1 = meta[4]
    an_gene_mod2 = meta[7]
    # an_gene_mod1 = orig_h5["metaDataHash/value/5/5"].value[0,0]
    # an_gene_mod2 = orig_h5["metaDataHash/value/8/8"].value[0,0]
    an_gene_mod  = "animalGeneModification1: " + an_gene_mod1 + "; animalGeneModification2: " + an_gene_mod2
    sg.set_dataset("genotype", an_gene_mod)
    an_id = meta[8]
    # an_id = orig_h5["metaDataHash/value/9/9"].value[0,0]
    sg.set_dataset("subject_id", an_id)
    sex = meta[9]
    # sex = orig_h5["metaDataHash/value/10/10"].value[0,0]
    sg.set_dataset("sex", sex)
    experimenters = meta[12]
    # experimenters = orig_h5["metaDataHash/value/13/13"].value[0,0]
    gg.set_dataset("experimenter", experimenters)
    gg.set_dataset("lab", "Svoboda lab")
    gg.set_dataset("institution", "Janelia Farm")
    gg.set_dataset("experiment_description", ut.load_file(path + "svoboda_files/experiment_description.txt"))
    gg.set_dataset("surgery", ut.load_file(path + "svoboda_files/surgery.txt"))
    gg.set_dataset("data_collection", ut.load_file(path + "svoboda_files/data_collection.txt"))


    print "Reading time series"
    read_whisker(orig_h5, simon)
    read_licks(orig_h5, simon)
    
    pole_pos_path = "trialPropertiesHash/value/3/3"
    pole_pos = parse_h5_obj(orig_h5[pole_pos_path])[0]
    trial_t = orig_h5["trialStartTimes/trialStartTimes"].value * 0.001
    rate = (trial_t[-1] - trial_t[0])/(len(trial_t)-1)
    comments = parse_h5_obj(orig_h5["trialPropertiesHash/keyNames"])[0][2]
    descr = parse_h5_obj(orig_h5["trialPropertiesHash/descr"])[0][2]
    zts = simon.make_group("<TimeSeries>", "zaber_motor_pos", path="/stimulus/presentation")
    zts.set_dataset("timestamps", trial_t)
    zts.set_dataset("data", pole_pos, attrs={"unit":"unknown",
        "conversion": 1.0, "resolution":1.0})
    zts.set_attr("description", str(descr))
    zts.set_attr("comments", (str(comments)))
    #- zts.finalize()
    
    pole_acc = simon.make_group("<IntervalSeries>", "pole_accessible", path="/stimulus/presentation")
    grp1 = orig_h5["eventSeriesArrayHash/value/1"]
    time = grp1["eventTimes/eventTimes"].value * 0.001
    # create dummy data: 1 for 'on', -1 for 'off'
    on_off = np.zeros(len(time))
    on_off += -1
    on_off[::2] *= -1
    pole_acc.set_dataset("data", on_off)
    pole_acc.set_attr("description", "Intervals that pole is accessible")
    pole_acc.set_dataset("timestamps", time)
    pole_acc.set_attr("source", "Intervals are as reported in Simon's data file")
    #- pole_acc.finalize()    
    
    aud_cue_ts = simon.make_group("<IntervalSeries>", "auditory_cue", path="/stimulus/presentation")
    grp7 = orig_h5["eventSeriesArrayHash/value/7"]
    time = grp7["eventTimes/eventTimes"].value * 0.001
    # create dummy data: 1 for 'on', -1 for 'off'
    on_off = np.zeros(len(time))
    on_off += -1
    on_off[::2] *= -1
    aud_cue_ts.set_dataset("data", on_off)
    aud_cue_ts.set_attr("description", "Intervals when auditory cue presented")
    aud_cue_ts.set_dataset("timestamps", time)
    aud_cue_ts.set_attr("source", "Intervals are as reported in Simon's data file")
    #- aud_cue_ts.finalize()
    
    water_left_ts = simon.make_group("<IntervalSeries>", "water_left", path="/stimulus/presentation")
    grp5 = orig_h5["eventSeriesArrayHash/value/5"]
    time = grp5["eventTimes/eventTimes"].value * 0.001
    # create dummy data: 1 for 'on', -1 for 'off'
    on_off = np.zeros(len(time))
    on_off += -1
    on_off[::2] *= -1
    water_left_ts.set_dataset("data", on_off)
    water_left_ts.set_attr("description", "Intervals for left water reward delivery")
    water_left_ts.set_dataset("timestamps", time)
    water_left_ts.set_attr("source", "Intervals are as reported in Simon's data file")
    #- water_left_ts.finalize()
    
    water_right_ts = simon.make_group("<IntervalSeries>", "water_right", path="/stimulus/presentation")
    grp6 = orig_h5["eventSeriesArrayHash/value/6"]
    time = grp6["eventTimes/eventTimes"].value * 0.001
    # create dummy data: 1 for 'on', -1 for 'off'
    on_off = np.zeros(len(time))
    on_off += -1
    on_off[::2] *= -1
    water_right_ts.set_dataset("data", on_off)
    water_right_ts.set_attr("description", "Intervals for right water reward delivery")
    water_right_ts.set_dataset("timestamps", time)
    water_right_ts.set_attr("source", "Intervals are as reported in Simon's data file")
    #- water_right_ts.finalize()

    print "Creating map between trials and ROIs"
    create_trial_roi_map(orig_h5, simon)
    
    print "Creating epochs"
    get_trial_types(orig_h5, simon)
    create_trials(orig_h5, simon)

    # store master images
    print "Creating reference images"
    num_subareas = len(orig_h5['timeSeriesArrayHash/descrHash'].keys()) - 1
    for subarea in range(num_subareas):
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            sys.stdout.write('_')
    print ""
    for subarea in range(num_subareas):
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            create_reference_image(orig_h5, simon, subarea+1, plane+1, num_planes)
            sys.stdout.write('.')
            sys.stdout.flush()
    print ""
    # create empty time series for whisker video
    whisker_vid = simon.make_group("<ImageSeries>", "whisker_video", path="/acquisition/timeseries")
    whisker_vid.set_dataset("format", "unknown");
    whisker_vid.set_dataset("external_file", ["whisker_data.tar.gz"], attrs={"starting_frame": [0]})
    #whisker_vid.set_value("bits_per_pixel", 16)
    whisker_vid.set_dataset("dimension", [1024, 1024])
    whisker_vid.set_attr("description", "Place-holder for whisker tracking video. Video information and timestamps not available")
    # whisker_vid.set_dataset("timestamps", [0])
    whisker_vid.set_dataset("timestamps", "extlink:external_timestamps_link,/path/to/timestamps")
    # must set number of samples explicitly
    whisker_vid.set_dataset("num_samples", 0)
#     whisker_vid.set_dataset("data", [0], attrs={"unit":"n/a", 
#         "resolution":float('nan'), "conversion":1.0})
    #- whisker_vid.finalize()
    
    # TODO define manifolds

    mod_name = "ROIs"
    mod = simon.make_group("<Module>", mod_name)
    mod.set_custom_dataset("description", "Segmentation (pixel-lists) and dF/F (dffTSA) for all ROIs")
    #mod.set_source("2Photon time series under acquisition are the bases for these ROIs. Those time series are named similarly to the image planes")
    dff_iface = mod.make_group("DfOverF")
    dff_iface.set_attr("source", "This module's ImageSegmentation interface")
    seg_iface = mod.make_group("ImageSegmentation", attrs={"source": "Simon's datafile"})
    # pull out image segmentation data. do it by subarea and imaging plane,
    #   as that's how data is stored in the source file
    print "Reading ROI and dF/F"
    for subarea in range(num_subareas):
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            sys.stdout.write('_')
    print ""
    for subarea in range(num_subareas):
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            fetch_rois(orig_h5, seg_iface, subarea+1, plane+1, num_planes)
            fetch_dff(orig_h5, dff_iface, seg_iface, subarea+1, plane+1, num_planes)

            sys.stdout.write('.')
            sys.stdout.flush()
    print ""
    print "Writing ROI and dF/F"
    #- mod.finalize()

    print "Defining imagine planes"
    # define imaging planes in general
    for subarea in range(num_subareas):
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            # get plane name and map it to stable inter-experiment name
            oname = "area%d_plane%d" % (subarea+1, plane+1)
            define_imaging_plane_red(simon, plane_map[oname])
            define_imaging_plane_green(simon, plane_map[oname])

    # add reference images to image segmentation
    # TODO
    for k in plane_map.keys():
        plane = plane_map[k]
        img = reference_image_red[plane]
        #- seg_iface.add_reference_image(plane, "%s_0002"%plane, img)
        ut.add_reference_image(seg_iface, plane, "%s_0002"%plane, img)
        img = reference_image_green[plane]
        #- seg_iface.add_reference_image(plane, "%s_0001"%plane, img)
        ut.add_reference_image(seg_iface, plane, "%s_0001"%plane, img)


    # generate time series for /acquisition
    # data is categorized into 7 chunks -- 6 are 2photon subareas and 1 is
    #   whisker data
    # process 2photon here
    # image stack file links stored in:
    #   timeSeriesArrayHash
    #        value
    #            2-7
    #                imagingPlane
    #                    1-3
    #                        sourceFileList
    print "Creating entries for source .tif"
    for subarea in range(num_subareas):
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            sys.stdout.write('_')
    print ""
    for subarea in range(num_subareas):
        # fetch time array
        grp = orig_h5["timeSeriesArrayHash"]["value"]["%d"%(subarea+2)]
        t = 0.001 * grp["time"]["time"].value
        # now move into imaging plane group, to generate time series for 
        #   2photon image stacks
        grp = grp["imagingPlane"]
        plane_path = 'timeSeriesArrayHash/descrHash/%d/value/1' %(subarea + 2)
        if orig_h5[plane_path].keys()[0] == 'masterImage':
            num_planes = 1
        else:
            num_planes = len(orig_h5[plane_path].keys())
        for plane in range(num_planes):
            # if num_planes == 1:
            #                 pgrp = grp
            #             else:
            #                 pgrp = grp["%d"%(plane+1)]
            pgrp = grp["%d"%(plane+1)]
            frame_idx = pgrp["sourceFileFrameIdx"]["sourceFileFrameIdx"].value
            lst = parse_h5_obj(pgrp["sourceFileList"])[0]
            cnt = 0
            srcfile = {}
            for k in range(len(lst)):
                srcfile[str(k+1)] = lst[k]
                cnt += 1
            filemap = {}
            lastfile =-1 
            lastframe = 1
            stack_t = []
            nname = None
            fname = None
            zero = np.zeros(1)
            assert len(t) == len(frame_idx[0])
            # following arrays used to make external_file as an array, reducing number of image_series
            external_file = []
            starting_frame = []
            timestamps = []
            for i in range(len(frame_idx[0])):
                filenum = frame_idx[0][i]
                if lastfile < 0:
                    lastfile = filenum
                framenum = frame_idx[1][i]
                stack_t.append(t[i])
                # check for embedded NaNs
                if np.isnan(filenum):
                    continue
                if np.isnan(framenum):
                    continue
                # use fname as a flag. if it's not None then there's data
                #   to write
                if fname is None:
                    # convert from file-specific area/plane mapping to
                    #   inter-session naming convention
                    oname = "area%d_plane%d" % (subarea+1, plane+1)
                    nname = plane_map[oname]
                    name = "%s_%d" % (nname, filenum)
                    fname = srcfile["%d"%filenum]
                # make sure frames and file numbers are sequential
                assert (lastfile == filenum and framenum == lastframe+1) or framenum == 1
                if lastfile != filenum:
                    if i>0:
                        if not np.isnan(frame_idx[0][i-1] ) and not np.isnan(frame_idx[1][i-1]):
                            # create_2p_ts(simon, name, fname, stack_t, nname)
                            save_2p_frames(external_file, starting_frame, timestamps, fname, stack_t)
                            stack_t = []
                            fname = None
                lastframe = framenum
                lastfile = filenum
            # make sure we write out the last entry
            if fname is not None:
                # create_2p_ts(simon, name, fname, stack_t, nname)
                save_2p_frames(external_file, starting_frame, timestamps, fname, stack_t)
            # write out timeseries with external_file as array
            create_2p_tsa(simon, nname, external_file, starting_frame, timestamps)
            sys.stdout.write('.')
            sys.stdout.flush()
    print ""

    print "Closing file"

    simon.close()
    print "Done"
    #break

