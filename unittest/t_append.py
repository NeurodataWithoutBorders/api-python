#!/usr/bin/python
import test_utils as ut
# import nwb
from nwb import nwb_file
from nwb import nwb_utils as utils

# test opening file in append mode
# TESTS modifying existing file
# TESTS creation of modification_time
# TESTS addition of TimeSeries to existing file
# TESTS preservation of TimeSeries when file modified

def test_append():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name1 = "annot1"
    name2 = "annot2"
    # create_annotation_series(fname, name1, "acquisition", True)
    create_annotation_series(fname, name1, "acquisition/timeseries", True)
    # create_annotation_series(fname, name2, "acquisition", False)
    create_annotation_series(fname, name2, "acquisition/timeseries", False)
    ut.verify_timeseries(fname, name1, "acquisition/timeseries", "TimeSeries")
    ut.verify_timeseries(fname, name1, "acquisition/timeseries", "AnnotationSeries")
    ut.verify_timeseries(fname, name2, "acquisition/timeseries", "TimeSeries")
    ut.verify_timeseries(fname, name2, "acquisition/timeseries", "AnnotationSeries")
    # ut.verify_attribute_present(fname, "file_create_date", "modification_time")


def create_annotation_series(fname, name, target, newfile):
    settings = {}
    settings["file_name"] = fname
    settings["verbosity"] = "none"
    if newfile:
        settings["identifier"] = utils.create_identifier("append example")
        settings["mode"] = "w"
        settings["start_time"] = "Sat Jul 04 2015 3:14:16"
        settings["description"] = "Test append file"
    else:
        settings["mode"] = "r+"
    f = nwb_file.open(**settings)
    #
    # annot = neurodata.create_timeseries("AnnotationSeries", name, target)
    annot = f.make_group("<AnnotationSeries>", name, path="/" + target)
    # annot.set_description("This is an AnnotationSeries '%s' with sample data" % name)
    # annot.set_comment("The comment and description fields can store arbitrary human-readable data")
    # annot.set_source("Observation of Dr. J Doe")
    annot.set_attr("description", "This is an AnnotationSeries '%s' with sample data" % name)
    annot.set_attr("comments", "The comment and description fields can store arbitrary human-readable data")
    annot.set_attr("source", "Observation of Dr. J Doe")
    
    #
#     annot.add_annotation("Rat in bed, beginning sleep 1", 15.0)
#     annot.add_annotation("Rat placed in enclosure, start run 1", 933.0)
#     annot.add_annotation("Rat taken out of enclosure, end run 1", 1456.0)
#     annot.add_annotation("Rat in bed, start sleep 2", 1461.0)
#     annot.add_annotation("Rat placed in enclosure, start run 2", 2401.0)
#     annot.add_annotation("Rat taken out of enclosure, end run 2", 3210.0)
#     annot.add_annotation("Rat in bed, start sleep 3", 3218.0)
#     annot.add_annotation("End sleep 3", 4193.0)
    #
    
    andata = []
    andata.append(("Rat in bed, beginning sleep 1", 15.0))
    andata.append(("Rat placed in enclosure, start run 1", 933.0))
    andata.append(("Rat taken out of enclosure, end run 1", 1456.0))
    andata.append(("Rat in bed, start sleep 2", 1461.0))
    andata.append(("Rat placed in enclosure, start run 2", 2401.0))
    andata.append(("Rat taken out of enclosure, end run 2", 3210.0))
    andata.append(("Rat in bed, start sleep 3", 3218.0))
    andata.append(("End sleep 3", 4193.0))
    annotations = [x[0] for x in andata]
    times = [x[1] for x in andata]
    annot.set_dataset("data",annotations)
    annot.set_dataset("timestamps", times)
    
    # annot.finalize()
    # neurodata.close()
    f.close()

test_append()
print("%s PASSED" % __file__)

