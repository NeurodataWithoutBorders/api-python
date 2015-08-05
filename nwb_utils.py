# Utility routines useful for creating NWB files

import sys
import numpy as np
import traceback

def load_file(filename):
    """ Load content of a file.  Useful 
    for setting metadata to content of a text file"""
    f = open(filename, 'r')
    content = f.read()
    f.close()
    return content
    

def add_epoch_ts(e, start_time, stop_time, name, ts):
    """ Add timeseries_X group to nwb epoch.
        e - h5gate.Group containing epoch
    start_time - start time of epoch
    stop_time - stop time of epoch
    name - name of <timeseries> group to be added to epoch
    ts - timeseries to be added, either h5gate.Group object or
       path to timeseries """
    if type(ts) is str:
        # ts is path to node rather than node.  Get the node
        ts = e.file.get_node(ts)
    start_idx, cnt = get_ts_overlaps(ts, start_time, stop_time)
    if start_idx == -1:
        # no overlap, don't add timeseries
        return
    f = e.make_group("<timeseries_X>", name)
    f.set_dataset("idx_start", start_idx)
    f.set_dataset("count", cnt)
    f.make_group("timeseries", ts)  # makes a link to ts group


def get_ts_overlaps(tsg, start_time, stop_time):
    """ Get starting index and count of overlaps between timeseries timestamp
        and interval between t_start and t_stop.  This is adapted from
        borg_epoch.py add_timeseries.
        Inputs:
            tsg - Group object containing NWB timeseries timestamp.
            start_time - starting time of interval (epoch)
            stop_time - ending time of interval
        returns tuple with:
            start_idx - starting index of interval in time series, -1 if no overlap
            cnt - number of elements in timeseries overlapping, zero 0 if no overlap
    """
    ts = tsg.file.file_pointer[tsg.full_path]   # h5py group object
    if "timestamps" in ts:
        t = ts["timestamps"].value
    else:
        if "num_samples" not in ts:
            print "in get_ts_overlap, num_samples needed, not found"
            # import pdb; pdb.set_trace()
        n = ts["num_samples"].value  # hopefully not needed
        t0 = ts["starting_time"].value
        rate = ts["starting_time"].attrs["rate"]
        t = t0 + np.arange(n) / rate
    # if no overlap, don't add to timeseries
    # look for overlap between epoch and time series
    start_idx = find_ts_interval_start(t, start_time, stop_time)
    if start_idx < 0:
        #sys.stderr.write("\t%s has no data in %s\n" % (in_epoch_name, self.name))
        return ( -1, 0, )
    cnt = find_ts_interval_overlap(start_idx, t, start_time, stop_time)
    if cnt <= 0:
        #sys.stderr.write("\t%s has no overlap with %s\n" % (in_epoch_name, self.name))
        return ( -1, 0, )
    return (start_idx, cnt)

# following routines taken directly from borg_epoch.py

def find_ts_interval(t, epoch_start, epoch_stop):
    """ Finds the overlapping section of array *t* with epoch start
        and stop times.

        Args:
            *t* (double array) Timestamp array
            *epoch_start* (double) Epoch start time
            *epoch_stop* (double) Epoch stop time

        Returns:
            *idx* (int) Index of first element in *t* at or after *epoch_start*
            *count* (int) Number of elements in *t* between *epoch_start* and *epoch_stop*
    """
    idx = find_ts_interval_start(t, epoch_start, epoch_stop)
    if idx < 0:
        return -1, -1
    cnt = find_ts_interval_overlap(idx, t, epoch_start, epoch_stop)
    return idx, cnt

def find_ts_interval_start(t, epoch_start, epoch_stop):
    """ Finds the first element in *t* that is >= *epoch_start*

        Args:
            *t* (double array) Timestamp array
            *epoch_start* (double) Epoch start time
            *epoch_stop* (double) Epoch stop time

        Returns:
            *idx* (int) Index of first element in *t* at or after *epoch_start*, or -1 if no overlap
    """
    i0 = 0
    t0 = t[i0]
    i1 = len(t) - 1
    t1 = t[i1]
    #print "Searching %d to %d" % (epoch_start, epoch_stop)
    # make sure there's overlap between epoch and time series
    # see if time series start is within range
    if t0 > epoch_stop or t1 < epoch_start:
        #print "No ts overlap"
        return -1
    # check edge case
    if epoch_start == t1:
        # epoch starts where time series ends
        # only overlap between timeseries and epoch is last sample
        #   of time series
        #print "epoch start == t1"
        return i1
    # else, start of epoch is somewhere in time series. look for it
    window = i1 - i0
    # search until we're within 4 samples, then search linearly
    while window > 4:
        mid = i0 + (i1 - i0) / 2
        midt = t[mid]
    #    print "%f\t%f\t%f\t(%d)" % (t0, midt, t1, window)
        if epoch_start == midt:
            #print "Found at mid=%d" % mid
            return mid
        if epoch_start > midt:
            # epoch start later than midpoint of window
            # move window start to midpoint and go again
            i0 = mid
            t0 = midt
        else:
            # start < midt: epoch start beforem midpoint of window
            #   so move window to end to midpoint and start again
            i1 = mid
            t1 = midt
        window = i1 - i0
    # sample is in narrow window. search linearly
    #print "Searching %d-%d (%f to %f)" % (i0, i1, t0, t1)
    for i in range(i0, i1+1):
        #print t[i]
        if t[i] >= epoch_start:
            # first sample greater than epoch start. make sure
            #   it's also before epoch end
            if t[i] < epoch_stop:
                #print "start<=%d<end, idx=%d" % (t[i], i)
                return i
            else:
                # epoch rests entirely between two timestamp 
                #    samples, with no overlap
                #print "No overlap"
                return -1
    #print "Epoch start: %f" % start_time
    #print "Epoch end: %f" % stop_time
    assert False, "Unable to find start of timeseries overlap with epoch"

def find_ts_interval_overlap(i0, t, epoch_start, epoch_stop):
    """ Finds the number of elements in *t* that overlap with epoch
        start/stop.

        Args:
            *i0* (int) Index of first element in *t* that is in [start,stop] interval
            *t* (double array) Timestamp array
            *epoch_start* (double) Epoch start time
            *epoch_stop* (double) Epoch stop time

        Returns:
            *cnt* (int) Number of elements in *t* that overlap with epoch
    """
    assert epoch_start <= t[i0]
    t0 = t[i0]
    i1 = len(t) - 1
    t1 = t[i1]
    # if we made it here, i0 is within epoch
    # see where timeseries ends relative to epoch end
    if t1 <= epoch_stop:
        # timeseries ends before or at end of epoch
        cnt = i1 - i0 + 1
        #print "\tA\t%d, %d -> %d" % (i0, i1, cnt)
        return cnt
    # time series extends beyond epoch end. find end of overlap
    # if we've made it here then there is at least one timeseries entry
    #   that extends beyond epoch
    for i in range(i0, (len(t)-1)):
        if t[i] <= epoch_stop and t[i+1] > epoch_stop:
            cnt = i - i0 + 1
            #print "\tB\t%d, %d -> %d" % (i0, i, cnt)
            return cnt
    assert False, "Failed to find overlap"  
    
    
    
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
        y = pixel_list[i][0]
        x = pixel_list[i][1]
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
    pm = roi_folder.set_dataset("pix_mask_0", pixel_list, dtype="i2", compression=True) 
    #- pm.attrs["weight"] = weights
    pm.set_attr("weight", weights)
    #- pm.attrs["help"] = "Pixels stored as (x, y). Relative weight stored as attribute."
    pm.set_attr("help", "Pixels stored as (x, y). Relative weight stored as attribute.")
    # im = roi_folder.create_dataset("img_mask_0", data=img, dtype='f4', compression=True)
    im = roi_folder.set_dataset("img_mask_0", img, dtype='f4', compression=True)
    #- im.attrs["help"] = "Image stored as [y][x] (ie, [row][col])"
    im.set_attr("help", "Image stored as [y][x] (ie, [row][col])")
    #- roi_folder.create_dataset("start_time_0", data=start_time, dtype='f8')
    roi_folder.set_dataset("start_time_0", start_time, dtype='f8')
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
    img_ts = ri.make_group("<ImageSeries>", name)
    #- img_ts.set_format("raw")
    img_ts.set_dataset('format', 'raw')
    #- img_ts.set_bits_per_pixel(8)
    img_ts.set_dataset('bits_per_pixel', 8)
    #- img_ts.set_dimension([len(img[0]), len(img)])
    img_ts.set_dataset('dimension', [len(img[0]), len(img)])
    #- img_ts.set_time([0])
    img_ts.set_dataset('timestamps', [0.0])
    #- img_ts.set_data(img, "grayscale", 1, 1)
    img_ts.set_dataset('data', img, attrs={'unit':'grayscale'})
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
            