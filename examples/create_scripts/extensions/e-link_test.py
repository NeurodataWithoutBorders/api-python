
{"fs": {"link_test": {


"info": {
    "name": "link_test",
    "version": "0.1",
    "date": "May 6, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": "Test defining a link in an extension to debug schema_id."
},

"schema": {
    "/analysis/": {
        "aibs_spike_times/": {
            "description": "Group for storing AIBS specific spike times",
            "pto_link?": {
                "description": ("The offset from the frame timestamp at which each pixel was acquired."
                            " Note that the offset is not time-varying, i.e. it is the same for"
                            " each frame. These offsets are given in the same units as for the"
                            " timestamps array, i.e. seconds."),
                "link": {"target_type": "pixel_time_offsets",
                         # "allow_subclasses": False  # allow_subclasses not allowed in dataset links
                         },
                "data_type": "float64!"
            },
            "pixel_time_offsets": {
                "description": ("The offset from the frame timestamp at which each pixel in this ROI"
                            " was acquired."
                            " Note that the offset is not time-varying, i.e. it is the same for"
                            " each frame. These offsets are given in the same units as for the"
                            " timestamps array, i.e. seconds."),
                "data_type": "float64!",
                "dimensions": [["y"], ["y", "x"]]
            }
        }
    }
}

}}}
