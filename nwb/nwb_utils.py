# Utility routines useful for creating NWB files

import sys
import numpy as np
import traceback
import datetime

def load_file(filename):
    """ Load content of a file.  Useful 
    for setting metadata to content of a text file"""
    f = open(filename, "rb") # py3, added rb mode
    content = f.read()
    f.close()
    return content
    
def current_time():
    """ Return current datetime in iso format"""
    cur_time = datetime.datetime.now().isoformat()
    return cur_time

def create_identifier(base_string):
    """ Create unique identifier using current time"""
    return base_string + "; " + current_time()
    
def create_epoch(f, name, start_time, stop_time):
    """ add an <epoch_X>.  f is the h5gate file object.
    name is name of epoch
    start_time and stop_time should both be float64
    Returns the group for the created epoch.
    """
    epoch = f.make_group("<epoch_X>", name)
    epoch.set_dataset("start_time", start_time)
    epoch.set_dataset("stop_time", stop_time)
    return epoch
    
    
# for storing cache to speedup finding timeseries overlaps
tse_cache = {}
tse_max_num_nans = 1000


def add_epoch_ts(e,  start_time, stop_time, in_epoch_name, timeseries):
    """ Associates time series with epoch. This will create a link
        to the specified time series within the epoch and will
        calculate its overlaps.

        Arguments:
            *e* - h5gate.Group containing epoch
            
            *start_time* - start time of epoch
            
            *stop_time* - stop time of epoch
            
            *in_epoch_name* (text) Name that time series will use 
            in the epoch (this can be different than the actual 
            time series name)

            *timeseries* (text or TimeSeries object) 
            Full hdf5 path to time series that's being added, 
            or the  h5gate.Group TimeSeries object itself

        Returns:
            *nothing*
    """
    global tse_cache, tse_max_num_nans
    if type(timeseries) is str:
        # ts is path to node rather than node.  Get the node
        timeseries = e.file.get_node(timeseries)
    elif "h5gate.Group" not in str(type(timeseries)):  # change to use string, was: is not h5gate.Group:
        print ("Don't recognize timeseries parameter as group or path, type=%s" % type(timeseries))
        sys.exit(1)
    timeseries_path = timeseries.full_path   
    if timeseries_path not in tse_cache:
        if timeseries_path not in e.file.file_pointer:
            sys.exit("Time series '%s' not found" % timeseries_path) 
        # get timeseries timestamps array (or generate using starting_time and sampling rate)
        ts = e.file.file_pointer[timeseries_path]
        if "timestamps" in ts:
            t = ts["timestamps"].value
        else:
            n = ts["num_samples"].value
            t0 = ts["starting_time"].value
            rate = ts["starting_time"].attrs["rate"]
            t = t0 + np.arange(n) / rate
        # make cached info
        get_tse_overlap_info(t, timeseries_path)
        # print "created tse info for %s" % timeseries_path
    # if no overlap, don't add to timeseries
    # look for overlap between epoch and time series
    # i0, i1 = find_ts_overlap(start_time, stop_time, t, timeseries_path)
    i0, i1 = find_ts_overlap_n(start_time, stop_time, timeseries_path)
    if i0 is None:
        return
    tsx = e.make_group("<timeseries_X>", in_epoch_name)
    tsx.set_dataset("idx_start", i0)
    tsx.set_dataset("count", i1 - i0 + 1)
    tsx.make_group("timeseries", timeseries)  # makes a link to ts group        
    


# internal function
# Finds the first element in *timestamps* that is >= *epoch_start*
# and last element that is <= "epoch_stop"
#
# Arguments:
#     *start* - starting time
#     *stop*  - stoping time
#     *timestamps* (double array) Timestamp array
#     *timeseries_path* - path to timeseries (displayed if error)
#
# Returns:
#     *idx_0*, "idx_1" (ints) Index of first and last elements 
#     in *timestamps* that fall within specified
#     interval, or None, None if there is no overlap
#
def find_ts_overlap(start, stop, timestamps, timeseries_path):
    # ensure there are non-nan times
    isnan = np.isnan(timestamps)
    if isnan.all(): 
        return None, None   # all values are NaN -- no overlap
    # convert all nans to a numerical value 
    # when searching for start, use -1
    # when searching for end, use stop+1
    timestamps = np.nan_to_num(timestamps)
    t_test = timestamps + isnan * -1 # make nan<0
    # array now nan-friendly. find first index where timestamps >= start
    i0 = np.argmax(t_test >= start)
    # if argmax returns zero then the first timestamp is >= start or 
    #   no timestamps are. find out which is which
    if i0 == 0:
        if t_test[0] < start:
            return None, None # no timestamps > start
    if t_test[i0] > stop:
        return None, None # timestamps only before start and after stop
    # if we reached here then some or all timestamps are after start
    # search for first after end, adjusting compare array so nan>stop
    t_test = timestamps + isnan * (stop+1)
    # start looking after i0 -- no point looking before, plus if we
    #   do look before and NaNs are present, it screws up the search
    i1 = np.argmin((t_test <= stop)[i0:])
    # if i1 is 0, either all timestamps are <= stop, or all > stop
    if i1 == 0:
        if t_test[0] > stop:
            return None, None # no timestamps < stop
        i1 = len(timestamps) - 1
    else:
        i1 = i0 + i1 - 1 # i1 is the first value > stop. fix that
    # make sure adjusted i1 value is non-nan
    while isnan[i1]:
        i1 = i1 - 1
        assert i1 >= 0
    try:    # error checking 
        assert i0 <= i1
        assert not np.isnan(timestamps[i0])
        assert not np.isnan(timestamps[i1])
        assert timestamps[i0] >= start and timestamps[i0] <= stop
        assert timestamps[i1] >= start and timestamps[i1] <= stop
        return i0, i1
    except AssertionError:
        print("-------------------" + timeseries_path)
        print("epoch: %f, %f" % (start, stop))
        print("time: %f, %f" % (timestamps[0], timestamps[-1]))
        print("idx 0: %d\tt:%f" % (i0, timestamps[i0]))
        print("idx 1: %d\tt:%f" % (i1, timestamps[i1]))
        assert False, "Internal error"


def get_tse_overlap_info(timestamps, timeseries_path):
    # get info about timeseries useful to speedup finding overlaps
    # stores info in cache
    # this mainly setup to deal with NaN values in the timeseries
    global tse_cache, tse_max_num_nans
    isnan = np.isnan(timestamps)
    num_nans = np.count_nonzero(isnan)
    if num_nans == 0 or num_nans == len(timestamps) or num_nans > tse_max_num_nans:
        info = {'num_nans': num_nans, 'timestamps': timestamps}
        if num_nans > tse_max_num_nans:
            print ("Warning: more than %i NaN's (%i) in timestamps for %s, not caching" % (
                tse_max_num_nans, num_nans, timeseries_path))
        tse_cache[timeseries_path] = info
        return
    # ok, are some NaN's, but not too many
    # build dictionary mapping each NaN index to the index of the first non-NaN value
    # before and after it
    nan_indicies = np.flatnonzero(isnan)
    nans = {}
    blocks = []
    block_last_index = None
    for i in range(len(nan_indicies)):
        nani = nan_indicies[i]
        if block_last_index is None:
            # this is the start of a new block, there was no previous block
            block_first_index = nani
            block_last_index = nani
        elif nani == block_last_index + 1:
            # this is the continuation of a block
            block_last_index = nani
        else:
            # this is the start of a new block; there was a previous block
            # make dict lookups for items in previous block
            block_prev_non_nan = block_first_index - 1 if block_first_index > 0 else None
            block_next_non_nan = block_last_index + 1
            block = (block_prev_non_nan, block_next_non_nan)
            # save the block
            blocks.append(block)
            # save map from each eleent in block to block
            for j in range(block_first_index, block_last_index + 1):
                nans[j] = block
            # start keeping track of new block
            block_first_index = nani
            block_last_index = nani
    # save info for last block
    block_prev_non_nan = block_first_index - 1
    block_next_non_nan = block_last_index + 1 if block_last_index + 1 < len(timestamps) else None
    block = (block_prev_non_nan, block_next_non_nan)
    blocks.append(block)
    for j in range(block_first_index, block_last_index + 1):
        nans[j] = block
    # make copy of timeseries with NaN values replaced by previous non-NaN values (or next
    # non-NaN value if at start of array)
    ts_fixed = np.copy(timestamps)
    # replace all NaN values in array with the closest non_NaN value
    for block in blocks:
        block_prev_non_nan, block_next_non_nan = block
        start_index = block_prev_non_nan + 1 if block_prev_non_nan is not None else 0
        end_index = block_next_non_nan if block_next_non_nan is not None else len(ts_fixed)
        value = timestamps[block_prev_non_nan] if block_prev_non_nan is not None else timestamps[block_next_non_nan]
        for j in range(start_index, end_index):
            # replace nan with value matching boundary, used for sorting
            ts_fixed[j] = value
    info = {'num_nans': num_nans, 'nans': nans, 'ts_fixed': ts_fixed}
    tse_cache[timeseries_path] = info
    return
    

# Internal function, find time_series overlaps.
# use cache to make faster, but call original if too many NaN values
def find_ts_overlap_n(start, stop, timeseries_path):
    global tse_cache, tse_max_num_nans
    tse_info = tse_cache[timeseries_path]
    num_nans = tse_info['num_nans']
    # if no NaNs, use normal search for overlaps, else use ts_fixed and later make sure all
    # returned values are not NaN
    times = tse_info['timestamps'] if 'timestamps' in tse_info else tse_info['ts_fixed']
    if num_nans > tse_max_num_nans:
        # use brute-force, slow method of finding overlaps
        return find_ts_overlap(start, stop, times, timeseries_path)
    elif num_nans == len(times):
        # all are NaNs, no overlap
        return None, None
    # now start searching to find overlaps
    i0 = np.searchsorted(times, start)
    if i0 == len(times):
        # start time is after last timestamp, no overlap
        return None, None
    if stop < times[i0]:
        # timestamps values only before start and after stop (none overlap)
        return None, None
    # search for stop index
    i1 = np.searchsorted(times[i0:], stop, side="right")
    i1 = i1 + i0 - 1 # adjust for offset and side
    if num_nans > 0:
        # make sure index to retured values are not NaN
        nans = tse_info['nans']
        if i0 in nans:
            i0 = nans[i0][1]
        if i1 in nans:
            i1 = nans[i1][0]
    return i0, i1
    
  
    
###############
## Imaging utilities, from: borg_modules.py


#- def add_roi_mask_pixels(self, image_plane, name, desc, pixel_list, weights, width, height, start_time=0):
def add_roi_mask_pixels(seg_iface, image_plane, name, desc, pixel_list, weights, width, height, start_time=0):

    """ Adds an ROI to the module, with the ROI defined using a list of pixels.

        Args:
            *image_plane* (text) name of imaging plane
        
            *name* (text) name of ROI

            *desc* (text) description of ROI

            *pixel_list* (2D int array) array of [x,y] pixel values

            *weights* (float array) array of pixel weights

            *width* (int) width of reference image, in pixels

            *height* (int) height of reference image, in pixels

            *start_time* (double) <ignore for now>

        Returns:
            *nothing*
    """
    # create image out of pixel list
    img = np.zeros((height, width))
    for i in range(len(pixel_list)):
        x = pixel_list[i][0]
        y = pixel_list[i][1]
        img[y][x] = weights[i]
    add_masks(seg_iface, image_plane, name, desc, pixel_list, weights, img, start_time)
        
        

    #- def add_roi_mask_img(self, image_plane, name, desc, img, start_time=0):

def add_roi_mask_img(seg_iface, image_plane, name, desc, img, start_time=0):
    """ Adds an ROI to the module, with the ROI defined within a 2D image.

        Args:
            *seg_iface* (h5gate Group object) ImageSegmentation folder
            
            *image_plane* (text) name of imaging plane

            *name* (text) name of ROI

            *desc* (text) description of ROI

            *img* (2D float array) description of ROI in a pixel map (float[y][x])

            *start_time* <ignore for now>

        Returns:
            *nothing*
    """
    # create pixel list out of image
    pixel_list = []
    weights = []
    for y in range(len(img)):
        row = img[y]
        for x in range(len(row)):
            if row[x] != 0:
                pixel_list.append([x, y])
                weights.append(row[x])
    add_masks(seg_iface, image_plane, name, pixel_list, weights, img, start_time)

def add_masks(seg_iface, image_plane, name, desc, pixel_list, weights, img, start_time):
    """ Internal/private function to store the masks. 
        The public functions (add_roi_*) take either a pixel list or an image, and they generate the missing one
        from the specified one. This procedure takes both pixel list and pixel map and writes them to the HDF5
        file.

        Note: Multiple sequential masks are suppored by the spec. The API only supports one presently

        Args:
            *seg_iface* (h5gate Group object) ImageSegmentation folder
            
            *image_plane* (text) name of imaging plane

            *name* (text) name of ROI

            *desc* (text) description of ROI

            *pixel_list* (2D int array) array of [x,y] pixel values

            *weights* (float array) array of pixel weights

            *img* (2D float array) description of ROI in a pixel map (float[y][x])

            *start_time* <ignore for now>

        Returns:
            *nothing*
    """
    # create folder for imaging plane if it doesn't exist
    #- if image_plane not in self.iface_folder:
    folder_path = seg_iface.full_path + "/" + image_plane
    ip = seg_iface.file.get_node(folder_path, abort=False)
    if ip is None:
        #- ip = self.iface_folder.create_group(image_plane)
        ip = seg_iface.make_group("<image_plane>", image_plane)
        # array for roi list doesn't exist either then -- create it
        #- self.roi_list[image_plane] = []
    #- else:
    #-    ip = self.iface_folder[image_plane]
    # create ROI folder
    #- ip.create_group(name)
    roi_folder = ip.make_group("<roi_name>", name)
    # save the name of this ROI
    #- self.roi_list[image_plane].append(name)
    # add data
    #- roi_folder = ip[name]
    #- pm = roi_folder.create_dataset("pix_mask_0", data=pixel_list, dtype='i2', compression=True)
    # pm = roi_folder.set_dataset("pix_mask", pixel_list, dtype="i2", compress=True)
    # default data type is uint16
    if len(pixel_list) == 0:
        # if empty, create empty list with proper shape to avoid errors with dimension mismatch
        dt = np.dtype((np.uint16, (2)))
        pixel_list = np.array([], dtype=dt)
    pm = roi_folder.set_dataset("pix_mask", pixel_list, compress=True)
    #- pm.attrs["weight"] = weights
    roi_folder.set_dataset("pix_mask_weight", weights)
    #- pm.attrs["help"] = "Pixels stored as (x, y). Relative weight stored as attribute."
    # pm.set_attr("help", "Pixels stored as (x, y). Relative weight stored as attribute.")
    # im = roi_folder.create_dataset("img_mask_0", data=img, dtype='f4', compression=True)
    # default data_type is float32
    # im = roi_folder.set_dataset("img_mask", img, dtype='f4', compress=True)
    im = roi_folder.set_dataset("img_mask", img, compress=True)
    #- im.attrs["help"] = "Image stored as [y][x] (ie, [row][col])"
    # im.set_attr("help", "Image stored as [y][x] (ie, [row][col])")
    #- roi_folder.create_dataset("start_time_0", data=start_time, dtype='f8')
    # roi_folder.set_dataset("start_time_0", start_time, dtype='f8')
    #- roi_folder.create_dataset("roi_description", data=desc)
    roi_folder.set_dataset("roi_description", desc)


def add_reference_image(seg_iface, plane, name, img):
    """ Add a reference image to the segmentation interface

        Args: 
            *seg_iface*  Group folder having the segmentation interface
            
            *plane* (text) name of imaging plane

            *name* (text) name of reference image

            *img* (byte array) raw pixel map of image, 8-bit grayscale

        Returns:
            *nothing*
    """
    #- import borg_timeseries as ts
    #- path = "processing/%s/ImageSegmentation/%s/reference_images" % (self.module.name, plane)
    #- grp = self.iface_folder[plane]
    #- if "reference_images" not in grp:
    #-     grp.create_group("reference_images")
    grp = seg_iface.get_node(plane)
    ri = grp.make_group("reference_images", abort=False)
    #- img_ts = ts.ImageSeries(name, self.module.borg, "other", path)
    img_ts = ri.make_group("<image_name>", name)
    #- img_ts.set_format("raw")
    img_ts.set_dataset('format', 'raw')
    #- img_ts.set_bits_per_pixel(8)
    img_ts.set_dataset('bits_per_pixel', 8)
    #- img_ts.set_dimension([len(img[0]), len(img)])
    img_ts.set_dataset('dimension', [len(img[0]), len(img[1])])  # modified
    #- img_ts.set_time([0])
    img_ts.set_dataset('timestamps', [0.0])
    #- img_ts.set_data(img, "grayscale", 1, 1)
    img_ts.set_dataset('data', img, attrs={'unit':'grayscale',
        "conversion": 1.0, "resolution": 1.0})
    img_ts.set_dataset('num_samples', 1)
    #- img_ts.finalize()

# def create_reference_image(self, stream, name, fmt, desc, dtype=None):
#         fp = self.file_pointer
#         img_grp = fp["acquisition/images"]
#         if dtype is None:
#             img = img_grp.create_dataset(name, data=stream)
#         else:
#             img = img_grp.create_dataset(name, data=stream, dtype=dtype)
#         img.attrs["format"] = fmt
#         img.attrs["description"] = desc
            