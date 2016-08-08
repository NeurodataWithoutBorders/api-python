#!/usr/bin/python
import sys
# import nwb
from nwb import nwb_file
from nwb import nwb_utils as utils

import test_utils as ut

# test creation of annotation time series
# TESTS AnnotationSeries creation
# TESTS TimeSeries ancestry


def test_annotation_series():
    if __file__.startswith("./"):
        fname = "s" + __file__[3:-3] + ".nwb"
    else:
        fname = "s" + __file__[1:-3] + ".nwb"
    name = "annot"
    # create_annotation_series(fname, name, "acquisition")
    create_annotation_series(fname, name, "acquisition/timeseries")
    ut.verify_timeseries(fname, name, "acquisition/timeseries", "TimeSeries")
    ut.verify_timeseries(fname, name, "acquisition/timeseries", "AnnotationSeries")
    # create_annotation_series(fname, name, "stimulus")
    create_annotation_series(fname, name, "stimulus/presentation")
    ut.verify_timeseries(fname, name, "stimulus/presentation", "TimeSeries")
    ut.verify_timeseries(fname, name, "stimulus/presentation", "AnnotationSeries")

def create_annotation_series(fname, name, target):
    settings = {}
    settings["file_name"] = fname
    settings["identifier"] = utils.create_identifier("annotation example")
    settings["mode"] = "w"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["description"] = "Test file with AnnotationSeries"
    settings["verbosity"] = "none"
    # neurodata = nwb.NWB(**settings)
    f = nwb_file.open(**settings)
    #   annot = neurodata.create_timeseries("AnnotationSeries", name, target)
    annot = f.make_group("<AnnotationSeries>", name, path="/" + target)

    # annot.set_description("This is an AnnotationSeries with sample data")
    annot.set_attr('description', "This is an AnnotationSeries with sample data")
    # annot.set_comment("The comment and description fields can store arbitrary human-readable data")
    annot.set_attr("comments", "The comment and desscription fields can store arbitrary human-readable data")
    # annot.set_source("Observation of Dr. J Doe")
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
    # store pretend data
    # all time is stored as seconds
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
        #
        #annot.finalize()
    f.close()

test_annotation_series()
print("%s PASSED" % __file__)

