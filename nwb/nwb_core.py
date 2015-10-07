# Partial definitions of NWB format using JSON formatted specification language

# nwb["core"] contains the core standard
# nwb["<extensionName>"] contains extensions.  (Like namespaces in xml) 
nwb={}
nwb["core"]={}
nwb["core"]["structures"] = {

    # Structures specify data sets or groups:
    #     "identifier" - dataset
    #     "identifier/" - group (has trailing slash)
    #     "<identifier>" - dataset with variable name
    #     "<identifier>/" - group with variable name
    
    # Top-level datasets
    "neurodata_version": {
        "data_type": "text",
        "description": ("File version string. This will be the name of the format with "
            "trailing major, minor and patch numbers (e.g., NWB-0.4.18)")},
    "identifier": {
        "data_type": "text",
        "description": "A unique text identifier for the file"},
    "file_create_date": {
        "data_type": "text",
        "description": "Date and time file was created, UTC (ISO 8601)",
        "attributes": {
            "modification_time": {
                "description": ("Times that the file was modified.  Only present if an existing"
                    " file was modified.  Each modificaiton time stored in ISO 8601 format."),
                "data_type": "text"}}},
    "session_start_time": {
        "data_type": "text",
        "description": ("Date and time experiment was started was created, UTC (ISO 8601)."
            " This serves as the reference time for data in the file. All timestamps in a"
            " neurodata file are stored as seconds after this reference time")},
    "session_description": {
        "data_type": "text",
        "description": "One or two sentences describing the experiment and data in the file"}, 

    # timeSeries timestamps
    "<timestamps>/": {
        "description": "Times that are synced to data",
        "attributes": {
            "description": {"data_type": "text", },
            "comments": {"data_type": "text", },
            "source": {"data_type": "text", "value":"Unspecified source"},
            "ancestry": {"data_type": "text", "value": "TimeSeries"},
            "neurodata_type": {"data_type": "text", "value": "TimeSeries", },
            "data_link": {
                "description": ("List of the paths of all TimeSeries that share a hard link "
                "to the same data field.  Attribute is only present if links are present. "
				"List should include the path to this TimeSeries also"),
				"data_type": "text" },
			"timestamp_link": {
                "description": ("List of the paths of all TimeSeries that share a hard link "
                "to the same timestamps field.  Attribute is only present if links are present. "
				"List should include the path to this TimeSeries also"),
				"data_type": "text" },
			"missing_fields": {
                "description": ("List of fields defined as 'required' parts of the"
                    " TimeSeries that are missing"),
				"data_type": "text" },
			"help": {
                "description": ("Displays the 'description' field of the time "
                    "series stored in the specification file/language"),
				"data_type": "text" },
				},
        "timestamps": {
            "description": "Timestamps for samples stored in data",
            "data_type": "float",
            "unit": "Seconds (all neurodata timestamps are in seconds)",
            "dimensions": ["timeIndex"],
            "semantic_type": "timestamps",
            "attributes": {
                "rate": { "data_type": "float", "description": "Sampling rate if known"},
                # "rate.unit": {"data_type": "text", "value": "Hz",},
                "interval": {"data_type": "int", "value": 1},
                # "interval.unit": {"data_type": "text", "value": "nSamples", },
                 }, },
        "starting_time?": {
            "description": ("In some edge cases it is not practical to store every timestamp"
                " (e.g., single-cell patch-clamp data sampled at 200KHz).  For these cases,"
                " a field called starting_time is used instead of timestamps. The field"
                " starting_time stores the starting time of the timeseries along with the"
                " exact sampling rate."),
            "data_type": "float",
            "unit": "second",
            "attributes": {
                "rate": {
                    "description": "Data sampling or stimulus presentation rate (Hz)",
                    "data_type": "float"},
                "unit": {
                    "data_type": "text",
                    "value": "Seconds (all neurodata timestamps are in seconds)"}, },
        },       
        "num_samples": {
            "description": "Number of samples valid for timestamp",
            "data_type": "int"},
        "control?": {
            "description": ("Numerical labels that apply to each element in data[]. "
                "Optional field. If present, the control array should have the same number "
                "of elements as data[]"), 
            "data_type": "int",
            "dimensions": ["timeIndex"],
            "references": "control_description.num_control_values"}, 
        "control_description?": {
            "data_type": "text",
            "dimensions": ["num_control_values"],
            "description": ("Description of each control value.  Array length should be as long"
                " as the highest number in control minus one, generating an zero-based"
                " indexed array for control values")},
        "sync/?": {
            "description": "Lab specific time and sync information" },   
        # attributes merged into groups "data" dataset that are merged
        "data": {
            "attributes": {
                "conversion": {"data_type": "float", },
                "unit": {"data_type": "text", },
                "resolution": {"data_type": "number" ,}, },
            # "scale": 1.0
            }, 
    },
    # timeSeries data types
    "<TimeSeries>/": {
        "description": "General purpose time series",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value": "TimeSeries" }, },
        "data": {
            # "description": "Recorded data",
            "dimensions": ["timeIndex"], # specifies 1-d array
            "data_type": "number", },
    },
    "<AbstractFeatureSeries>/": {
        "description": "Abstract features, such as quantitative descriptions of sensory stimuli.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,AbstractFeatureSeries" },},
        "feature": {
            "description": "Description of the features represented in TimeSeries::data",
            "dimensions": ["timeIndex","featureIndex"],
            "data_type": "text"},
        "feature_units": {
            "description": "Units of each feature",
            "dimensions": ["featureIndex"],
            "data_type": "text"},
        "data": {
            "dimensions": ["timeIndex", "featureIndex"],
            "data_type": "number"},
    },
    "<AnnotationSeries>/": {
        "description": "Stores user annotations made during an experiment.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,AnnotationSeries" },},
        "data": {
            "dimensions": ["timeIndex"],
            "data_type": "text"},
    },       
    "<IndexSeries>/": {
        "description": "Stores indices to image frames stored in an ImageSeries.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,IndexSeries" },},
        "data": {
            "dimensions": ["timeIndex"],
            "data_type": "int",
            "references": "indexed_timeseries/data.timeIndex"},
        "indexed_timeseries/": {
            "description": "HDF5 link to TimeSeries containing images that are indexed"},
        "indexed_timesereis_path": {
            "description": "Path to linked TimeSeries"},
    },
    "<IntervalSeries>/": {
        "description": "Stores intervals of data.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,IntervalSeries" },},
        "data": {
            "description": ">0 if interval started, <0 if interval ended",
            "dimensions": ["timeIndex"],
            "data_type": "int",
            "unit": "none",
            "semantic_type": "IntervalSeries" },
    },
    "<OptogeneticSeries>/": {
        "description": "Optogenetic stimulus.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,OptogeneticSeries" },},
        "data": {
            "description": "Applied power for optogenetic stimulus",
            "dimensions": ["timeIndex"],
            "data_type": "number",
            "unit": "watt"},
        "site": {
            "description": "Name of site description in general/optogentics",
            "data_type": "text",
            "references": "/general/optogenetics/<site_X>/"}
    },
  
    "<RoiResponseSeries>/": {
        "description": ("ROI responses over an imaging plane. Each row in data[] should correspond to "
            "the signal from one ROI."),
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,RoiResponseSeries>" }},
        "data": {
            "description": "Signals from ROIs",
            "dimensions": ["timeIndex", "RoiIndex"],
            "data_type": "number",
            "semantic_type": "RoiResponseSeries" },
        "segmentation_interface/":  {
            "description": "HDF5 link to image segmentation module defining ROIs" },
        "segmentation_interface_path": {
            "description": "Path to segmentation module",
            "data_type": "text" },
        "roi_names": {
            "description": "List of ROIs represented, one name for each row of data[]",
            "data_type": "text",
            "dimensions": ["RoiIndex",] }
    },
    "<SpatialSeries>/": {
        "description": "Direction, e.g., of gaze or travel, or position.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,SpatialSeries>" }},
        "reference_frame": {
            "description": "Description defining what exactly 'straight-ahead' means",
            "data_type": "text"},
        "data": {
            "description": "2-D array storing position or direction relative to some reference frame.",
            "dimensions": ["timeIndex", "featureIndex"],
            "data_type": "number",
            "semantic_type": "RoiResponseSeries" },
    }, 
    "<ElectricalSeries>/": {
        "description": "Acquired voltage data from extracellular recordings.",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value": "TimeSeries, ElectricalSeries" },},
        "data": {
            "description": "Recorded voltage data",
            "dimensions": ["timeIndex", "channelIndex"], # specifies 2-d array
            "data_type": "number",
            "unit": "volt",
            "semantic_type": "ElectricalSeries" },
        "electrode_idx": {
            "description": "Indicies to electrodes in general/extracellular_ephys/electrode_map",
            "dimensions": ["channelIndex"],
            "data_type": "int",
            "references": "/general/extracellular_ephys/electrode_map.electrode_number",},     
    },
    "<SpikeEventSeries>/": {
        "description": "Stores 'snapshots' of spike events (e.g. threshold crossings).",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries, SpikeEventSeries" },},
        "data": {
            "description": "Spike waveforms",
            "dimensions": ["timeIndex", "channelIndex","sampleIndex"], # specifies 3-d array
            # will be 2-d array ["timeIndex", "sampleIndex"] for single electrode
            "data_type": "number",
            "unit": "volt",
            "semantic_type": "SpikeEventSeries" },
        "electrode_idx": {
            "description": "Indicies to electrodes in general/extracellular_ephys/electrode_map",
            "dimensions": ["channelIndex"],
            "data_type": "int",
            "references": "/general/extracellular_ephys/electrode_map.electrode_number", },
        "source" : {
            "description" : "Source of events (eg, timeseries, hardware) and description of event definition",
            "data_type": "text"},
    },
    "<PatchClampSeries>/": {
        "description": "Stores stimulus or response current or voltage.",
        "merge": ["<timestamps>/", ],
        "attributes": {"ancestry": {"data_type": "text", "value": "TimeSeries,PatchClampSeries" },},
        "data": {
            "description": "Recorded voltage or current",
            "dimensions": ["timeIndex"],
            "data_type": "number",
            "semantic_type": "PatchClampSeries" },
        "electrode_name": {   # in earlier version, this was electrode
            "description": "Name of electrode entry in /general/intracellular_ephys",
            "data_type": "text",
            "references": "/general/intracellular_ephys/<electrode_X>/"},
#         "gain": {
#             "description": "Units: Volt/Amp (v-clamp) or Volt/Volt (c-clamp)",
#             "data_type": "float"},
#         "initial_access_resistance": {
#             "description": "Initial access resistance",
#             "data_type": "float",
#             "unit": "Ohm" },
#         "seal": {
#             "description": "Seal",
#             "data_type": "float",
#             "unit": "Ohm" },
    },
    "<VoltageClampStimulusSeries>/": {
        "description": ("Aliases to standard PatchClampSeries. Its functionality is to better"
            " tag PatchClampSeries for machine (and human) readability of the file."),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {"ancestry": {"data_type": "text",
            "value": "TimeSeries,PatchClampSeries,VoltageClampStimulusSeries" },},        
    },
    "<CurrentClampStimulusSeries>/": {
        "description": ("Aliases to standard PatchClampSeries. Its functionality is to better"
            " tag PatchClampSeries for machine (and human) readability of the file."),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {"ancestry": {"data_type": "text",
            "value": "TimeSeries,PatchClampSeries,CurrentClampStimulusSeries" },},              
    },
    "<VoltageClampSeries>/": {
        "description": ("Stores current data recorded from intracellular voltage-clamp"
            " recordings. A corresponding VoltageClampStimulusSeries (stored separately as a"
            " stimulus) is used to store the voltage injected. The VoltageClampSeries has all"
            " of the datasets of an PatchClampSeries as well as the following:"),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {"ancestry": {"data_type": "text",
            "value": "TimeSeries,PatchClampSeries,VoltageClampSeries" },},
        "capacitance_fast": {
            "description": "Capacitance fast",
            "data_type": "float",
            "unit": "Farad"},
        "capacitance_slow": {
            "description": "Capacitance slow",
            "data_type": "float",
            "unit": "Farad"},
        "resistance_comp_bandwidth": {
            "description": "resistance_comp_bandwidth",
            "data_type": "number",   # Docs say this is float, AI data set has int
            "unit": "Hz"},
        "resistance_comp_correction": {
            "description": "resistance_comp_correction",
            "data_type": "number",   # Docs say this is float, AI data set has int
            "unit": "%"},
        "resistance_comp_prediction": {
            "description": "resistance_comp_prediction",
            "data_type": "number",   # Docs say this is float, AI data set has int
            "unit": "%"},
        "whole_cell_capacitance_comp": {
            "description": "whole_cell_capacitance_comp",
            "data_type": "float",
            "unit": "Farad"},
        "whole_cell_series_resistance_comp": {
            "description": "whole_cell_series_resistance_comp",
            "data_type": "float",
            "unit": "Ohm"},
        "gain": {
            "description": "gain",
            "data_type": "float",
            "unit": "Volt/Amp"},
    },
    "<CurrentClampSeries>/": {
        "description": ("Stores voltage data recorded from intracellular current-clamp recordings."
            " A corresponding CurrentClampStimulusSeries (stored separately as a stimulus) is used"
            " to store the current injected. The CurrentClampSeries has all of the datasets of an"
            " PatchClampSeries as well as the following:"),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {"ancestry": {"data_type": "text",
            "value": "TimeSeries,PatchClampSeries,CurrentClampSeries" },},
        "bias_current": {
            "description": "Bias current",
            "data_type": "float",
            "unit": "Amp"},
        "bridge_balance": {
            "description": "Bridge Balance",
            "data_type": "float",
            "unit": "Ohm"},
        "capacitance_compensation": {
            "description": "Capacitance compensation",
            "data_type": "float",
            "unit": "Farad"},
        "resistance_compensation": {
            "description": "Resistance compensation",
            "data_type": "float",
            "unit": "Ohms"},
        "gain": {
            "description": "gain",
            "data_type": "float",
            "unit": "Volt/Volt"},
    },
    "<ImageSeries>/": {
        "description": "Stores images or path to images on file system",
        "merge": ["<timestamps>/"],
        "attributes": {"ancestry": {"data_type": "text", "value":"TimeSeries,ImageSeries" },},
        "data": {
            "description": "Either binary data containing image or empty",
            "dimensions": ["frame","x","y"], # if 4d then:"frame","z","x","y"
            "data_type": "number", },
        "format": {
            "description": ("Format of image. If this is 'external' then the field external_file"
                " contains the path or URL information to that file. For tiff, png, jpg, etc,"
                " the binary representation of the image is stored in data. If the format is"
                " raw then the fields bit_per_pixel and dimension are used. For raw images,"
                " only a single channel is stored (eg, red)."),
            "data_type": "text"},
        "external_file?": {
            "description": "Path or URL to external file. Field only present if format=external",
            "data_type": "text"},
        "bits_per_pixel": {
            "description": "Number of bit per image pixel",
            "data_type": "number",},
        "dimension": {
            "description": "Number of pixels on x, y, (and z) axes",
            "data_type": "int",
            "dimensions": ["rank"]},       
    },
    "<ImageMaskSeries>/": {
        "description": "An alpha mask that is applied to a presented visual stimulus.",
        "merge": ["<imageSeries>/"],
        "attributes": {"ancestry": {"data_type": "text", 
            "value":"TimeSeries,ImageSeries,ImageMaskSeries" }},
        "masked_imageseries/": {
            "description": "Link to ImageSeries that mask is applied to" },
        "masked_imageseries_path": {
            "description": "Path to linked ImageSeries",
            "data_type": "text"},
        }, 
    "<TwoPhotonSeries>/": {
        "description": "A special case of optical imaging.",
        "attributes": {
            "ancestry": {
                "data_type":"text",
                "value": "TimeSeries,ImageSeries,TwoPhotonSeries"},},
        "merge": ["<ImageSeries>/",],
        "pmt_gain": {
            "description": "Photomultiplier gain",
            "data_type": "number"},
        "field_of_view": {
            "description": "Width, height and depth of image, or imaged area (meters)",
            "data_type": "float",
            "dimensions": ["whd", ],
            "whd": {
                "type": "struct", 
                "components": [
                    { "alias": "width", "unit": "meter" },
                    { "alias": "height", "unit": "meter" },
                    { "alias": "depth", "unit": "meter" } ] } },
        "imaging_plane": {
            "description": "Name of imaging plane description in /general/optophysiology",
            "data_type": "text",
            "references": "/general/optophysiology/<imaging_plane_X>"},
        "scan_line_rate": {
            "description": "Scan lines per second (Hz)",
            "unit": "Hz",
            "data_type": "number"},
#         "max_voltage": {
#             "data_type": "float",
#             "unit": "Volt"},
#         "min_voltage": {
#             "data_type": "float",
#             "unit": "Volt"},
#         "wavelength": {
#             "description": "Laser Wavelength, Units: nm or meters",
#             "data_type": "number"},        
#         "indicator": {
#             "description": "Imaging indicator (e.g., GCaMP6s) and response wavelength",
#             "data_type": "text"},
#         "imaging_depth": {
#             "description": "Imaging depth into tissue (i.e., below surface). Units: Meters",
#             "unit": "Meter",
#             "data_type": "float"},
    },   
    "<OpticalSeries>/": {
        "description": ("Image data that is presented or recorded. A stimulus template movie will"
            " be stored only as an image."),
        "attributes": {"ancestry": {"data_type":"text", "value":"TimeSeries,ImageSeries,OpticalSeries"},},
        "merge": ["<ImageSeries>/", ],
        "field_of_view": {
            "description": "Width, height and depto of image, or imaged area (meters)",
            "data_type": "float",
            "dimensions" : ["fov",],
            "fov" : {  # definition of dimension fov
                "type": "structure", 
                "components": [
                    { "alias": "width", "unit": "meter" },
                    { "alias": "height", "unit": "meter" },
                    { "alias": "depth", "unit": "meter", "optional": True } ] },
            },
        "distance": {
            "description": "Distance from camera/monitor to target/eye",
            "data_type": "float",
            "unit": "meter" },
        "orientation": {
            "description": ("Description of image relative to some reference frame (e.g.,"
                " which way is up). Must also specify frame of reference." ),
            "data_type": "text"}
    },
#     "<WidefieldSeries>/": {
#         "description": "Imagestack recorded from wide-field imaging",
#         "merge": ["<OpticalSeries>/", ],
#         "attributes": {"ancestry": {"data_type":"text", "value":"TimeSeries,ImageSeries,OpticalSeries,WidefieldSeries"},},
#         "indicator": {
#             "description": "Indicator used",
#             "data_type": "text"},
#         "illumination_power": {
#             "data_type": "float",
#             "unit": "Watts"},
#         "pixel_binning": {
#             "data_type": "int",
#             "dimensions" : ["xyt",] },
#         "xyt" : {  # definition of dimension fov
#                 "type": "structure", 
#                 "components": [
#                     { "alias": "x", "unit": "meter" },
#                     { "alias": "y", "unit": "meter" },
#                     { "alias": "t", "unit": "?" } ] },
#         "exposure_time": {
#             "data_type": "float",
#             "description": "Exposure Time",
#             "unit": "Second"},
#         "counts_per_bit": {
#             "data_type": "float",
#             "description": "Counts per bit"},
#     },   
    # Following specifies attributes associated with each module
    "<module>/": {
        "attributes": {
            "interfaces": {"data_type": "text", },
            "neurodata_type": {"data_type": "text", "value": "Module"}},
    },
    "<interface>/": {
        "attributes": {
            "source": {
                "data_type": "text",
                "description": "Path to the origin of the data represented in this interface",
                "references": "/"}}
    },
    "BehavioralEvents/": {
        "merge": ["<interface>/", ],
        "Description": "TimeSeries for storing behavioral irregular events",
        "include": {"<TimeSeries>/*": {"data": {"semantic_type": "+BehavorialEvents", }, }, },
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+BehavorialEvents",},},
    },
    "BehavioralEpochs/": {
        "merge": ["<interface>/", ],
        "Description": "TimeSeries for storing behavoioral epochs",
        "include": {"<IntervalSeries>/*": {"data": {"semantic_type": "+BehavorialEpochs", }, }, },
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+BehavorialEpochs",},},
    },
    "BehavioralTimeSeries/": {
        "merge": ["<interface>/", ],
        "Description": "Behavoioral time series",
        "include": {"<TimeSeries>/*": {"data": {"semantic_type": "+BehavioralTimeSeries", }, }, },
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+BehavorialEpochs",},},
    },   
    "Clustering/": {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+Clustering"}},
        "times": {
            "description": "Time of clustered events",
            "dimensions": ["eventIndex"],
            "data_type": "number",
            "unit": "second",
            "semantic_type": "timestamps"},
        "num": {
        	"description": "Cluster number of each event",
        	"dimensions": ["eventIndex"],
        	"data_type": "int"},
        "description": {
            "data_type": "text",
            "description": "Description of clusters or clustering, e.g. cluster 0 is noise, ..."},    
        "cluster_nums": {  # Not used with Buzsaki sample data
           "description": "List of cluster number that are a part of this set.",
		   "data_type": "int",
		   "dimensions": ["num_clusters"]},
        "peak_over_rms": {
            "description": "Maximum ration of waveform peak to RMS on any channel in the cluster",
            "data_type": "float",
            "dimensions": ["num_clusters"]}          
    },
    "ClusterWaveforms/": {
        "merge": ["<interface>/", ],
        "description": "The mean waveform shape, including standard deviation, of the different clusters.",
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+ClusterWaveforms"}},
        "waveform_mean": {
            "description": "The mean waveform for each cluster",
            "data_type": "float",
            "dimensions": ["num_clusters", "num_samples"]},
        "waveform_sd": {
            "description": "Stdev of waveforms for each cluster",
            "data_type": "float",
            "dimensions": ["num_clusters", "num_samples"]},
        "waveform_filtering": {
            "description":  "Filtering applied to data before generating mean/sd",
            "data_type": "text"},
        "clustering_interface/": {
            "description":  "HDF5 link to Clustering interface that was the source of the clustered data"},
        "clustering_interface_path": {
            "description":  "Path to linked clustering interface",
            "data_type": "text"}
    },       
    "CompassDirection/": {
        "merge": ["<interface>/", ],
        "description": "A SpatialSeries object representing a floating point value for theta.",
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+CompassDirection"}},
        "include": {"<SpatialSeries>/*": {} },
    },
    "DfOverF/": {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+DfOverF"},},
        "description": ("dF/F information about a region of interest (ROI). Storage hierarchy"
            " of dF/F should be the same as for segmentation (ie, same names for ROIs and for"
            " image planes). DfOverF/"),
        "include": {"<RoiResponseSeries>/*": {} },
    },
#         "<image_plane>/*": {
#             "attributes": {
#                 "description": {
#                     "data_type": "text",
#                     "description": "Description of image plane, recording wavelength, depth, etc"},},
#             "<roi_name>/*": {
#                 "description": "Name of region of interest",
#                 "merge": ["<timestamps>/"],
#                 "data": {
#                     "description": "dF/F signal",
#                     "dimensions": ["timeIndex"],
#                     "data_type": "number",
#                     "semantic_type": "TimeSeries" },
#                 "roi_segments": {
#                     "data_type": "text",
#                     "description": "<<< Need to fill in, not in docs>>>", },
#                 "trial_ids": {
#                     "data_type": "int",
#                     "description": "<<< Need to fill in, not in docs>>>", },
#             },
#         },
    "EventDetection/": {
        "merge": ["<interface>/", ],
        "description": "Detected spike events from voltage trace(s).",
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+EventDection"},},
		"times": {
			"description": "Spike time for the units",
			"dimensions": ["eventIndex"],
			"data_type": "number",
			"unit": "second",
			"semantic_type": "timestamps"},
		"detection_method": {
            "description": ("Description of how events were detected, such as voltage"
        		    " threshold, or dV/dT threshold, as well as relevant values"),
            "data_type": "text"},     		    
        "source_idx": {
            "description": ("Indices into source TimeSeries::data array corresponding to"
                " time of event."),
            "dimensions": ["eventIndex"],
			"data_type": "int",
			"references": "source_electrical_series/data.timeIndex"},
		"source_electricalseries/": {
            "description": "HDF5 link to TimeSeries that this data was calculated from."},
        "source_electricalseries_path": {
            "description": "Path to linked ElectricalSeries",
            "data_type": "text",
            "references": "/"}
        },
    "EventWaveform/" : {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+EventWaveform",},},
        "include": {"<SpikeEventSeries>/*": {} },
    },
    "EyeTracking/" : {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+EyeTracking",},},
        "include": {"<SpatialSeries>/*": {} },
    },
    "FeatureExtraction/" : {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+FeatureExtraction"},},
        "features": {
            "description": "Array of features extracted from each event",
            "dimensions": ["eventIndex", "channelIndex", "featureIndex"],
            "data_type": "number"},
        "times": {
            "description": "Time of events that features correspond to",
            "dimensions": ["eventIndex"],
            "data_type": "number",
            "unit": "second",
            "semantic_type": "timestamps"},
        "description": {
            "description": "Description of each feature",
            "dimensions": ["featureIndex"],
            "data_type": "text"},    
        "electrode_idx": {
            "description": "Indicies to electrodes in general/extracellular_ephys/electrode_map",
            "dimensions": ["channelIndex"],
            "data_type": "int",
            "references": "/general/extracellular_ephys/electrode_map.electrode_number"},
    },   
    "FilteredEphys/" : {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+FilteredEphys",},},
        "include": {"<ElectricalSeries>/*": {} },
    },
    "Fluorescence/" : {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+Fluorescence",},},
        "include": {"<ElectricalSeries>/*": {} },
    },
    "ImageSegmentation/" : {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+ImageSegmentation"},},
        "description": "Stores pixels in an image that represent different regions of interest (ROIs).",
        "<image_plane>/*" : {
            "description": {
                "data_type": "text",
                "description": "Description of image plane, recording wavelength, depth, etc"},
            "imaging_plane_name": {
                "data_type": "text",
                "description": "Name of imaging plane under general/optophysiology"},
            "roi_list": {
                "description": "List of ROIs in this imaging plane",
                "data_type": "text",
                "dimensions": ["num_rois"],
                "references": "<roi_name>/"},
            "<roi_name>/*": {
                "img_mask": {
                    "description": "ROI mask, represented in 2D ([y][x]) intensity image",
                    "data_type": "number",
                    "dimensions": ["numx","numy"]},
                "pix_mask": {
                    "description": "List of pixels (x,y) that compose mask",
                    "data_type": "float",
                    "dimensions": ["2","numPixels"],
                    "attributes": {
                        "weight": {
                            "description": "Weight of each pixel",
                            "data_type": "int",
                            # "dimensions": ["numPixels"] # feature to be added
                            },},},
                "roi_description": {
                    "description": "Description of this ROI",
                    "data_type": "text" },},
#                 "start_time_0": {
#                     "description": "Time when the mask starts to be used",
#                     "data_type": "number" },  # should be changed to float.
            "reference_images/": {
                "include": {"<ImageSeries>/*": {} },},
        },
    },
    "LFP/": {
        "merge": ["<interface>/", ],
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+LFP"}, },
        "include": {"<ElectricalSeries>/": {"data": {"semantic_type": "+LFP", }, }, },
    },
    "MotionCorrection/": {
        "merge": ["<interface>/", ],
        "description": ("An image stack where all frames are shifted (registered) to a common coordinate "
            "system, to account for movement and drift between frames."),
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+MotionCorrection"}, },
        "<image stack name>/": {
            "<original>/": {
                "description": "HDF5 Link to image series that is being registered"},
            "xy_translation/": {
                "description": ("Stores the x,y delta necessary to align each frame to"
                    " the common coordinates"),
                "include": {"<TimeSeries>/*": {} } },
            "corrected/": {
                "description": "Image stack with frames shifted to the common coordinates",
                "include": {"<ImageSeries>/*": {} } } }
    },
    "Position/": {
        "merge": ["<interface>/", ],
        "description": "Position data, whether along the x, x/y or x/y/z axis.",
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+Position"}, },
        "include": {"<SpatialSeries>/*": {} },
    },
    "PupilTracking/": {
        "merge": ["<interface>/", ],
        "description": "Eye-tracking data, representing pupil size.",
        "parent_attributes": {"interfaces": {"data_type":"text", "value":"+PupilTracking"}, },
        "include": {"<TimeSeries>/*": {"data": {"semantic_type": "PupilTracking", }, }, },
    },
    "UnitTimes/": {
        "merge": ["<interface>/", ],
        "description": "Event times of observed units (e.g. cell, synapse, etc.)",
        "parent_attributes": {"interfaces": {"data_type": "text", "value":"+UnitTimes"},},
        "unit_list": {
            "description": "List of units present",
            "data_type": "text",
            "dimensions": ["num_units",],
            "references": "<unit_N>/"},  # 1-to-1 is relationship type. To be implemented.
        "<unit_N>/*": {
            "times": {
                "description": "Spike time for the units",
            	"dimensions": ["eventIndex"],
            	"data_type": "number",
            	"unit": "second",
            	"semantic_type": "timestamps"},
        	"unit_description": {
        		"description": "Description of the unit (e.g. cell type)",
        		"data_type": "text"},
        	"source?": {
                "description": "Name, path or description of where unit times originatd",
                "data_type": "text"},}
    },
    "epochs/": {
        "description": "Top-level epochs group",
        "links": {
            "description": ("A human-readable list mapping TimeSeries entries in "
                "the epoch to the path of the TimeSeries within the file."),
            "data_type": "text"},
        "tags": {
            "description": ("A list of the different tags used by epochs."),
            "data_type": "text",
            "dimensions": ["num_tags"]},
		"<epoch_X>/": {
			"description": "Stores data about sub experiments or trial intervals",
			"attributes": {
				"neurodata_type": {"data_type": "text", "value": "Epoch", }, },            
			"description": {
				"data_type": "text", },
			"start_time": {
				"description": "Start time of epoch, in seconds",
				"data_type": "number",
				"unit": "second", },
			"stop_time": {
				"description": "Stop time of epoch, in seconds",
				"data_type": "float",
				"unit": "second", },
			"tags": {
				"description": "User defined tags that help characterize an epoch",
				"data_type": "text",
				"dimensions": ["num_tags"], },
			"<timeseries_X>/*" : {
				"description": "Reference for zero or more time series that overlap with epoch",
				"idx_start": {
					"description": "First index in timeseries::data that overlaps with this epoch",
					"data_type": "int", },
				"count": {
					"description": "Number of entries in TimeSeries::data that overlaps with this epoch",
					"data_type": "int", },
				"timeseries/": {
					"description": ("Link to timeseries.  Target timeseries can be" 
						" anywhere in the file"), }, }, },
    },
    # "/general"
    "session_id": {
        "data_type": "text",
        "description":"Lab-specific ID for the session."},
    "experimenter": {
        "data_type": "text",
        "description": "Name of person who performed the experiment"},
    "institution": {
        "data_type": "text",
         "description": "Institution(s) where experiment was performed"},
    "lab": {
        "data_type": "text",
        "description": "Lab where experiment was performed"},
#     "publication_info": {
#         "data_type": "text",
#         "description": "Information about publications related to this data"},
    "related_publications": {
        "data_type": "text",
         "description": "Publication information, such as PMID, DOI, URL, etc"},
    "notes": {
        "data_type": "text",
        "description": ("Notes about the experiment, especially things particular to"  
            " this experiment")},
    "experiment_description": {
        "data_type": "text",
        "description": "General description of the experiment"},
    "data_collection": {
        "data_type": "text",
        "description": "Notes about data collection and analysis"},
    "stimulus": {
        "data_type": "text",
        "description": "Notes about stimuli, such as how and where presented"},
    "pharmacology": {
        "data_type": "text",
        "description": ("Description of drugs used, including how and when they were"
            " administered")},
    "surgery": {
        "data_type": "text",
        "description": ("Narrative description about surgery/surgeries, including date(s)"
            " and who performed surgery")},                                    
    "protocol": {
        "data_type": "text",
        "description": "Experimetnal protocol, if applicable (e.g., IACUC)"},
    "subject/": {
		"subject_id": {
			"data_type": "text",
			"description": ("ID of animal/person used/participating in experiment"
				" (lab convention)")},
		"description": { 
			"data_type": "text",
			"description": ("Description of subject and where subject came from (e.g.,"  
				" breeder, if animal)")},                                          
		"species": {
			"data_type": "text",
			 "description": "Species of subject"},
		"genotype": {
			"data_type": "text",
			"description": "Genotype of subject"},
		"sex": {
			"data_type": "text",
			"description": "Gender of subject"},                                            
		"age": {
			"data_type": "text",
			"description": "Age of subject"},
		"weight": {
			"data_type": "text",
			"description": ("Weight at time of experiment, at time of surgery and at other"
				" important times")}
    },
    "virus": {
        "data_type": "text",
        "description": ("Information about virus(es) used in experiments, including"
            " virus ID, source, date made, injection location, volume, etc")
    },
    "slices": {
        "data_type": "text",
        "description": ("Description of slices, including information about preparation"
            " thickness, orientation, temperature and bath solution")
    },            
    # /acquisition/images/
    "<image_X>": {
        "data_type": "any",  # image could be numbers or a long string
        "description": "Documentation image (or movie).  Dimensions left unspecified",
        "attributes": {
            "format": {
                "data_type": "text",
                "description": "Format of the image (eg, 'png', 'avi')" },
            "description": {
                "data_type": "text",
                "description": "Descriptive text describing the image" },
            "neurodata_type": {
                "data_type": "text", "value": "image"}},
    },
    # general/intracellular_ephys
    "intracellular_ephys/": {
        "filtering": {
            "data_type": "text",
            "description": ("Description of filtering used, including filter type,"
                " parameters, fall-off, etc. If this changes between Time-Series then"
                " filter descriptions should be stored with the data") },
        "<electrode_X>/": {
            "description": ("One of possibly many folders describing electrode properties. "
                "Name should be informative.  This can optionally be a free-form text field "
                "that includes relevant description and metadata. (Using TAPI)"),
			"attributes": {
				"description": {
					"data_type": "text",
					"description": ("Recording description, description of electrode (e.g., "
					" whole-cell, sharp, etc)"), }, },
			"location": {
				"data_type": "text",
				"description": ("Area, layer, comments on estimation, stereotaxis coordinates"
					" (if in vivo, etc)") },
			"device": {
				"data_type": "text",
				"description": "Name(s) of devices in general/devices" },
			"slice": {
				"data_type": "text",
				"description": "Information about slice used for recording" },
			"initial_access_resistance": {
				"data_type": "text",
				"description": "Initial access resistance" },
			"seal": {
				"data_type": "text",
				"description": "Information about seal used for recording" },
			"resistance": {
				"data_type": "text",
				"unit": "Ohm",
				"description": "Electrode resistance in ohms" }},
	},			
    # /general/extracellular_ephys
    "extracellular_ephys/": {
		"electrode_map": {
			"description": "Physical location of electrode, x,y,z in meters",
			"dimensions": ["electrode_number","xyz"],  # specifies 2-D array
			"data_type": "number",
			"xyz" : {  # definition of dimension xyz
				"type": "struct", 
				"components": [
					{ "alias": "x", "unit": "meter" },
					{ "alias": "y", "unit": "meter" },
					{ "alias": "z", "unit": "meter" } ] }
		},
		"electrode_group": {
			"description": "Identification string for probe, shank or tetrode",
			"dimensions": ["electrode_number"],  # specifies 1-D array
			"references": "<electrode_group_X>/",
			"data_type": "text",
		},
		"impedance": {
			"description": "Impediance of electodes in electrode_map",
			"dimensions": ["electrode_number"],  # specifies 1-D array
			"data_type": "text"
		},
		"filtering": {
			"description": ("Description of filtering used.  If this changes between TimeSeries,"
			    " filter description should be stored as a text attribute for each TimeSeries."),
			"data_type": "text"
		},
		"<electrode_group_X>/": {
			"_description": "One folder for each electrode group.  Name matches group_id",
			"description": {  # this description is a dataset since it has a data_type
				"data_type": "text",
				"description": "Description of probe or shank", },          
			"location": {
				"data_type": "text",
				"description": "Description of probe location", },
			"device": {
				"data_type": "text",
				"description": "Name of device(s) in /general/devices",
				"references": "/general/devices/devices/<device_X>/", }
		}
	},
    "optophysiology/": {
        "<imaging_plane_X>/*": {
            "description": ("Folder one of possibly many folders describing an imaging plane."
                " Name is arbitrary but should be meaningful. It is referenced by TwoPhotonSeries"
                " and also ImageSegmentation and DfOverF interfaces."),
			"manifold": {
				"description": "Physical position of each pixel.",
				"data_type": "float",
				"dimensions": ["height", "weight", "xyz"],
				"attributes": {
					"unit": {"data_type": "text", "value": "Meter"},
					"conversion": {"data_type": "float", "value": 1.0}}},
			"xyz" : {  # definition of dimension xyz
				 "type": "struct", 
				"components": [
				    { "alias": "x", "unit": "meter" },
				    { "alias": "y", "unit": "meter" },
				    { "alias": "z", "unit": "meter" } ] },
			"reference_frame": {
				"description": ("Describes position and reference frame of manifold based on "
					"position of first element in manifold."),
				"data_type": "text" },
			"<channel_X>/": {
				"description": "One of possibly many folders storing channel-specific data",
			    "emission_lambda": {
			        "description": "Emission lambda for channel",
					"data_type": "text"},
			    "description": {
			        "description": "Any notes or comments about the channel",
					"data_type": "text"}},
			"indicator": {
				"description": "Calcium indicator",
				"data_type": "text" },
			"excitation_lambda": {
				"description": "Excitation wavelength",
				"data_type": "text" },
			"imaging_rate": {
				"data_type": "text" },
			"location": {
				"description": "Location of image plane",
				"data_type": "text" },
			"device": {
				"description": "Name of device in /general/devices",
				"data_type": "text",
				"references": "/general/devices/<device_X>/"}}
	},
	"optogenetics/": {
		"<site_X>/*": {
			"_description": ("One of possibly many folders describing an describing"
				" an optogenetic stimuluation site."),
			"description": {
				"data_type": "text"},
			"device": {
				"description": "Name of device in /general/devices",
				"data_type": "text",
				"references": "/general/devices/<device_X>/"},
			"excitation_lambda": {
				"description": "Excitation wavelength",
				"data_type": "text" },
			"location": {
				"description": "Location of stimulation site",
				"data_type": "text" }}
    },
    "devices/": {
        "description": "Description of hardware devices used during experiment.",
        "<device_X>*": {
            "description": "One of possibly many. Information about device and device description.",
            "data_type": "text"}
    }
}
# list of all TimeSeries types.  Used in locations below
time_series = [ "<TimeSeries>/*", "<AbstractFeatureSeries>/*", "<AnnotationSeries>/*",
        "<IndexSeries>/*", "<IntervalSeries>/*", "<OptogeneticSeries>/*",
        "<RoiResponseSeries>/*", "<SpatialSeries>/*", "<ElectricalSeries>/*",
        "<SpikeEventSeries>/*", "<PatchClampSeries>/*", "<VoltageClampStimulusSeries>/",
        "<CurrentClampStimulusSeries>/*", "<VoltageClampSeries>/*",
        "<CurrentClampSeries>/*", "<ImageSeries>/*", "<TwoPhotonSeries>/*",
        "<OpticalSeries>/*"]
        
# specify locations for where structures are stored in hdf5 file
# quantities are indicated by suffix: "!"- required, "*"- 0 or more, "+"- 1 or more, none- optional
nwb["core"]["locations"] = {
    "/":
        ["neurodata_version!", "identifier!", "file_create_date!", "session_start_time",
        "session_description", "epochs/"],
    "/general": 
        [ "session_id!", "experimenter!", "institution", "lab", "related_publications", "notes",
        "experiment_description", "data_collection", "stimulus", "pharmacology",  "surgery",
        "protocol", "subject/", "virus", "slices", "intracellular_ephys/",
        "extracellular_ephys/", "optogenetics/", "devices/", "__custom"],
    "/acquisition/images":
        [ "<image_X>*", ],
    "/acquisition/timeseries": time_series,
    "/stimulus/presentation": time_series,
    "/stimulus/templates": time_series,
    "/processing": [ "<module>/*",],
    "<module>/":
        ["BehavioralEvents/", "BehavioralEpochs/", "BehavioralTimeSeries/", "Clustering/",
        "ClusterWaveforms/", "CompassDirection/", "DfOverF/", "EventDetection/",
        "EventWaveform/", "EyeTracking/", "FeatureExtraction/", "FilteredEphys/",
        "Fluorescence/", "ImageSegmentation/", "LFP/", "MotionCorrection/",
        "Position/", "PupilTracking/", "UnitTimes/"]
}
