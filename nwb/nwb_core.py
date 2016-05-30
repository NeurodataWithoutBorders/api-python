# Definitions of NWB file format
# This is JSON, but allows Python comments (proceeded by #)
# and multiline strings in parentheses e.g. ("part-1" "part 2") or in triple quotes

# "fs" stands for 'format specification'
# "core" is the schema id (also called 'namespace')

{"fs": {"core": {

# info section has metadata about the schema

"info": {
    "name": "NWB file format specification",
    "version": "1.0.3-beta",
    "date": "May 23, 2016",
    "author": "Keith Godfrey.  Converted to format specification by Jeff Teeters.",
    "contact": "jteeters@berkeley.edu, keithg@alleninstitute.org",
    "description": "Specification for the core NWB (Neurodata Withoug Borders) format."
},

# schema section specifies all datasets and groups:
#     "identifier" - dataset
#     "identifier/" - group (has trailing slash)
#     "<identifier>" - dataset with variable name
#     "<identifier>/" - group with variable name
  
"schema": {
    "/": {
		"description": "Top level of NWB file.",
		# Example of how a root attribute would be specified:
		# "attributes": {
		# 	"nwb_version": {
		# 		"data_type": "text",
		# 		"value": fs["core"]["info"]["version"]}},
				
		"nwb_version": {
			"data_type": "text",
			"description": ("File version string. COMMENT: Eg, NWB-1.0.0. This will be the "
			    "name of the format with trailing major, minor and patch numbers.")},

		"identifier": {
			"data_type": "text",
			"description": "A unique text identifier for the file. COMMENT: Eg, concatenated "
			    "lab name, file creation date/time and experimentalist, or a hash of these "
			    "and/or other values. The goal is that the string should be unique to all "
			    "other files."},

		"file_create_date": {
            "data_type": "text",
            "description": ("Time file was created, UTC, and subsequent modifications to file. "
                "COMMENT: Date + time, Use ISO format (eg, ISO 8601) or a format that is "
                "easy to read and unambiguous. File can be created after "
                "the experiment was run, so this may differ from experiment start "
                "time. Each modifictation to file adds new entry to array. "),
            "dimensions": ["*unlimited*"]},

		"session_start_time": {
			"data_type": "text",
			"description": ("Time of experiment/session start, UTC.  COMMENT: Date "
                "+ time, Use ISO format (eg, ISO 8601) or an easy-to-read and unambiguous "
                "format. All times stored in the "
                "file use this time as reference (ie, time zero)")},
                
		"session_description": {
			"data_type": "text",
			"description": "One or two sentences describing the experiment and data in the file."},
			
	},
	"/acquisition/": {
	    "description": ("Data streams recorded from the system, including ephys, ophys, tracking, etc. "
		    "COMMENT: This group is read-only after the experiment is completed and timestamps are corrected to "
		    "a common timebase. The data stored here may be links to raw data stored in external HDF5 "
		    "files. This will allow keeping bulky raw data out of the file while preserving the option "
		    "of keeping some/all in the file. "
		    "MORE_INFO: Acquired data includes tracking and experimental data streams (ie, "
		    "everything measured from the system)."
		    "If bulky data is stored in the /acquisition group, the data can exist in a "
		    "separate HDF5 file that is linked to by the file being used for processing "
		    "and analysis."),
		"autogen": { "type": "create"},
		"images/": {
            "description": "Acquired images",
            "autogen": { "type": "create"},
            "<image_X>*": {
				"data_type": "binary",
				"description": ("Photograph of experiment or experimental setup (video also OK). "
					"COMMENT: Name is arbitrary.  Data is stored as a single binary object "
					"(HDF5 opaque type)."),
				"attributes": {
					"format": {
						"data_type": "text",
						"description": "Format of the image.  COMMENT: eg, jpg, png, mpeg" },
					"description^": {
						"data_type": "text",
						"description": ("Human description of image. "
							"COMMENT: If image is of slice data, include slice thickness and "
							"orientation, and reference to appropriate entry in /general/slices")}}}},
            # "include": {"<image_X>*": {}},
        "timeseries/": {
            "description": ("Acquired TimeSeries."
                "COMMENT: When importing acquisition data to an NWB file, "
                "all acquisition/tracking/stimulus data must already be aligned to a common time "
                "frame. It is assumed that this task has already been performed."),
            "autogen": { "type": "create"},
            "include":  {
                "<TimeSeries>/*":{"_options": {"subclasses": True}},
                }}
    },
    "/analysis/": {
        "description": ("Lab-specific and custom scientific analysis of data. There is no "
            "defined format for the content of this group - the format is up to the individual "
            "user/lab. COMMENT: To facilitate sharing analysis data between labs, the contents "
            "here should be stored in standard types (eg, INCF types) and appropriately "
            "documented. "
            "MORE_INFO: The file can store lab-specific and custom data analysis without "
            "restriction on its form or schema, reducing data formatting restrictions on "
            "end users. Such data should be placed in the analysis group. The analysis data "
            "should be documented so that it is sharable with other labs"),
        "autogen": { "type": "create"}
    },
    "/epochs/": {
        "description": ("Experimental intervals, whether that be logically distinct sub-experiments "
            "having a particular scientific goal, trials during an experiment, or epochs deriving "
            "from analysis of data.  COMMENT: Epochs provide pointers to time series that are "
            "relevant to the epoch, and windows into the data in those time series (i.e., the start "
            "and end indices of TimeSeries::data[] that overlap with the epoch). This allows easy "
            "access to a range of data in specific experimental intervals. "
            "MORE_INFO: An experiment can be separated "
            "into one or many logical intervals, with the order and duration of these intervals "
            "often definable before the experiment starts. In this document, and in the context "
            "of NWB, these intervals are called 'epochs'. Epochs have acquisition and stimulus "
            "data associated with them, and different epochs can overlap. Examples of epochs are "
            "the time when a rat runs around an enclosure or maze as well as intervening sleep "
            "sessions; the presentation of a set of visual stimuli to a mouse running on a "
            "wheel; or the uninterrupted presentation of current to a patch-clamped cell. Epochs "
            "can be limited to the interval of a particular stimulus, or they can span multiple "
            "stimuli. Different windows into the same time series can be achieved by including "
            "multiple instances of that time series, each with different start/stop times."),
        "autogen": { "type": "create"},
        "attributes": {
            "tags": {
                "description": ("A sorted list of the different tags used by epochs. "
                    "COMMENT:This is a sorted list of all tags that are in any of the "
                    "&lt;epoch_X&gt;/tags datasets`."),
                "data_type": "text",
                "dimensions": ["num_tags",],
                "autogen": {
                    "type": "values",
                    "target":"<epoch_X>/tags",
                    "trim": True,
                    "qty": "*",
                    "include_empty": True}}},                    
        "<epoch_X>/*": {
            "_description": ("One of possibly many different experimental epoch"
                "COMMENT: Name is arbitrary but must be unique within the experiment."),   
            "attributes": {
                "neurodata_type": {
                    "description": "The string \"Epoch\"",
                    "data_type": "text", "value": "Epoch", "const": True },
                "links": {
                    "description": ("A sorted list "
                    "mapping TimeSeries entries in "
                    "the epoch to the path of the TimeSeries within the file. "
                    "Each entry in the list has the following format: "
                    "\"'<i>&lt;TimeSeries_X&gt;</i>' <b>is</b> '<i>path_to_TimeSeries</i>'\", "
                    "where <i>&lt;TimeSeries_X&gt;</i> is the name assigned to group "
                    " &lt;TimeSeries_X&gt; (below). Note that the name and path are both "
                    "enclosed in single quotes and the word \"is\" (with a single space before "
                    "and after) separate them. "
                    "<b>Example list element:</b> "
                    "\"'auditory_cue' is '/stimulus/presentation/auditory_cue'\"."
                    ),
                    "data_type": "text",
                    "dimensions": "num_links",
                    "autogen": {
                        "type": "link_path",
                        "target":"<timeseries_X>/timeseries",
                        "trim": True,
                        "qty": "*",
                        "format": "'$s' is '$t'",
                        "include_empty": True}},
                 },
            "description?": {
                "data_type": "text",
                "description": "Description of this epoch (&lt;epoch_X&gt;)."},
            "start_time": {
                "description": "Start time of epoch, in seconds",
                "data_type": "float64!",
                "unit": "second", },
            "stop_time": {
                "description": "Stop time of epoch, in seconds",
                "data_type": "float64!",
                "unit": "second", },
            "tags?": {
                "description": ("User-defined tags used throughout "
                    "the epochs. Tags are "
                    "to help identify or categorize epochs. "
                    "COMMENT: E.g., can describe stimulus (if template) or behavioral "
                    "characteristic (e.g., \"lick left\")"),
                "data_type": "text",
                "dimensions": ["num_tags"]},
            "<timeseries_X>/*" : {
                "description": ("One of possibly many input or output streams recorded during epoch. "
                    "COMMENT: Name is arbitrary and does not have to match the TimeSeries that "
                    "it refers to."),
                "idx_start": {
                    "description": ("Epoch's start index in TimeSeries data[] field. "
                    "COMMENT: This can be used to calculate location in TimeSeries timestamp[] "
                    "field"),
                    "data_type": "int32", },
                "count": {
                    "description": ("Number of data samples available in this time series, "
                        "during this epoch."),
                    "data_type": "int32", },
                "timeseries/": {
                    "description": ("Link to TimeSeries.  An HDF5 soft-link should be "
                        "used."),
                    "link": {"target_type": "<TimeSeries>/", "allow_subclasses": True } } } }
    },
    "/general/": {
        "description": ("Experimental metadata, including protocol, notes and description "
            "of hardware device(s).  COMMENT: The metadata stored in this section should "
            "be used to describe the experiment. Metadata necessary for interpreting the "
            "data is stored with the data. "
            "MORE_INFO: General experimental metadata, including animal strain, experimental "
            "protocols, experimenter, devices, etc, are stored under 'general'. "
            "Core metadata (e.g., that required to interpret data fields) is "
            "stored with the data itself, and implicitly defined by the file "
            "specification (eg, time is in seconds). The strategy used here for "
            "storing non-core metadata is to use free-form text fields, such as "
            "would appear in sentences or paragraphs from a Methods section. "
            "Metadata fields are text to enable them to be more general, for "
            "example to represent ranges instead of numerical values. "
            "Machine-readable metadata is stored as attributes to these free-form "
            "datasets. <br /><br />"
            "All entries in the below table are to be included when data is present. "
            "Unused groups (e.g., intracellular_ephys in an optophysiology experiment) "
            "should not be created unless there is data to store within them."),
        "autogen": { "type": "create"},
        "__custom?": {
            "description": ("TIndicates that this group (general/) is the default location for custom"
                " nodes.  This dataset in the format specification is just a flag. "
                " There is no actual data stored in the HDF5 file for this data sets."),
            "data_type": "int"},
		"session_id^": {
			"data_type": "text",
			"description":("Lab-specific ID for the session."
			    "COMMENT: Only 1 session_id per file, with all time aligned to "
			    "experiment start time.")},
		"experimenter^": {
			"data_type": "text",
			"description": ("Name of person who performed the experiment."
			    "COMMENT: More than one person OK. Can specify roles of different people involved.")},
		"institution^": {
			"data_type": "text",
			 "description": "Institution(s) where experiment was performed"},
		"lab^": {
			"data_type": "text",
			"description": "Lab where experiment was performed"},
		"related_publications?": {
			"data_type": "text",
			 "description": ("Publication information."
			     "COMMENT: PMID, DOI, URL, etc. If multiple, concatenate together and describe "
			         "which is which. such as PMID, DOI, URL, etc")},
		"notes?": {
			"data_type": "text",
			"description": ("Notes about the experiment.  COMMENT: Things particular to"  
				" this experiment")},
		"experiment_description^": {
			"data_type": "text",
			"description": ("General description of the experiment."
			    "COMMENT: Can be from Methods")},
		"data_collection?": {
			"data_type": "text",
			"description": ("Notes about data collection and analysis."
			    "COMMENT: Can be from Methods")},
		"stimulus?": {
			"data_type": "text",
			"description": ("Notes about stimuli, such as how and where presented."
			    "COMMENT: Can be from Methods")},
		"pharmacology?": {
			"data_type": "text",
			"description": ("Description of drugs used, including how and when they were"
				" administered. "
				"COMMENT: Anesthesia(s), painkiller(s), etc., plus dosage, concentration, "
				"etc.")},
		"surgery?": {
			"data_type": "text",
			"description": ("Narrative description about surgery/surgeries, including date(s)"
				" and who performed surgery. "
				"COMMENT: Much can be copied from Methods")},                                    
		"protocol?": {
			"data_type": "text",
			"description": ("Experimetnal protocol, if applicable."
			    "COMMENT: E.g., include IACUC protocol")},
		"subject/?": {
			"_description": ("Information about the animal or person from which the "
			    "data was measured."),
			"subject_id?": {
				"data_type": "text",
				"description": ("ID of animal/person used/participating in experiment"
					" (lab convention)")},
			"description?": { 
				"data_type": "text",
				"description": ("Description of subject and where subject came from (e.g.,"  
					" breeder, if animal)")},                                          
			"species?": {
				"data_type": "text",
				 "description": "Species of subject"},
			"genotype?": {
				"data_type": "text",
				"description": ("Genetic strain "
				    "COMMENT: If absent, assume Wild Type (WT)")},
			"sex?": {
				"data_type": "text",
				"description": "Gender of subject"},                                            
			"age?": {
				"data_type": "text",
				"description": "Age of subject"},
			"weight?": {
				"data_type": "text",
				"description": ("Weight at time of experiment, at time of surgery and at other"
					" important times")}
		},
		"virus?": {
			"data_type": "text",
			"description": ("Information about virus(es) used in experiments, including"
				" virus ID, source, date made, injection location, volume, etc")
		},
		"slices?": {
			"data_type": "text",
			"description": ("Description of slices, including information about preparation"
				" thickness, orientation, temperature and bath solution")
		},
		"devices/?": {
			"description": ("Description of hardware devices used during experiment. "
			    "COMMENT: Eg, monitors, ADC boards, microscopes, etc"),
			"<device_X>*": {
				"description": ("One of possibly many. Information about device and device "
				    "description. "
				    "COMMENT: Name should be informative. Contents can be from Methods."),
				"data_type": "text"},
        },
        "source_script?": {
            "description": "Script file used to create this NWB file.",
                "attributes": {
                    "file_name?": {
                        "description": "Name of script file",
                        "data_type": "text" }
                },
                "data_type": "text"
        },
        "specifications/?": {
			"description": "Group for storing format specification files.",
			"<specification_file>*": {
				"description": "Dataset for storing contents of a specification file for either "
					"the core format or an extension.  Name should match name of file.`",
				"attributes": {
					"help?": {
					    "data_type": "text",
					    "value": "Contents of format specification file." },
					"namespaces": {
					    "description": "Namespaces defined in the file",
					    "data_type": "text",
					    "dimensions": ["num_namespaces"]
					    }
	#                 "version": { "data_type": "text"},
	#                 "date": { "data_type": "text"},
	#                 "author": {"data_type": "text"},
	#                 "contact": {"data_type": "text"},
	#                 "description": {"data_type": "text"},
				},
				"data_type": "text"
			}
        }
    },
    "/general/intracellular_ephys/?": {
        "description": "Metadata related to intracellular electrophysiology",
        "filtering?": {
            "data_type": "text",
            "description": ("Description of filtering used. "
                "COMMENT: Includes filtering type and parameters, frequency "
                "fall- off, etc. If this changes between TimeSeries, filter description "
                "should be stored as a text attribute for each TimeSeries.") },
        "<electrode_X>/": {
            "_description": ("One of possibly many. "
            "COMMENT: Name should be informative."),
			"description": {
				"data_type": "text",
				"description": ("Recording description, description of electrode (e.g., "
				" whole-cell, sharp, etc)"
				"COMMENT: Free-form text (can be from Methods)")},
            "location?": {
                "data_type": "text",
                "description": ("Area, layer, comments on estimation, stereotaxis coordinates"
                    " (if in vivo, etc)") },
            "device?": {
                "data_type": "text",
                "description": "Name(s) of devices in general/devices" },
            "slice?": {
                "data_type": "text",
                "description": "Information about slice used for recording" },
            "initial_access_resistance?": {
                "data_type": "text",
                "description": "Initial access resistance" },
            "seal?": {
                "data_type": "text",
                "description": "Information about seal used for recording" },
            "resistance?": {
                "data_type": "text",
                "description": "Electrode resistance COMMENT: unit: Ohm" },
            "filtering?": {
                "data_type": "text",
                "description": "Electrode specific filtering."}
        },
    },            
    "/general/extracellular_ephys/?": {
        "description": "Metadata related to extracellular electrophysiology.",
        "electrode_map": {
            "description": ("Physical location of electrode, (x,y,z in meters) "
                "COMMENT: Location of electrodes relative to one another. This "
                "records the points in space. If an electrode is moved, it needs "
                "a new entry in the electrode map for its new location. Otherwise "
                "format doesn't support using the same electrode in a new location, "
                "or processing spikes pre/post drift."),
            "dimensions": ["num_electrodes","xyz"],  # specifies 2-D array
            "data_type": "number",
            "xyz" : {  # definition of dimension xyz
                "type": "struct", 
                "components": [
                    { "alias": "x", "unit": "meter" },
                    { "alias": "y", "unit": "meter" },
                    { "alias": "z", "unit": "meter" } ] }
        },
        "electrode_group": {
            "description": ("Identification string for probe, shank or tetrode "
                "each electrode resides on. Name should correspond to one of "
                "electrode_group_X groups below. "
                "COMMENT: There's one entry here for each element in electrode_map. "
                "All elements in an electrode group should have a functional association, "
                "for example all being on the same planar electrode array, or on the "
                "same shank."),
            "dimensions": ["num_electrodes"],  # specifies 1-D array
            "references": "<electrode_group_X>/",
            "data_type": "text",
        },
        "impedance": {
            "description": ("Impedence of electrodes listed in electrode_map. "
                "COMMENT: Text, in the event that impedance is stored as range "
                "and not a fixed value"),
            "dimensions": ["num_electrodes"],  # specifies 1-D array
            "data_type": "text"
        },
        "filtering": {
            "description": ("Description of filtering used. "
                "COMMENT: Includes filtering type and parameters, frequency fall- off, "
                "etc. If this changes between TimeSeries, filter description should be "
                "stored as a text attribute for each TimeSeries.  If this changes between "
                "TimeSeries, filter description should be stored as a text attribute "
                "for each TimeSeries."),
            "data_type": "text"
        },
        "<electrode_group_X>/": {
            "_description": ("One of possibly many groups, one for each electrode group. "
                "If the groups have a hierarchy, such as multiple probes each having multiple "
                "shanks, that hierarchy can be mirrored here, using groups for "
                "electrode_probe_X and subgroups for electrode_group_X."
                "COMMENT: Name is arbitrary but should be meaningful."),
            "description": {  # this description is a dataset since it is a dict with a data_type
                "data_type": "text",
                "description": "Description of probe or shank", },          
            "location": {
                "data_type": "text",
                "description": ("Description of probe location"
                    "COMMENT: E.g., stereotaxic coordinates and other data, e.g., drive "
                    "placement, angle and orientation and tetrode location in drive and "
                    "tetrode depth") },
            "device": {
                "data_type": "text",
                "description": "Name of device(s) in /general/devices",
                "references": "/general/devices/devices/<device_X>/", }
        }
    },
    "/general/optophysiology/?": {
        "description": "Metadata related to optophysiology.",
        "<imaging_plane_X>/*": {
            "_description": ("One of possibly many groups describing an imaging plane. "
                "COMMENT: Name is arbitrary but should be meaningful. It is referenced by "
                "TwoPhotonSeries and also ImageSegmentation and DfOverF interfaces"),
            "description?": {
                "description": "Description of &lt;image_plane_X&gt;",
                "data_type": "text"
            },
            "manifold": {
                "description": ("Physical position of each pixel. "
                "COMMENT: \"xyz\" represents the position of the pixel relative to the "
                "defined coordinate space"),
                "data_type": "float32",
                "dimensions": ["height", "weight", "xyz"],
                "attributes": {
                    "unit": {
                        "description": ("Base unit that coordinates are stored in "
                            "(e.g., Meters)"),
                            "data_type": "text", "value": "Meter"},
                    "conversion": {
                        "description": ("Multiplier to get from stored values to specified "
                            "unit (e.g., 1e-3 for millimeters)"),
                        "data_type": "float", "value": 1.0}},
                "xyz" : {  # definition of dimension xyz
                     "type": "struct", 
                    "components": [
                        { "alias": "x", "unit": "Meter" },
                        { "alias": "y", "unit": "Meter" },
                        { "alias": "z", "unit": "Meter" } ] }},
            "reference_frame": {
                "description": ("Describes position and reference frame of manifold based "
                    "on position of first element in manifold. For example, text description "
                    "of anotomical location or vectors needed to rotate to common anotomical "
                    "axis (eg, AP/DV/ML). "
                    "COMMENT: This field is necessary to interpret manifold. If manifold is "
                    "not present then this field is not required"),
                "data_type": "text" },
            "<channel_X>/": {
                "_description": ("One of possibly many groups storing channel-specific data "
                    "COMMENT: Name is arbitrary but should be meaningful"),
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
                "description": "Rate images are acquired, in Hz.",
                "data_type": "text" },
            "location": {
                "description": "Location of image plane",
                "data_type": "text" },
            "device": {
                "description": "Name of device in /general/devices",
                "data_type": "text",
                "references": "/general/devices/<device_X>/"}}
    },
    "/general/optogenetics/?": {
        "description": "Metadata describing optogenetic stimuluation",
        "<site_X>/*": {
            "_description": ("One of possibly many groups describing an optogenetic "
            "stimuluation site. "
            "COMMENT: Name is arbitrary but should be meaningful. Name is referenced "
            "by OptogeneticSeries"),
            "description": {
                "description": "Description of site",
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
    "/processing/": {
        "description": ("The home for processing Modules. These modules perform intermediate "
            "analysis of data that is necessary to perform before scientific analysis. "
            "Examples include spike clustering, extracting position from tracking data, stitching "
            "together image slices. "
            "COMMENT: Modules are defined below. They can be large and express many data sets "
            "from relatively complex analysis (e.g., spike detection and clustering) or small, "
            "representing extraction of position information from tracking video, or even binary"
            " ""lick/no-lick"" decisions. Common software tools (e.g., klustakwik, MClust) are "
            "expected to read/write data here. "
            "MORE_INFO: 'Processing' refers to intermediate analysis of the acquired data to make "
            "it more amenable to scientific analysis. These are performed using Modules, as "
            "defined above. All modules reside in the processing group."),
        "autogen": { "type": "create"},
		"<Module>/*": {
			"description": ("Module.  Name should be descriptive. "
			    "Stores a collection of related data organized by "
			    "contained interfaces.  Each interface is a contract specifying content "
				"related to a particular type of data."),
			"attributes": {
			    "description?": {
                    "data_type": "text",
                    "description": "Description of Module"},
				# "interfaces": {"data_type": "text", "dimensions": ["num_interfaces",]},
				"interfaces": {
				    "description": ("Names of the data interfaces offered by this module. "
				        "COMMENT: E.g., [0]=\"EventDetection\", [1]=\"Clustering\", "
				            "[2]=\"FeatureExtraction\""),
					"data_type": "text",
					"dimensions": ["num_interfaces",],
					"autogen": {
						"type": "names",
						"target":"<*>/",
						# should modify autogen to use target <Interface> subclass, rather than tsig
						# "target":"<Interface>/",
						"tsig": {"type": "group",
 						    "attrs": { "neurodata_type": "Interface"}},
						"trim": True,
						"qty": "*"}},
				"neurodata_type": {
				    "description": "The string \"Module\"",
				       "data_type": "text", "value": "Module", "const":True}},
            "include": { "<Interface>/*": {"_options": {"subclasses": True}}}
		}
	},
    "/stimulus/": {
        "description": ("Data pushed into the system (eg, video stimulus, sound, voltage, etc) and "
            "secondary representations of that data (eg, measurements of something used as a "
            "stimulus) COMMENT: This group is read-only after experiment complete and timestamps "
            "are corrected to common timebase. Stores both presented stimuli and stimulus templates, "
            "the latter in case the same stimulus is presented multiple times, or is pulled from an "
            "external stimulus library."
            "MORE_INFO: Stimuli are here defined as any signal that is pushed into the system "
            "as part of the experiment (eg, sound, video, voltage, etc). Many different "
            "experiments can use the same stimuli, and stimuli can be re-used during an "
            "experiment. The stimulus group is organized so that one version of template "
            "stimuli can be stored and these be used multiple times. These templates can "
            "exist in the present file or can be HDF5-linked to a remote library file."
            ),
        "autogen": { "type": "create"},
        "presentation/": {
            "description": "Stimuli presented during the experiment.",
            "autogen": { "type": "create"},
            "include": {
                "<TimeSeries>/*":{"_options": {"subclasses": True}},
            }
        },
        "templates/": {
            "description": ("Template stimuli. "
                "COMMENT: Time stamps in templates are based on stimulus design and are "
                "relative to the beginning of the stimulus. When templates are used, the "
                "stimulus instances must convert presentation times to the experiment's "
                "time reference frame."),
            "autogen": { "type": "create"},
            "include": {
                "<TimeSeries>/*":{"_options": {"subclasses": True}},
            }
        },
    },
    # start of id's without absolute path
    # base timeSeries structure
    "<TimeSeries>/": {
        "description": "General purpose time series.",
        "attributes": {
            "description^": {
                "data_type": "text",
                # "value": "", # default empty string
                "description": "Description of TimeSeries"},
            "comments^": {
                "data_type": "text",
                # "value":"", # default empty string
                "description": ("Human-readable comments about the TimeSeries. This second "
                    "descriptive field can be used to store additional information, or "
                    "descriptive information if the primary description field is populated "
                    "with a computer-readable string.")},
            "source": {
                "description": ("Name of TimeSeries or Modules that serve as the source for "
                    "the data contained here. It can also be the name of a device, for "
                    "stimulus or acquisition data"),
                # "value": "",  # default to empty string if nothing specified          
                "data_type": "text"},
            "ancestry": {
                "data_type": "text", "value": ["TimeSeries"], "const": True,
                "description": ("The class-hierarchy of this TimeSeries, with one entry "
                    "in the array for each ancestor. An alternative and equivalent "
                    "description is that this TimeSeries object contains the datasets "
                    "defined for all of the TimeSeries classes listed. The class hierarchy "
                    "is described more fully below. "
                    "COMMENT: For example: [0]=""TimeSeries"", [1]=""ElectricalSeries"" "
                    "[2]=""PatchClampSeries"". The hierarchical order should be preserved "
                    "in the array -- i.e., the parent object of subclassed element N in the "
                    "array should be element N-1")},
            "neurodata_type": {
                "data_type": "text", "value": "TimeSeries", "const": True},
                # "description": "The string \"TimeSeries\"",
            "data_link": {
                "description": ("A sorted list of the paths of all TimeSeries that share a link "
                    "to the same data field. "
                    "Example element of list: \"/stimulus/presentation/Sweep_0\"` "
                    "COMMENT: Attribute is only present if links are present. "
                    "List should include the path to this TimeSeries also."),
                "data_type": "text",
                "dimensions": ["num_dlinks"],
                "autogen": {
                    "type": "links",
                    "target":"data",
                    "trim": True,
                    "qty": "*"}},
            "timestamp_link": {
                "description": ("A sorted list of the paths of all TimeSeries that share a link "
                    "to the same timestamps field.  "
                    "Example element of list: \"/acquisition/timeseries/lick_trace\" "
                    "COMMENT: Attribute is only present if links "
                    "are present. List should include the path to this TimeSeries also."),
                "data_type": "text",
                # dimension commented out to make a single string
                # "dimensions": ["num_tslinks"],
                "autogen": {
                    "type": "links",
                    "target":"timestamps",
                    "trim": True,
                    "qty": "*"}},
            "missing_fields^": {
                "description": ("List of fields that are not optional (i.e. either "
                    "required or recommended parts of the"
                    " TimeSeries) that are missing. "
                    "COMMENT: Only present if one or more required or recommended fields are missing. Note that "
                    "a missing required field (such as data or timestamps) should generate an error "
                    "by the API"),
                "data_type": "text",
                "dimensions": ["num_missing_fields"],
                "autogen": {
                    "type": "missing",
                    # "target": 
                    # "trim": True,
                    "qty": "*"}},
            "extern_fields^": {
                "description": ("List of fields that are HDF5 external links."
                    "COMMENT: Only present if one or more datasets is set to an HDF5 external link."),
                "data_type": "text",
                "dimensions": ["num_extern_fields"],
                "autogen": {
                    "type": "extern",
                    # "target": 
                    # "trim": True,
                    "qty": "*"}},                    
            "help?": {
                "description": ("Short description indicating what this type of TimeSeries stores."),
                "data_type": "text",
                "value": "General time series object",
                "const": True
                }
        },
        "timestamps": {
            "description": ("Timestamps for samples stored in data."
                "COMMENT: Timestamps here have all been corrected to the common experiment "
                "master-clock. Time is stored as seconds and all timestamps are relative to "
                "experiment start time."),
            "data_type": "float64!",
            "dimensions": ["num_times"],
            "attributes": {
                "interval": {
                    "description": ("The number of samples between each timestamp. "
                        "COMMENT: Presently this value is restricted to 1 (ie, a timestamp "
                        "for each sample)"),
                    "data_type": "int32", "value": 1, "const": True},
                "unit": {
                    "description": ("The string \"Seconds\" "
                        "COMMENT: All timestamps in the file are stored in seconds. "
                        "Specifically, this is the number of seconds since the start of the "
                        "experiment (i.e., since session_start_time)"),
                    "data_type": "text", "value": "Seconds"} }
        },
        "_required": { # Specifies required member combinations",
            "start_time" :
                ["starting_time XOR timestamps",
                    "Either starting_time or timestamps must be present, but not both."],
            "control": 
                ["(control AND control_description) OR (NOT control AND NOT control_description)",
                    ("If either control or control_description are present, then "
                    "both must be present.")]},
        "starting_time?": {
            "description": ("The timestamp of the first sample. "
                "COMMENT: When timestamps are uniformly spaced, the timestamp of the first "
                "sample can be specified and all subsequent ones calculated from the "
                "sampling rate."),
            "data_type": "float64!",
            "attributes": {
                "rate": {
                    "description": ("Sampling rate, in Hz "
                        "COMMENT: Rate information is stored in Hz"),
                    "data_type": "float32!"},
                "unit": {
                    "description": ("The string \"Seconds\""
                        "COMMENT: All timestamps in the file are stored in seconds. "
                        "Specifically, this is the number of seconds since the start of the "
                        "experiment (i.e., since session_start_time)"),
                    "data_type": "text",
                    "value": "Seconds"}},
        },       
        "num_samples": {
            "description": ("Number of samples in data, or number of image frames. "
                "COMMENT: This is important if the length of timestamp and data are "
                "different, such as for externally stored stimulus image stacks"),
            "data_type": "int32",
            "autogen": {
                    "type": "length",
                    "target":"timestamps"},
        },
        "control?": {
            "description": ("Numerical labels that apply to each element in data[]. "
                "COMMENT: Optional field. If present, the control array should have the "
                "same number of elements as data[]."), 
            "data_type": "uint8",
            "dimensions": ["num_times"],
            "references": "control_description.num_control_values"
        }, 
        "control_description?": {
            "data_type": "text",
            "dimensions": ["num_control_values"],
            "description": ("Description of each control value. COMMENT: Array length should "
                "be as long as the highest number in control minus one, generating an "
                "zero-based indexed array for control values.")
        },
        "sync/?": {
            "description": ("Lab specific time and sync information as provided directly "
                "from hardware devices and that is necessary for aligning all acquired "
                "time information to a common timebase. The timestamp array stores time "
                "in the common timebase. "
                "COMMENT: This group will usually only be populated in TimeSeries that "
                "are stored external to the NWB file, in files storing raw data. Once "
                "timestamp data is calculated, the contents of 'sync' are mostly for "
                "archival purposes.") },   
        "data": {
            "description": ("Data values. Can also store binary data (eg, image frames) "
                "COMMENT: This field may be a link to data stored in an external file, "
                "especially in the case of raw data."),
            "attributes": {
                "conversion": {
                    "description": ("Scalar to multiply each element in data to convert it to "
                        "the specified unit"),
                    "value": 1.0, # default value
                    "data_type": "float32!" },
                "unit": {
                    "description": ("The base unit of measure used to store data. This should "
                        "be in the SI unit. "
                        "COMMENT: This is the SI unit (when appropriate) of the stored data, "
                        "such as Volts. If the actual data is stored in millivolts, the field "
                        "'conversion' below describes how to convert the data to the specified "
                        "SI unit."),
                    "data_type": "text"},
                "resolution": {
                    "description": ("Smallest meaningful difference between values in data, stored "
                        "in the specified by unit. "
                        "COMMENT: E.g., the change in value of the least significant bit, or a larger "
                        "number if signal noise is known to be present. If unknown, use NaN"),
                        "value": 0.0, # default value
                        "data_type": "float32!"},
            },
            "dimensions": ["num_times"], # specifies 1-d array
            "data_type": "any"
        },
    },
    "<AbstractFeatureSeries>/": {
        "description": (
            "Abstract features, such as quantitative descriptions of sensory "
            "stimuli. The TimeSeries::data field is a 2D array, storing those features (e.g., "
            "for visual grating stimulus this might be orientation, spatial frequency and "
            "contrast). Null stimuli (eg, uniform gray) can be marked as being an independent "
            "feature (eg, 1.0 for gray, 0.0 for actual stimulus) or by storing NaNs for "
            "feature values, or through use of the TimeSeries::control fields. A set of "
            "features is considered to persist until the next set of features is defined. "
            "The final set of features stored should be the null set."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {"data_type": "text",
                "dimensions": ["2"],
                "value":["TimeSeries","AbstractFeatureSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Features of an applied stimulus. This is useful when storing the raw "
                    "stimulus is impractical"),
                "const": True}},
        "features": {
            "description": "Description of the features represented in TimeSeries::data.",
            "dimensions": ["num_features"],
            "data_type": "text"},
        "feature_units^": {
            "description": "Units of each feature.",
            "dimensions": ["num_features"],
            "data_type": "text"},
        "data": {
            "description": "Values of each feature at each time.", 
            "dimensions": ["num_times", "num_features"],
            "data_type": "float32",
            "attributes": { "unit": {
                "value": "see 'feature_units'"}}},
    },
    "<AnnotationSeries>/": {
        "description": ("Stores, eg, user annotations made during an experiment. The "
        "TimeSeries::data[] field stores a text array, and timestamps are stored for "
        "each annotation (ie, interval=1). This is largely an alias to a standard TimeSeries "
        "storing a text array but that is identifiable as storing annotations in a "
        "machine-readable way."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value":["TimeSeries","AnnotationSeries"],
                "const": True },
            "help?": {
                "data_type": "text",
                "value": "Time-stamped annotations about an experiment",
                "const": True}},
        "data": {
            "description": "Annotations made during an experiment.",
            "dimensions": ["num_times"],
            "data_type": "text",
            "attributes": {
				"conversion": {
					"description": "Value is float('NaN') (const) since this does not apply.",
					"value": "float('NaN')", "const": True},
				"resolution": {
					"description": "Value is float('nan') (const) since this does not apply",
					"value": "float('NaN')", "const": True},
				"unit": {
					"description": "Value is \"n/a\" to indicate that this does not apply", 
					"value": "n/a", "const": True}}},
    },
    "<IndexSeries>/": {
        "description": ("Stores indices to image frames stored in an ImageSeries. The purpose "
            "of the ImageIndexSeries is to allow a static image stack to be stored somewhere, "
            "and the images in the stack to be referenced out-of-order. This can be for the "
            "display of individual images, or of movie segments (as a movie is simply a "
            "series of images). The data field stores the index of the frame in the "
            "referenced ImageSeries, and the timestamps array indicates when that image "
            "was displayed."), 
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value":["TimeSeries","IndexSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("A sequence that is generated from an existing image stack. "
                    "Frames can be presented in an arbitrary order. The data[] field "
                    "stores frame number in reference stack"),
                "const": True}},
        "data": {
            "dimensions": ["num_times"],
            "data_type": "int",
            "description": "Index of the frame in the referenced ImageSeries.",
            "references": "indexed_timeseries/data.num_times"},
        "indexed_timeseries/": {
            "description": "HDF5 link to TimeSeries containing images that are indexed.",
            "link": {"target_type": "<ImageSeries>/", "allow_subclasses": False } },
        "indexed_timeseries_path": {
            "description": "Path to linked TimeSeries",
            "data_type": "text",
            "autogen": {
                "type": "link_path",
                "target":"indexed_timeseries/",
                "trim": False,
                "qty": "!",
                "format": "path is $t"}},
    },
    "<IntervalSeries>/": {
        "description": ("Stores intervals of data. The timestamps field stores the beginning "
            "and end of intervals. The data field stores whether the interval just started "
            "(>0 value) or ended (<0 value). Different interval types can be represented in "
            "the same series by using multiple key values (eg, 1 for feature A, 2 for feature "
            "B, 3 for feature C, etc). The field data stores an 8-bit integer. This is largely "
            "an alias of a standard TimeSeries but that is identifiable as representing time "
            "intervals in a machine-readable way."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value": ["TimeSeries","IntervalSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": "Stores the start and stop times for events",
                "const": True}},
        "data": {
            "description": (">0 if interval started, <0 if interval ended."),
            "dimensions": ["num_times"],
            "attributes": {
                "conversion": {
                    # "description": "Valus is float('nan') (const) since this does not apply.",
                    "value": "float('NaN')", "const": True},
                "resolution": {
                    # "description": "Value is float('nan') (const) since this does not apply",
                    "value": "float('NaN')", "const": True},
                "unit": {
                    # "description": "Value is \"n/a\" to indicate that this does not apply", 
                    "value": "n/a", "const": True}},
            "data_type": "int8"},
    },
    "<OptogeneticSeries>/": {
        "description": "Optogenetic stimulus.  The data[] field is in unit of watts.",
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value":["TimeSeries","OptogeneticSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": "Optogenetic stimulus",
                "const": True}},
        "data": {
            "description": "Applied power for optogenetic stimulus.",
            "dimensions": ["num_times"],
            "attributes": { "unit": { "data_type": "text", "value": "watt" }},
            "data_type": "float32"},
        "site": {
            "description": "Name of site description in general/optogentics.",
            "data_type": "text",
            "references": "/general/optogenetics/<site_X>/"}
    },
    "<RoiResponseSeries>/": {
        "description": ("ROI responses over an imaging plane. Each row in data[] should correspond to "
            "the signal from one ROI."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value": ["TimeSeries","RoiResponseSeries"],
                "const": True },
            "help?": {
                "data_type": "text",
                "value": ("ROI responses over an imaging plane. Each row in data[] should "
                    "correspond to the signal from one ROI"),
                "const": True}},
        "data": {
            "description": "Signals from ROIs",
            "dimensions": ["num_times", "num_ROIs"],
            "data_type": "float32"},
        "segmentation_interface/":  {
            "description": "HDF5 link to image segmentation module defining ROIs.",
            "link": {"target_type": "ImageSegmentation/", "allow_subclasses": False } },
        "segmentation_interface_path": {
            "description": "Path to segmentation module.",
            "data_type": "text",
            "autogen": {
                "type": "link_path",
                "target":"segmentation_interface/",
                "trim": False,
                "qty": "!",
                "format": "$t"}},
        "roi_names": {
            "description": "List of ROIs represented, one name for each row of data[].",
            "data_type": "text",
            "dimensions": ["num_ROIs",] }
    },
    "<SpatialSeries>/": {
        "description": ("Direction, e.g., of gaze or travel, or position. The "
            "TimeSeries::data field is a 2D array storing position or direction relative "
            "to some reference frame. Array structure: [num measurements] [num dimensions]. "
            "Each SpatialSeries has a text dataset reference_frame that indicates the "
            "zero-position, or the zero-axes for direction. For example, if representing "
            "gaze direction, \"straight-ahead\" might be a specific pixel on the monitor, "
            "or some other point in space. For position data, the 0,0 point might be the "
            "top-left corner of an enclosure, as viewed from the tracking camera. The unit "
            "of data will indicate how to interpret SpatialSeries values."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value":["TimeSeries","SpatialSeries"],
                "const": True },
             "help?": {
                "data_type": "text",
                "value": ("Stores points in space over time. The data[] array structure "
                    "is [num samples][num spatial dimensions]"),
                "const": True}},
        "reference_frame^": {
            "description": "Description defining what exactly 'straight-ahead' means.",
            "data_type": "text"},
        "data": {
            "description": "2-D array storing position or direction relative to some reference frame.",
            "dimensions": ["num_times", "num_features"],
            "attributes": { "unit": { "data_type": "text", "value": "meter" }},
            "data_type": "number"},
    }, 
    "<ElectricalSeries>/": {
        "description": ("Stores acquired voltage data from extracellular recordings. "
        "The data field of an ElectricalSeries is an int or float array storing data "
        "in Volts. "
        "TimeSeries::data array structure: :blue:`[num times] [num channels] "
        "(or [num_times] for single electrode).`"),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "const":True,
                "value": ["TimeSeries","ElectricalSeries"]},
             "help?": {
                "data_type": "text",
                "value": "Stores acquired voltage data from extracellular recordings",
                "const": True}},
        "data": {
            "description": "Recorded voltage data.",
            "dimensions": [   
                ["num_times"],                # for single electrode (2-d array)       
                ["num_times", "num_channels"]], # for multiple electrode (3-d array)
            "data_type": "number",
            "attributes": { "unit": { "data_type": "text", "value": "volt" }}},
        "electrode_idx": {
            "description": ("Indicies (zero-based) to electrodes in "
                "general/extracellular_ephys/electrode_map."),
            "dimensions": ["num_channels"],
            "data_type": "int32",
            "references": "/general/extracellular_ephys/electrode_map.num_electrodes",},     
    },
    "<SpikeEventSeries>/": {
        "description": ("Stores \"snapshots\" of spike events (i.e., threshold crossings) "
            "in data. This may also be raw data, as reported by ephys hardware. If so, the "
            "TimeSeries::description field should describing how events were detected. All "
            "SpikeEventSeries should reside in a module (under EventWaveform interface) "
            "even if the spikes were reported and stored by hardware. All events span the "
            "same recording channels and store snapshots of equal duration. "
            "TimeSeries::data array structure: :blue:`[num events] [num channels] [num samples] "
            "(or [num events] [num samples] for single electrode)`."),
        "merge": ["<ElectricalSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"],
                "value":["TimeSeries","ElectricalSeries","SpikeEventSeries"],
                "const": True},
             "help?": {
                "data_type": "text",
                "value": "Snapshots of spike events from data.",
                "const": True}},
        "data": {
            "description": "Spike waveforms.",
            "dimensions": [
                ["num_events", "num_samples"],                # for single electrode (2-d array)       
                ["num_events","num_channels","num_samples"]], # for multiple electrode (3-d array)
            "data_type": "float32",
            "attributes": { "unit": { "data_type": "text", "value": "volt" }}},
    },
    "<PatchClampSeries>/": {
        "description": ("Stores stimulus or response current or voltage. "
            "Superclass definition for patch-clamp data (this class "
            "should not be instantiated directly)."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value": ["TimeSeries","PatchClampSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Superclass definition for patch-clamp data"),
                "const": True}},
        "data": {
            "description": "Recorded voltage or current.",
            "dimensions": ["num_times"],
            "data_type": "number"},
        "electrode_name": {
            "description": "Name of electrode entry in /general/intracellular_ephys.",
            "data_type": "text",
            "references": "/general/intracellular_ephys/<electrode_X>/"},
        "gain^": {
            "description": "Units: Volt/Amp (v-clamp) or Volt/Volt (c-clamp)",
            "data_type": "float"},
    },
    "<VoltageClampStimulusSeries>/": {
        "description": ("Aliases to standard PatchClampSeries. Its functionality is to better"
            " tag PatchClampSeries for machine (and human) readability of the file."),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"],
                "value": ["TimeSeries","PatchClampSeries","VoltageClampStimulusSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Stimulus voltage applied during voltage clamp recording"),
                "const": True}},      
    },
    "<CurrentClampStimulusSeries>/": {
        "description": ("Aliases to standard PatchClampSeries. Its functionality is to better"
            " tag PatchClampSeries for machine (and human) readability of the file."),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"],
                "value": ["TimeSeries","PatchClampSeries","CurrentClampStimulusSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Stimulus current applied during current clamp recording"),
                "const": True}},            
    },
    "<VoltageClampSeries>/": {
        "description": ("Stores current data recorded from intracellular voltage-clamp"
            " recordings. A corresponding VoltageClampStimulusSeries (stored separately as a"
            " stimulus) is used to store the voltage injected."),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"],
                "value": ["TimeSeries","PatchClampSeries","VoltageClampSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Current recorded from cell during voltage-clamp recording"),
                "const": True}},
        "capacitance_fast^": {
            "attributes": { "unit": {"data_type": "text", "value": "Farad"}},
            "description": "Unit: Farad",
            "data_type": "float32"},
        "capacitance_slow^": {
            "attributes": { "unit": {"data_type": "text", "value": "Farad"}},
            "description": "Unit: Farad",
            "data_type": "float32"},
        "resistance_comp_bandwidth^": {
            "attributes": { "unit": {"data_type": "text", "value": "Hz"}},
            "description": "Unit: Hz",
            "data_type": "float32"},
        "resistance_comp_correction^": {
            "attributes": { "unit": {"data_type": "text", "value": "pecent"}},
            "description": "Unit: %",
            "data_type": "float32"},
        "resistance_comp_prediction^": {
            "attributes": { "unit": {"data_type": "text", "value": "pecent"}},
            "description": "Unit: %",
            "data_type": "float32"},
        "whole_cell_capacitance_comp^": {
            "attributes": { "unit": {"data_type": "text", "value": "Farad"}},
            "description": "Unit: Farad",
            "data_type": "float32"},
        "whole_cell_series_resistance_comp^": {
            "attributes": { "unit": {"data_type": "text", "value": "Ohm"}},
            "description": "Unit: Ohm",
            "data_type": "float32"}
    },
    "<CurrentClampSeries>/": {
        "description": ("Stores voltage data recorded from intracellular current-clamp recordings."
            " A corresponding CurrentClampStimulusSeries (stored separately as a stimulus) is used"
            " to store the current injected."),
        "merge": ["<PatchClampSeries>/", ],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"],
                "value": ["TimeSeries","PatchClampSeries","CurrentClampSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Voltage recorded from cell during current-clamp recording"),
                "const": True}},
        "bias_current^": {
            "description": "Unit: Amp",
            "data_type": "float32"},
        "bridge_balance^": {
            "description": "Unit: Ohm",
            "data_type": "float32"},
        "capacitance_compensation^": {
            "description": "Unit: Farad",
            "data_type": "float32"},
#         "resistance_compensation": {
#             "description": "Resistance compensation",
#             "data_type": "float",
#             "unit": "Ohms"},
    },
    "<IZeroClampSeries>/": {
        "description": ("Stores recorded voltage data from intracellular recordings "
            "when all current and amplifier settings are off (i.e., CurrentClampSeries "
            "fields will be zero). There is no CurrentClampStimulusSeries associated "
            "with an IZero series because the amplifier is disconnected and no stimulus "
            "can reach the cell."),
        "merge": [ "<CurrentClampSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["4"],
                "value": ["TimeSeries","PatchClampSeries","CurrentClampSeries","IZeroClampSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": ("Voltage from intracellular recordings "
                    "when all current and amplifier settings are off"),
                "const": True}} 
    },
    "<ImageSeries>/": {
        "description": ("General image data that is common between acquisition and "
        "stimulus time series. Sometimes the image data is stored in the HDF5 file in a "
        "raw format while other times it will be stored as an external image file in the "
        "host file system. The data field will either be binary data or empty. "
        "TimeSeries::data array structure: [frame] [y][x] or [frame][z][y][x]."),
        "merge": ["<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value":["TimeSeries","ImageSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": "Storage object for time-series 2-D image data",
                "const": True}},
        "_required": {
            "ext_data" :
                ["external_file XOR data",
                    "Either 'external_file' or 'data' must be specified, but not both"]},
        "data": {
            "description": "Either binary data containing image or empty.",
            "dimensions": [["x","y"], ["frame","y","x"], ["frame","z","y","x"]],
            "data_type": "number"},
        "format^": {
            "description": ("Format of image. If this is 'external' then the field external_file"
                " contains the path or URL information to that file. For tiff, png, jpg, etc,"
                " the binary representation of the image is stored in data. If the format is"
                " raw then the fields bit_per_pixel and dimension are used. For raw images,"
                " only a single channel is stored (eg, red)."),
            "data_type": "text"},
        "external_file?": {
            "description": ("Path or URL to one or more external file(s). Field only present if "
                "format=external. "
                "NOTE: this is only relevant if the image is stored in the file system as one or "
                "more image file(s). This field should NOT be used if the image is stored in "
                "another HDF5 file and that file is HDF5 linked to this file."),
            "data_type": "text",
            "dimensions": ["num_files"],
            "attributes": {
                "starting_frame": {
                    "data_type": "int",
                    "dimensions": ["num_files"],
                    "description": ("Each entry is the frame number (within the full ImageSeries) "
                        "of the first frame in the corresponding external_file entry. This serves "
                        "as an index to what frames each file contains, allowing random access."
                        "Zero-based indexing is used.  (The first element will always be zero).")}}},
        "bits_per_pixel^": {
            "description": "Number of bit per image pixel.",
            "data_type": "int32",},
        "dimension^": {
            "description": "Number of pixels on x, y, (and z) axes.",
            "data_type": "int32",
            "dimensions": ["rank"]},       
    },
    "<ImageMaskSeries>/": {
        "description": ("An alpha mask that is applied to a presented visual stimulus. The "
            "data[] array contains an array of mask values that are applied to the displayed "
            "image. Mask values are stored as RGBA. Mask can vary with time. The timestamps "
            "array indicates the starting time of a mask, and that mask pattern continues "
            "until it's explicitly changed."),
        "merge": ["<ImageSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"], 
                "value":["TimeSeries","ImageSeries","ImageMaskSeries"],
                "const": True},
            "help?": {
                "data_type": "text",
                "value": "An alpha mask that is applied to a presented visual stimulus",
                "const": True}},
        "masked_imageseries/": {
            "description": "Link to ImageSeries that mask is applied to.",
            "link": {"target_type": "<ImageSeries>/", "allow_subclasses": False } },
        "masked_imageseries_path": {
            "description": "Path to linked ImageSeries",
            "data_type": "text",
            "autogen": {
                "type": "link_path",
                "target":"masked_imageseries/",
                "trim": False,
                "qty": "!",
                "format": "path is $t"}},
    },    
    "<TwoPhotonSeries>/": {
        "description": "A special case of optical imaging.",
        "attributes": {
            "ancestry": {
                "data_type":"text",
                "dimensions": ["3"],
                "value": ["TimeSeries","ImageSeries","TwoPhotonSeries"],
                "const": True},
            "help?": {
                "data_type":"text",
                "value":"Image stack recorded from 2-photon microscope",
                "const": True }},
        "merge": ["<ImageSeries>/",],
        "pmt_gain^": {
            "description": "Photomultiplier gain",
            "data_type": "float32"},
        "field_of_view^": {
            "description": "Width, height and depth of image, or imaged area (meters).",
            "data_type": "float32",
            "dimensions": ["whd", ],
            "whd": {
                "type": "struct", 
                "components": [
                    { "alias": "width", "unit": "meter" },
                    { "alias": "height", "unit": "meter" },
                    { "alias": "depth", "unit": "meter" } ] } },
        "imaging_plane": {
            "description": "Name of imaging plane description in /general/optophysiology.",
            "data_type": "text",
            "references": "/general/optophysiology/<imaging_plane_X>"},
        "scan_line_rate^": {
            "description": ("Lines imaged per second. This is also stored in /general/optophysiology "
                "but is kept here as it is useful information for analysis, and so good to be stored "
                "w/ the actual data."),
            "data_type": "float32"},
    },
    "<OpticalSeries>/": {
        "description": ("Image data that is presented or recorded. A stimulus template movie "
            "will be stored only as an image. When the image is presented as stimulus, "
            "additional data is required, such as field of view (eg, how much of the visual "
            "field the image covers, or how what is the area of the target being imaged). "
            "If the OpticalSeries represents acquired imaging data, orientation is also "
            "important."),
        "attributes": {
            "ancestry": {
                "data_type":"text",
                "dimensions": ["3"],
                "value":["TimeSeries","ImageSeries","OpticalSeries"],
                "const": True},
            "help?": {
                "data_type":"text",
                "value":"Time-series image stack for optical recording or stimulus",
                "const": True}},
        "merge": ["<ImageSeries>/", ],
        "field_of_view^": {
            "description": "Width, height and depto of image, or imaged area (meters).",
            "data_type": "float32",
            "dimensions" : ["fov",],
            "fov" : {  # definition of dimension fov
                "type": "structure", 
                "components": [
                    [ 
                        { "alias": "width", "unit": "meter" },
                        { "alias": "height", "unit": "meter" }
                    ],
                    [
                        { "alias": "width", "unit": "meter" },
                        { "alias": "height", "unit": "meter" },
                        { "alias": "depth", "unit": "meter" }
                    ] 
                ]
            }
        },
        "distance^": {
            "description": "Distance from camera/monitor to target/eye.",
            "data_type": "float32"},
        "orientation^": {
            "description": ("Description of image relative to some reference frame (e.g.,"
                " which way is up). Must also specify frame of reference." ),
            "data_type": "text"}
    },
    "<Interface>/": {
        "description": ("The attributes specified here are "
            "included in all interfaces."),
        "attributes": {
            "neurodata_type": {"data_type": "text", "value": "Interface" },
            "source": {
                "data_type": "text",
                "description": "Path to the origin of the data represented in this interface.",
                "references": "/"},
            "help?": {
                "data_type": "text",
                "description": "Short description of what this type of Interface contains."}},
        "_properties": {
            # indicate that this group is abstract, i.e. must be subclassed via 'merge'
            "abstract": True
        }
    },
    "BehavioralEvents/": {
        "merge": ["<Interface>/", ],
        "description": ("TimeSeries for storing behavioral events. "
            "See description of <a href=\"#BehavioralEpochs\">BehavioralEpochs</a> "
            "for more details."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":"Position data, whether along the x, xy or xyz axis",
                "const": True}},
        "include": {"<TimeSeries>/*": {}, },
    },
    "BehavioralEpochs/": {
        "merge": ["<Interface>/", ],
        "description": ("TimeSeries for storing behavoioral epochs.  The "
        "objective of this and the other two Behavioral interfaces "
        "(e.g. BehavioralEvents and BehavioralTimeSeries) is to provide generic "
        "hooks for software tools/scripts. This allows a tool/script to take the "
        "output one specific "
        "interface (e.g., UnitTimes) and plot that data relative to another data "
        "modality (e.g., behavioral events) without having to define all possible "
        "modalities in advance. Declaring one of these interfaces means that one or "
        "more TimeSeries of the specified type is published. These TimeSeries should "
        "reside in a group having the same name as the interface. For example, if a "
        "BehavioralTimeSeries interface is declared, the module will have one or more "
        "TimeSeries defined in the module sub-group \"BehavioralTimeSeries\". "
        "BehavioralEpochs should use IntervalSeries. BehavioralEvents is used for "
        "irregular events. BehavioralTimeSeries is for continuous data."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":"General container for storing behavorial epochs",
                "const": True}},
        "include": {"<IntervalSeries>/*": {}},
    },
    "BehavioralTimeSeries/": {
        "merge": ["<Interface>/", ],
        "description": ("TimeSeries for storing Behavoioral time series data."
            "See description of <a href=\"#BehavioralEpochs\">BehavioralEpochs</a> "
            "for more details.") ,
        "include": {"<TimeSeries>/*": {}},
    },   
    "Clustering/": {
        "merge": ["<Interface>/", ],
        "_description": ("Clustered spike data, whether from automatic clustering tools "
            "(e.g., klustakwik) or as a result of manual sorting."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":("Clustered spike data, whether from automatic clustering tools "
                    "(eg, klustakwik) or as a result of manual sorting"),
                "const": True}},
        "times": {
            "description": ("Times of clustered events, in seconds. This may be a link to "
                "times field in associated FeatureExtraction module."),
            "dimensions": ["num_events"],
            "data_type": "float64!"},
        "num": {
            "description": "Cluster number of each event",
            "dimensions": ["num_events"],
            "data_type": "int32"},
        "description": {
            "data_type": "text",
            "description": ("Description of clusters or clustering, (e.g. cluster 0 is noise, "
                "clusters curated using Klusters, etc)")},   
        "cluster_nums": {
            "description": ("List of cluster number that are a part of this set (cluster "
                "numbers can be non- continuous)"),
            "data_type": "int32",
            "dimensions": ["num_clusters"],
            "autogen": {
                "type": "values",
                    "target":"num",
                    # "trim": True,
                    "qty": "*",
                    "include_empty": True}
           },
        "peak_over_rms": {
            "description": ("Maximum ratio of waveform peak to RMS on any channel in the cluster "
                "(provides a basic clustering metric)."),
            "data_type": "float32",
            "dimensions": ["num_clusters"]}     
    },
    "ClusterWaveforms/": {
        "merge": ["<Interface>/", ],
        "description": ("The mean waveform shape, including standard deviation, of the different "
            "clusters. Ideally, the waveform analysis should be performed on data that is only "
            "high-pass filtered. This is a separate module because it is expected to require "
            "updating. For example, IMEC probes may require different storage requirements to "
            "store/display mean waveforms, requiring a new interface or an extension of this one."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":("Mean waveform shape of clusters. Waveforms should be high-pass "
                    "filtered (ie, not the same bandpass filter used waveform analysis and "
                    "clustering)"),
                "const": True}},
        "waveform_mean": {
            "description": ("The mean waveform for each cluster, using the same indices for each "
                "wave as cluster numbers in the associated Clustering module (i.e, cluster 3 is "
                "in array slot [3]). Waveforms corresponding to gaps in cluster sequence should "
                "be empty (e.g., zero- filled)"),
            "data_type": "float32",
            "dimensions": ["num_clusters", "num_samples"]},
        "waveform_sd": {
            "description": "Stdev of waveforms for each cluster, using the same indices as in mean",
            "data_type": "float32",
            "dimensions": ["num_clusters", "num_samples"]},
        "waveform_filtering": {
            "description":  "Filtering applied to data before generating mean/sd",
            "data_type": "text"},
        "clustering_interface/": {
            "description":  ("HDF5 link to Clustering interface that was the source of "
                "the clustered data"),
            "link": {"target_type": "Clustering/", "allow_subclasses": False } },
        "clustering_interface_path": {
            "description":  "Path to linked clustering interface",
            "data_type": "text",
            "autogen": {
                "type": "link_path",
                "target":"clustering_interface/",
                "trim": False,
                "qty": "!",
                "format": "path is $t"}},
    },       
    "CompassDirection/": {
        "merge": ["<Interface>/", ],
        "description": ("With a CompassDirection interface, a module publishes a SpatialSeries "
            "object representing a floating point value for theta. The SpatialSeries::reference_frame "
            "field should indicate what direction corresponds to ""0"" and which is the direction "
            "of rotation (this should be ""clockwise""). The si_unit for the SpatialSeries should "
            "be ""radians"" or ""degrees""."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":("Direction as measured radially. Spatial series reference frame should "
                "indicate which direction corresponds to zero and what is the direction of positive "
                "rotation"),
                "const": True}},
        "include": {"<SpatialSeries>/*": {} }, # One of possibly many SpatialSeries storing direction. Name should be informative
    },
    "DfOverF/": {
        "merge": ["<Interface>/", ],
        "description": ("dF/F information about a region of interest (ROI). Storage hierarchy"
            " of dF/F should be the same as for segmentation (ie, same names for ROIs and for"
            " image planes)."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":("Df/f over time of one or more ROIs. TimeSeries names should correspond "
                    "to imaging plane names"),
                "const": True}},
        "include": {"<RoiResponseSeries>/*": {} }, # One of possibly many RoiResponseSeries, one for each 
            #imaging plane. Name should match entry in /general/optophysiology
    },
    "EventDetection/": {
        "merge": ["<Interface>/", ],
        "description": "Detected spike events from voltage trace(s).",
        "times": {
            "description": "Timestamps of events, in Seconds",
            "dimensions": ["num_events"],
            "data_type": "float64!"},
        "detection_method": {
            "description": ("Description of how events were detected, such as voltage"
                    " threshold, or dV/dT threshold, as well as relevant values."),
            "data_type": "text"},                 
        "source_idx": {
            "description": ("Indices (zero-based) into source ElectricalSeries::data array "
                "corresponding to time of event. Module description should define what is "
                "meant by time of event (e.g., .25msec before action potential peak, "
                "zero-crossing time, etc). The index points to each event from the raw data"),
            "dimensions": ["num_events"],
            "data_type": "int32",
            "references": "source_electrical_series/data.num_times"},
        "source_electricalseries/": {
            "description": ("HDF5 link to ElectricalSeries that this data was calculated from. "
                "Metadata about electrodes and their position can be read from that "
                "ElectricalSeries so it's not necessary to mandate that information be "
                "stored here"),
            "link": {"target_type": "<ElectricalSeries>/", "allow_subclasses": False } },
        "source_electricalseries_path": {
            "description": "Path to linked ElectricalSeries.",
            "data_type": "text",
            "autogen": {
                "type": "link_path",
                "target": "source_electricalseries/",
                "trim": False,
                "qty": "!",
                "format": "path is $t"}},
        },
    "EventWaveform/" : {
        "merge": ["<Interface>/", ],
        "description": ("Represents either the waveforms of detected events, as extracted from a raw data "
            "trace in /acquisition, or the event waveforms that were stored during experiment acquisition."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":("Waveform of detected extracellularly recorded spike events"),
                "const": True}},
        "include": {"<SpikeEventSeries>/*": {} },
    },
    "EyeTracking/" : {
        "merge": ["<Interface>/", ],
        "description": "Eye-tracking data, representing direction of gaze.",
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Eye-tracking data, representing direction of gaze"),
                "const": True}},
        "include": {"<SpatialSeries>/*": {} },
    },
    "FeatureExtraction/" : {
        "merge": ["<Interface>/", ],
        "_description": ("Features, such as PC1 and PC2, that are extracted from signals stored "
            "in a SpikeEvent TimeSeries or other source."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Container for salient features of detected events"),
                "const": True}},
        "features": {
            "description": "Multi-dimensional array of features extracted from each event.",
            "dimensions": ["num_events", "num_channels", "num_features"],
            "data_type": "float32"},
        "times": {
            "description": "Times of events that features correspond to (can be a link).",
            "dimensions": ["num_events"],
            "data_type": "float64!"},
        "description": {
            "description": "Description of features (eg, \"PC1\") for each of the extracted features.",
            "dimensions": ["num_features"],
            "data_type": "text"},    
        "electrode_idx": {
            "description": ("Indices (zero-based) to electrodes described in the experiment's "
                "electrode map array (under /general/extracellular_ephys)."),
            "dimensions": ["num_channels"],
            "data_type": "int32",
            "references": "/general/extracellular_ephys/electrode_map.num_electrodes"},
    },
    "FilteredEphys/" : {
        "merge": ["<Interface>/", ],
        "description": ("Ephys data from one or more channels that has been subjected to filtering. "
            "Examples of filtered data include Theta and Gamma (LFP has its own interface). FilteredEphys "
            "modules publish an ElectricalSeries for each filtered channel or set of channels. The name of "
            "each ElectricalSeries is arbitrary but should be informative. The source of the filtered data, "
            "whether this is from analysis of another time series or as acquired by hardware, should be noted "
            "in each's TimeSeries::description field. There is no assumed 1::1 correspondence between filtered "
            "ephys signals and electrodes, as a single signal can apply to many nearby electrodes, and one "
            "electrode may have different filtered (e.g., theta and/or gamma) signals represented."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Ephys data from one or more channels that is subjected to filtering, such as "
                    "for gamma or theta oscillations (LFP has its own interface). Filter properties should "
                    "be noted in the ElectricalSeries"),
                "const": True}},
        "include": {"<ElectricalSeries>/+": {} },
    },
    "Fluorescence/" : {
        "merge": ["<Interface>/", ],
        "description": ("Fluorescence information about a region of interest (ROI). Storage hierarchy of "
            "fluorescence should be the same as for segmentation (ie, same names for ROIs and for image "
            "planes)."), 
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Fluorescence over time of one or more ROIs. TimeSeries names should correspond "
                    "to imaging plane names"),
                "const": True}},
        "include": {"<RoiResponseSeries>/+": {} }
    },
    "ImageSegmentation/" : {
        "merge": ["<Interface>/", ],
        "description": ("Stores pixels in an image that represent different regions of interest (ROIs) or "
            "masks. All segmentation for a given imaging plane is stored together, with storage for "
            "multiple imaging planes (masks) supported. Each ROI is stored in its own subgroup, with the "
            "ROI group containing both a 2D mask and a list of pixels that make up this mask. Segments can "
            "also be used for masking neuropil. If segmentation is allowed to change with time, a new "
            "imaging plane (or module) is required and ROI names should remain consistent between them."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Stores groups of pixels that define regions of interest from one or more "
                    "imaging planes",),
                "const": True}},
        "<image_plane>/*" : {
            "_description": "Group name is human-readable description of imaging plane",
            "description^": {
                "data_type": "text",
                "description": "Description of image plane, recording wavelength, depth, etc"},
            "imaging_plane_name": {
                "data_type": "text",
                "description": "Name of imaging plane under general/optophysiology"},
            "roi_list": {
                "description": "List of ROIs in this imaging plane",
                "data_type": "text",
                "dimensions": ["num_rois"],
                "references": "<roi_name>/",
                "autogen": {
				    "type": "names",
				    "target":"<roi_name>",
				    "trim": True,
				    # "tsig": {"type": "group"}, # would be good to require member "times" data set.
				    "qty": "*"}},
            "<roi_name>/*": {
                "description": "Name of ROI",
                "img_mask": {
                    "description": "ROI mask, represented in 2D ([y][x]) intensity image",
                    "data_type": "float32",
                    "dimensions": ["num_x","num_y"]},
                "pix_mask": {
                    "description": "List of pixels (x,y) that compose the mask",
                    "data_type": "uint16",
                    "dimensions": ["num_pixels", "2"]},
                "pix_mask_weight": {
                    "description": "Weight of each pixel listed in pix_mask",
                    "data_type": "float32",
                    "dimensions": ["num_pixels"]},
                "roi_description": {
                    "description": "Description of this ROI.",
                    "data_type": "text" }},
#                 "start_time_0": {
#                     "description": "Time when the mask starts to be used",
#                     "data_type": "number" },  # should be changed to float.
            "reference_images/": {
                "description": "Stores image stacks segmentation mask apply to.",
                "<image_name>/+": {
                    "description": ("One or more image stacks that the masks apply "
                        "to (can be one-element stack)"),
                    "merge": ["<ImageSeries>/",] }}
        },
    },
    "ImagingRetinotopy/": {
        "merge": ["<Interface>/", ],
        "description": (
            "Intrinsic signal optical imaging or widefield imaging for measuring "
            "retinotopy. Stores orthogonal maps (e.g., altitude/azimuth; radius/theta) of responses "
            "to specific stimuli and a combined polarity map from which to identify visual areas.<br />"
            "Note: for data consistency, all images and arrays are stored in the format [row][column] "
            "and [row, col], which equates to [y][x]. Field of view and dimension arrays may appear "
            "backward (i.e., y before x)."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Intrinsic signal optical imaging or Widefield imaging for measuring retinotopy"),
                "const": True}},
        "axis_descriptions": {
            "description": ("Two-element array describing the contents of the two response axis "
                "fields. Description should be something like ['altitude', 'azimuth'] or "
                "'['radius', 'theta']"),
            "data_type": "text",
            "dimensions": ["2",]},
        "axis_1_phase_map": {
            "description": "Phase response to stimulus on the first measured axis",
            "data_type": "float32",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "unit": {
                    "data_type": "text",
                    "description": "Unit that axis data is stored in (e.g., degrees)"},
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col",],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "field_of_view": {
                    "data_type": "float",
                    "dimensions": ["row_col",],
                    "description": "Size of viewing area, in meters",
                    "row_col" : {  # definition of dimension row_col
                        "type": "structure", 
                        "components": [
                            { "alias": "row", "unit": "meter"},
                            { "alias": "column", "unit": "meter" } ]}}}},
        "axis_1_power_map^": {
            "description": ("Power response on the first measured axis. Response is scaled so "
                "0.0 is no power in the response and 1.0 is maximum relative power."),
            "data_type": "float32",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "unit": {
                    "data_type": "text",
                    "description": "Unit that axis data is stored in (e.g., degrees)"},
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col"],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "field_of_view^": {
                    "data_type": "float",
                    "dimensions": ["row_col"],
                    "description": "Size of viewing area, in meters"}}},
        "axis_2_phase_map": {
            "description": "Phase response to stimulus on the second measured axis",
            "data_type": "float32",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "unit": {
                    "data_type": "text",
                    "description": "Unit that axis data is stored in (e.g., degrees)"},
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col",],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "field_of_view": {
                    "data_type": "float",
                    "dimensions": ["row_col",],
                    "description": "Size of viewing area, in meters"}}},
        "axis_2_power_map^": {
            "description": ("Power response on the second measured axis. Response is scaled so "
                "0.0 is no power in the response and 1.0 is maximum relative power."),
            "data_type": "float32",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "unit": {
                    "data_type": "text",
                    "description": "Unit that axis data is stored in (e.g., degrees)"},
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col",],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "field_of_view^": {
                    "data_type": "float",
                    "dimensions": ["row_col",],
                    "description": "Size of viewing area, in meters"}}},
        "sign_map": {
            "description": ("Sine of the angle between the direction of the gradient in "
                "axis_1 and axis_2"),
            "data_type": "float32",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col",],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "field_of_view^": {
                    "data_type": "float",
                    "dimensions": ["row_col",],
                    "description": "Size of viewing area, in meters."}}},
        "vasculature_image": {
            "description": ("Gray-scale anatomical image of cortical surface. Array structure: "
                "[rows][columns]"),
            "data_type": "uint16",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "format": {
                    "data_type": "text",
                    "description": "Format of image. Right now only 'raw' supported"},
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col",],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "field_of_view^": {
                    "data_type": "float",
                    "dimensions": ["row_col",],
                    "description": "Size of viewing area, in meters"},
                "bits_per_pixel": {
                    "data_type": "int32",
                    "description": ("Number of bits used to represent each value. This is "
                        "necessary to determine maximum (white) pixel value")}}},
        "focal_depth_image": {
            "description": ("Gray-scale image taken with same settings/parameters (e.g., "
                "focal depth, wavelength) as data collection. Array format: [rows][columns]"),
            "data_type": "uint16",
            "dimensions": ["num_rows", "num_cols"],
            "attributes": {
                "format": {
                    "data_type": "text",
                    "description": "Format of image. Right now only 'raw' supported"},
                "dimension": {
                    "data_type": "int32",
                    "dimensions": ["row_col",],
                    "description": ("Number of rows and columns in the image. NOTE: row, column "
                        "representation is equivalent to height,width.")},
                "bits_per_pixel": {
                    "data_type": "int32",
                    "description": ("Number of bits used to represent each value. This is "
                        "necessary to determine maximum (white) pixel value")},
                "focal_depth^": {
                    "data_type": "float",
                    "description": "Focal depth offset, in meters"},
                "field_of_view^": {
                    "data_type": "float",
                    "dimensions": ["row_col",],
                    "description": "Size of viewing area, in meters"}}}                    
    },
    "LFP/": {
        "merge": ["<Interface>/", ],
        "description": ("LFP data from one or more channels. The electrode map in each published "
            "ElectricalSeries will identify which channels are providing LFP data. Filter properties "
            "should be noted in the ElectricalSeries description or comments field."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("LFP data from one or more channels. Filter properties should be "
                    "noted in the ElectricalSeries"),
                "const": True}},
        "include": {"<ElectricalSeries>/+": {}, },
    },
    "MotionCorrection/": {
        "merge": ["<Interface>/", ],
        "description": ("An image stack where all frames are shifted (registered) to a common coordinate "
            "system, to account for movement and drift between frames. "
            "Note: each frame at each point in time is assumed to be 2-D (has only x & y dimensions)."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Image stacks whose frames have been shifted (registered) to account for motion"),
                "const": True}},
        "<image stack name>/+": {
            "description": "One of possibly many.  Name should be informative.",
            "original/": {
                "description": "HDF5 Link to image series that is being registered.",
                "link": {"target_type": "<ImageSeries>/", "allow_subclasses": True } },
            "original_path": {
                "description":  "Path to linked original timeseries",
                "data_type": "text",
                "autogen": {
                    "type": "link_path",
                    "target":"original/",
                    "trim": False,
                    "qty": "!",
                    "format": "$t"}},
            "xy_translation/": {
                "description": ("Stores the x,y delta necessary to align each frame to"
                    " the common coordinates, for example, to align each frame to a"
                    " reference image."),
                #{ "include": {"<TimeSeries>/*": {} } },
                "merge": ["<TimeSeries>/",],
                "data": {
                    "description": ("TimeSeries for storing x,y offset for each "
                        "image frame."),
                    "dimensions": ["num_times", "xy"], # specifies 2-d array
                    "data_type": "float",
                    "xy" : {  # definition of dimension xy
                        "type": "structure", 
                        "components": [
                            { "alias": "x", "unit": "pixels" },
                            { "alias": "y", "unit": "pixels" } ],
                    }
                }
            },
            "corrected/": {
                "description": "Image stack with frames shifted to the common coordinates.",
                #{ "include": {"<ImageSeries>/*": {} } }
                "merge": ["<ImageSeries>/", ]
            }
        },
    },
    "Position/": {
        "merge": ["<Interface>/", ],
        "description": "Position data, whether along the x, x/y or x/y/z axis.",
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":"Position data, whether along the x, xy or xyz axis",
                "const": True}},
        "include": {"<SpatialSeries>/+": {} },
    },
    "PupilTracking/": {
        "merge": ["<Interface>/", ],
        "description": "Eye-tracking data, representing pupil size.",
        "attributes": {
            "help?": {
                "data_type":"text",
                "value":"Eye-tracking data, representing pupil size",
                "const": True}},
        "include": {"<TimeSeries>/+": {}, },
    },
    "UnitTimes/": {
        "merge": ["<Interface>/", ],
        "description": ("Event times of observed units (e.g. cell, synapse, etc.). "
            "The UnitTimes group contains a group for each unit. The name of the group should match "
            "the value in the source module, if that is possible/relevant (e.g., name of ROIs from "
            "Segmentation module)."),
        "attributes": {
            "help?": {
                "data_type":"text",
                "value": ("Estimated spike times from a single unit"),
                "const": True}},
        "unit_list": {
            "description": "List of units present.",
            "data_type": "text",
            "dimensions": ["num_units"],
            "autogen": {
				"type": "names",
				"target":"<unit_N>",
				"trim": True,
				# "tsig": {"type": "group"}, # would be good to require member "times" data set.
				"qty": "*"},
            "references": "<unit_N>/"},  # 1-to-1 is relationship type. To be implemented.
        "<unit_N>/+": {
            "description": "Group storing times for &lt;unit_N&gt;.",
            "times": {
                "description": "Spike time for the units (exact or estimated)",
                "dimensions": ["num_events"],
                "data_type": "float64!",
                },
            "source^": {
                "description": ("Name, path or description of where unit times originated. This "
                    "is necessary only if the info here differs from or is more fine-grained than "
                    "the interface's source field"),
                "data_type": "text"},
            "unit_description": {
                "description": "Description of the unit (eg, cell type).",
                "data_type": "text"},
        }
    },
},

# documentation about format.  These are in an array
"doc": [
    {
        "id": "Introduction",
        "description": "Introduction section.",
        "location": {"id":"_toc_top", "position": "after"},
        "level": 0,
        "content": """
    <p style="margin-bottom: 0in">Neurodata Without Borders:
      Neurophysiology is a project to develop a unified data format for
      cellular-based neurophysiology data, focused on the dynamics of
      groups of neurons measured under a large range of experimental
      conditions. Participating labs provided use cases and critical
      feedback to the effort. The design goals for the NWB format included:</p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in"><b>Compatibility</b></p>
    <ul>
      <li>
        <p style="margin-bottom: 0in">Cross-platform</p>
      </li>
      <li>
        <p style="margin-bottom: 0in">Support for tool makers</p>
      </li>
    </ul>
    <p style="margin-bottom: 0in"><b>Usability</b></p>
    <ul>
      <li>
        <p style="margin-bottom: 0in">Quickly develop a basic understanding of
          an experiment and its data</p>
      </li>
      <li>
        <p style="margin-bottom: 0in">Review an experiment's details without
          programming knowledge</p>
      </li>
    </ul>
    <p style="margin-bottom: 0in"><b>Flexibility</b></p>
    <ul>
      <li>
        <p style="margin-bottom: 0in">Accommodate an experiment's raw and
          processed data</p>
      </li>
      <li>
        <p style="margin-bottom: 0in">Encapsulate all of an experiment's data,
          or link to external data source when necessary</p>
      </li>
    </ul>
    <p style="margin-bottom: 0in"><b>Extensibility</b></p>
    <ul>
      <li>
        <p style="margin-bottom: 0in">Accommodate future experimental paradigms
          without sacrificing backwards compatibility.</p>
      </li>
      <li>
        <p style="margin-bottom: 0in">Support custom extensions when the
          standard is lacking</p>
      </li>
    </ul>
    <p style="margin-bottom: 0in"><b>Longevity</b></p>
    <ul>
      <li>
        <p style="margin-bottom: 0in">Data published in the format should be
          accessible for decades</p>
      </li>
    </ul>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in"><a href="https://www.hdfgroup.org/HDF5/"><font
          color="#0000ff"><u>Hierarchical
            Data Format (HDF)</u></font></a> was selected for the NWB format
      because it met several of the project's requirements. First, it is
      a mature data format standard with libraries available in multiple
      programming languages. Second, the format's hierarchical structure
      allows data to be grouped into logical self-documenting sections. Its
      structure is analogous to a file system in which its "groups" and
      "datasets" correspond to directories and files. Groups and
      datasets can have attributes that provide additional details, such as
      authorities' identifiers. Third, its linking feature enables data
      stored in one location to be transparently accessed from multiple
      locations in the hierarchy. The linked data can be external to the
      file. Fourth, 
      <a href="https://www.hdfgroup.org/products/java/hdfview/">HDFView</a>,
      a free, cross-platform application, can be used to open a file and
      browse data. Finally, ensuring the ongoing accessibility of
      HDF-stored data is the mission of The HDF Group, the nonprofit that
      is the steward of the technology.</p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in">The NWB format standard is codified in
      a schema file written in a specification language created for this
      project. The specification language describes the schema, including
      data types and associations. A new schema file will be published for
      each revision of the NWB format standard. Data publishers can use the
      specification language to extend the format in order to store types
      of data not managed by the base format.
      </p>      
    """
    },
    {
        "id": "Naming conventions",
        "location": {"id":"Introduction", "position": "after"},
        "level": 1,
        "content": """
        <p>
        In this document (and in the specification language used to define
        the format) an identifier enclosed in angle brackets (e.g. 
        "<i>&lt;ElectricalSeries&gt;</i>")
        denotes a group or dataset with a "variable" name. That is, the name
        within the HDF5 file is set by the application
        creating the file and multiple instances may be created within the same
        group (each having a unique name).
        Identifiers that are not enclosed in angle brackets 
        (e.g. "<i>CompassDirection</i>") are
        the actual name of the group or dataset within the HDF5 file.
        There can only be one instance within a given group since the name is fixed.
        </p>
        """
    },
    {
        "id": "Link types",
        "location": {"id":"Naming conventions", "position": "after"},
        "level": 1,
        "content": """
        <p>
        In some instances, the specification refers to HDF5 links.  When links are
        made within the file, HDF5 soft-links (and not hard-links) should be used.  This
        is because soft-links distinguish between the link and the target of the link,
        whereas hard-links cause multiple names (paths) to be created for the
        target, and there is no way to determine which of these names are preferable
        in a given situation.  If the target of a soft link
        is removed (or moved to another location in the HDF5 file)&mdash;both of
        which can be done using the HDF5 API&mdash;then the soft link will "dangle," that
        is point to a target that no longer exists.  For this reason, moving or removing
        targets of soft links should be avoided unless the links are updated to point
        to the new location.
        """
    },
    {
        "id": "Automatically created components",
        "location": {"id":"Link types", "position": "after"},
        "level": 1,
        "content": """
        <p>
        In the format, the value of some datasets and attributes can usually be determined
        automatically from other parts of the HDF5 file.  For example, a dataset that
        has as value the target of a link can be determined automatically from a list
        of links in the HDF5 file.  When possible, the NWB API will automatically create
        such components and required groups.  The components (datasets, attributes and
        required groups) that are automatically created by the API are
        indicated by the phrase <em>(Automatically
        created)</em> in the description or comment.  The creation of these components is
        specified by the "autogen" option in the format specification language.  This is
        not a part of the format (different API's may create the data files in
        different ways).  The information is included for the convenience of those using
        the NWB API and also for developers of other APIs who may wish to also auto-generate
        these components.</p>
        """
    },
    {
        "id": "top_level_groups_post",
        "description": "Content under table of top level groups",
        "location": {"id":"Top level groups", "position": "post"},
        "content": """
      <br />
      <p style="margin-bottom: 0in">The content of these organizational
      groups is more fully described in the section titled,
      <a href="#File_organization">File organization</a>. 
      The NWB format is
      based on <i><a href="#TimeSeries">TimeSeries</a></i>
      and <i><a href="#Modules">Modules</a></i> and these are defined first. </p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in">NWB stores general optical and
      electrical physiology data in a way that should be understandable to
      a naive user after a few minutes using looking at the file in an HDF5
      browser, such as HDFView. The format is designed to be friendly to
      and usable by software tools and analysis scripts, and to impose few
      a priori assumptions about data representation and analysis. Metadata
      required to understand the data itself (core metadata) is generally
      stored with the data. Information required to interpret the
      experiment (general metadata) is stored in the group 'general'. Most
      general metadata is stored in free-form text fields. Machine-readable
      metadata is stored as attributes on these free-form text fields.</p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in">The only API assumed necessary to read
      a NWB file is an HDF5 library (e.g., h5py in python, libhdf5 in C,
      JHI5 in Java).</p>
    """
    },
    {
        "id": "top_level_datasets_mid",
        "description": "Text place after header for top-level datasets but before table",
        "location": {"id": "Top level datasets", "position": "mid"},
        "content": """
    <p style="margin-bottom: 0in; page-break-after: avoid">Top-level
      datasets are for file identification and version information.</p>
        """
    },
    {
        "id": "top_level_datasets_post",
        "description": "Text place after table for top-level datasets",
        "location": {"id": "Top level datasets", "position": "post"},
        "content": """
    <p style="margin-bottom: 0in"><br>
    </p><p>
    All times are stored in seconds using double precision (64 bit) floating
    point values.  A smaller floating point value, e.g. 32 bit, is <b>not</b> permitted
    for storing times.
    This is because significant errors for time can result from using smaller data sizes.
    Throughout this document, sizes (number of bits) are provided
    for many datatypes (e.g. float32).
    If the size is followed by "!" then the size is the
    minimum size, otherwise it is the recommended size.  For fields with a
    recommended size, larger or smaller sizes can be used (and for integer types both signed and
    unsigned), so long as the selected size encompasses the full range of
    data, and for floats, without loss of significant precision.  Fields that have
    a minimum size can use larger, but not smaller sizes.
    </p>       
        """
    },
    {
        "id": "TimeSeries",
        "description": "Text place before <TimeSeries>/, included in table of contents",
        "location": {"id": "<TimeSeries>", "position": "before"},
        "level": 0,
        "content": """
   <p style="margin-bottom: 0in; page-break-after: avoid">The file
      format is designed around a data structure called a <i>TimeSeries</i>
      which stores time-varying data. A <i>TimeSeries</i> is a superset of
      several INCF types, including signal events, image stacks and
      experimental events. To account for different storage requirements
      and different modalities, a <i>TimeSeries</i> is defined in a minimal
      form and it can be extended, or subclassed, to account for different
      modalities and data storage requirements. When a <i>TimeSeries</i> is
      extended, it means that the 'subclassed' instance maintains
      or changes each of
      the components (eg, groups and datasets) of its parent and may have
      new groups and/or datasets of its own. The <i>TimeSeries</i> makes
      this process of defining such pairs more hierarchical.</p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in">Each <i>TimeSeries</i> has its own HDF5
      group, and all datasets belonging to a <i>TimeSeries</i> are in that
      group. The group contains time and data components and users are free
      to add additional fields as necessary. There are two time objects
      represented. The first, <i>timestamps</i>, stores time information
      that is corrected to the experiment's time base (i.e., aligned to a
      master clock, with time-zero aligned to the starting time of the
      experiment). This field is used for data processing and subsequent
      scientific analysis. The second, <i>sync</i>, is an optional group
      that can be used to store the sample times as reported by the
      acquisition/stimulus hardware, before samples are converted to a
      common timebase and corrected relative to the master clock. This
      approach allows the NWB format to support streaming of data directly
      from hardware sources.</p>
      """
    },
    {
        "id": "<TimeSeries>_post",
        "description": "Text place after <TimeSeries>/, not included in table of contents",
        "location": {"id": "<TimeSeries>", "position": "post"},
        "content": """
    <p style="margin-bottom: 0in">When data is streamed from experiment
      hardware it should be stored in an HDF5 dataset having the same
      attributes as <i>data</i>, with time information stored as necessary.
      This allows the raw data files to be separate file-system objects
      that can be set as read-only once the experiment is complete.
      <i>TimeSeries</i> objects in /acquisition will link to the <i>data</i>
      field in the raw time series. Hardware-recorded time data must be
      corrected to a common time base (e.g., timestamps from all hardware
      sources aligned) before it can be included in <i>timestamps</i>. The
      uncorrected time can be stored in the <i>sync</i> group.</p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in">The group holding the <i>TimeSeries</i>
      can be used to store additional information (HDF5 datasets) beyond
      what is required by the specification. I.e., an end user is free to
      add additional key/value pairs as necessary for their needs. It
      should be noted that such lab-specific extensions may not be
      recognized by analysis tools/scripts existing outside the lab. 
      Extensions are described in section 
      <a href="#Extending_the_format">Extending the format</a>).</p>
    <p style="margin-bottom: 0in"><br>
    </p>
    <p style="margin-bottom: 0in">The <i>data</i> element in the
      <i>TimeSeries</i> will typically be an array of any valid HDF5 data
      type (e.g., a multi-dimentsional floating point array). The data
      stored can be in any unit. The attributes of the data field must
      indicate the SI unit that the data relates to (or appropriate
      counterpart, such as color-space) and the multiplier necessary to
      convert stored values to the specified SI unit. </p>
      """
    },
    {
        "id": "TimeSeries Class Hierarchy",
        "description": "Text placed before <AbstractFeatureSeries>/, included in table of contents",
        "location": {"id": "<AbstractFeatureSeries>", "position": "before"},
        "level": 0,
        "content": """
    <p style="margin-bottom: 0in; page-break-after: avoid">The <i>TimeSeries</i>
      is a data structure/object. It can be "subclassed" (or extended)
      to represent
      more narrowly focused modalities (e.g., electrical versus optical
      physiology) as well as new modalities (eg, video tracking of whisker
      positions). When it a <i>TimeSeries</i> is subclassed, new datasets
      can be added while all datasets of parent classes are 
      either preserved as specified in the parent class 
      or replaced by a new definition (changed).  In the tables
      that follow, identifiers in the "Id" column that change the definition in
      the parent
      class are <u>underlined</u>. An
      initial set of subclasses are described here. Users are free to
      define subclasses for their particular requirements. This can be done
      by creating an extension to the format defining a
      new <i>TimeSeries</i> subclass (see  
      <a href="#Extending_the_format">Extending the format</a>).</p>
    <p style="margin-bottom: 0in">All datasets that are defined to be
      part of TimeSeries have the text attribute 'unit' that stores the
      unit specified in the documentation.</p>
        """
    },
    {
        "id": "Modules",
        "description": "Text placed before <Interface>/, included in table of contents",
        "location": {"id": "<Interface>", "position": "before"},
        "level": 0,
        "content": """
         <p>
        NWB uses <i>modules</i> to store data for&mdash;and represent the results of&mdash;common 
        data processing steps, such as spike sorting and image segmentation, that occur 
        before scientific analysis of the data.  Modules store the data
      used by software tools to calculate these intermediate results. Each
      module provides a list of the data it makes available, and it is free
      to provide whatever additional data that the module generates.
      Additional documentation is required for data that goes beyond
      standard definitions.  All modules are stored directly under 
        group <a href="#/processing">/processing</a>.  The name of each module
        is chosen by the data provider (i.e. modules have a "variable" name).
        The particular data within each module is specified by one or more
        <i>interfaces</i>, which are groups residing directly within a module.
        Each interface extends (contains the attributes in) group 
        <a href="#<Interface>"><i>&lt;Interface&gt;</i></a> and has a fixed 
        name (e.g. <i>ImageSegmentation</i>) that suggests the
        type of data it contains.  The names of the interfaces within a given
        module are listed in the "interfaces" attribute for the module.
        The different types of Interfaces are described below.
        </p><br />
        """
    },
    {
        "id": "/acquisition_post",
        "description": "Text placed after acquisition table",
        "location": {"id": "/acquisition", "position": "post"},
        "content": """
    <p style="margin-bottom: 0in">When converting data from another
      format into NWB, there will be times that some data, particularly the
      raw data in <i>acquisition</i> and <i>stimulus</i>, is not included
      as part of the conversion. In such cases, a <i>TimeSeries</i> should
      be created that represents the missing data, even if the contents of
      that <i>TimeSeries</i> are empty. This helps to interpret the data in
      the file.</p>
      """
    },
    {
        "id": "Extending the format",
        "description": "Describes how to extend the format.",
        "location": {"id":"_toc_bottom", "position": "after"},
        "level": 0,
        "content": """
        
        <p>
        The data organization presented in this document constitutes the <i>core</i> NWB
        format.  Extensibility is handled by allowing users to store additional
        data as necessary using new datasets, attributes or groups.  There are
        two ways to document these additions.  The first is to add an attribute
        "schema_id" with value the string "Custom" to the additional groups
        or datasets, and provide documentation to describe the extra data if
        it is not clear from the context what the data represent.  This method
        is simple but does not include a consistant way to describe
        the additions.  The second method is to write an
        <i>extension</i> to the format.  With this method, the additions are
        describe by the extension and attribute "schema_id" is set to
      the string "<i>namespace</i>:<i>id</i>" where <i>namespace</i>
      is the namespace of the extension, and <i>id</i>
      is the identifier of the structure within the namespace.
      Extensions to the format are written
        using the same specification language that is used to define the
        core format.  Creating an extension allows adding the new data to the file
        through the API, validating files containing extra data, and also
        generating documentation for the additions.
        Popular extensions can be proposed
        and added to the official format specification.
        Writing and using extensions are described in the API documentation.
        Both methods allow extensibility without breaking backward compatibility.
        </p>
        """
      },{
    "id": "Acknowledgements",
        "location": {"id":"Extending the format", "position": "after"},
        "level": 0,
        "content": """
<p style="margin-bottom: 0in">The Neurodata Without Borders:
Neurophysiology Initiative is funded by GE, the Allen Institute for
Brain Science, the Howard Hughes Medical Institute (HHMI), The Kavli
Foundation and the International Neuroinformatics Coordinating
Facility. Our founding scientific partners are the Allen Institute,
the Svoboda Lab at the Janelia Research Campus of HHMI, the Meister
Lab at the California Institute of Technology, the Buzsaki Lab at
New York University School of Medicine, and the University of
California, Berkeley. Ovation.io is our founding development partner.
Ken Harris at University College London provided invaluable input and
advice.</p>
<p style="margin-bottom: 0in"><br/>
       """
      },{
    "id": "Change history",
        "location": {"id":"Acknowledgements", "position": "after"},
        "level": 0,
        "content": """
<p style="margin-bottom: 0in">1.0.3-Beta June 2016</p>
<p>Generate documentation directly from format specification file."<br />
Change ImageSeries external_file to an array.  Added attribute
starting_frame.<br />
Made TimeSeries description and comments recommended.<br />
<p style="margin-bottom: 0in">Added IZeroClampSeries.`</p>
<p style="margin-bottom: 0in"><br/>


<p style="margin-bottom: 0in">1.0.3 April, 2016</p>
<p>Renamed "ISI_Retinotopy" to "ISIRetinotopy"<br />
Change ImageSeries external_file to an array.  Added attribute
starting_frame.<br />
<p style="margin-bottom: 0in">Added IZeroClampSeries.</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">1.0.2 February, 2016</p>
<p style="margin-bottom: 0in">Fixed documentation error, updating
'neurodata_version' to 'nwb_version'</p>
<p style="margin-bottom: 0in">Created ISI_Retinotopy interface</p>
<p style="margin-bottom: 0in">In ImageSegmentation module, moved
pix_mask::weight attribute to be its own dataset, named
pix_mask_weight. Attribute proved inadequate for storing sufficiently
large array data for some segments</p>
<p style="margin-bottom: 0in">Moved 'gain' field from
Current/VoltageClampSeries to parent PatchClampSeries, due need of
stimuli to sometimes store gain</p>
<p style="margin-bottom: 0in">Added Ken Harris to the
Acknowledgements section</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">1.0.1 October 7th, 2015</p>
<p style="margin-bottom: 0in">Added 'required' field to tables in the
documentation, to indicate if group/dataset/attribute is required,
standard or optional</p>
<p style="margin-bottom: 0in">Obsoleted 'file_create_date' attribute
'modification_time' and made file_create_date a text array</p>
<p style="margin-bottom: 0in">Removed 'resistance_compensation' from
CurrentClampSeries due being duplicate of another field</p>
<p style="margin-bottom: 0in">Upgraded TwoPhotonSeries::imaging_plane
to be a required value</p>
<p style="margin-bottom: 0in">Removed 'tags' attribute to group
'epochs' as it was fully redundant with the 'epoch/tags' dataset</p>
<p style="margin-bottom: 0in">Added text to the documentation stating
that specified sizes for integer values are recommended sizes, while
sizes for floats are minimum sizes</p>
<p style="margin-bottom: 0in">Added text to the documentation stating
that, if the TimeSeries::data::resolution attribute value is unknown
then store a NaN</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">1.0.0 September 28<sup>th</sup>, 2015</p>
<p style="margin-bottom: 0in">Convert document to .html</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in"><font size="5" style="font-size: 18pt"><b>Design
notes</b></font></p>
<p style="margin-bottom: 0in"><b>1.0.1</b></p>
<p style="margin-bottom: 0in">Declaring the following groups as
required (this was implicit before) 
</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">acquisition/</p>
<p style="margin-bottom: 0in">_ images/</p>
<p style="margin-bottom: 0in">_ timeseries/</p>
<p style="margin-bottom: 0in">analysis/</p>
<p style="margin-bottom: 0in">epochs/</p>
<p style="margin-bottom: 0in">general/</p>
<p style="margin-bottom: 0in">processing/</p>
<p style="margin-bottom: 0in">stimulus/</p>
<p style="margin-bottom: 0in">_ presentation/</p>
<p style="margin-bottom: 0in">_ templates/</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">This is to ensure consistency between
.nwb files, to provide a minimum expected structure, and to avoid
confusion by having someone expect time series to be in places
they're not. I.e., if 'acquisition/timeseries' is not present,
someone might reasonably expect that acquisition time series might
reside in 'acquisition/'. It is also a subtle reminder about what the
file is designed to store, a sort of built-in documentation.
Subfolders in 'general/' are only to be included as needed. Scanning
'general/' should provide the user a quick idea what the experiment
is about, so only domain-relevant subfolders should be present (e.g.,
'optogenetics' and 'optophysiology'). There should always be a
'general/devices', but it doesn't seem worth making it mandatory
without making all subfolders mandatory here. 
</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">TwoPhotonSeries::imaging_plane was
upgraded to mandatory to help enforce inclusion of important metadata
in the file.</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in">The listed size of integers is the
suggested size. What's important for integers is simply that the
integer is large enough to store the required data, and preferably
not larger. For floating point, double is required for timestamps,
while floating point is largely sufficient for other uses. This is
why doubles (float64) are stated in some places. Because floating
point sizes are provided, integer sizes are provided as well.</p>
<p style="margin-bottom: 0in"><br/>

</p>
<p style="margin-bottom: 0in"><b>Why do timestamps_link and data_link
record linking between datasets, but links between epochs and
timeseries are not recorded?</b></p>
<p style="margin-bottom: 0in; font-variant: normal; letter-spacing: normal; font-style: normal; font-weight: normal">
<font color="#000000"><font face="Calibri, Arial, Helvetica, sans-serif"><font size="3" style="font-size: 12pt">Epochs
have a hardlink to entire timeseries (ie, the HDF5 group). If 100
epochs link to a time series, there is only one time series. The data
and timestamps within it are not shared anywhere (at least from the
epoch linking). <font face="Calibri, Arial, Helvetica, sans-serif, Apple Color Emoji, Segoe UI Emoji, NotoColorEmoji, Segoe UI Symbol, Android Emoji, EmojiSymbols">An
epoch is an entity that is put in for convenience and annotation so
there isn't necessarily an important association between what epochs
link to what time series (all epochs could link to all time series).</font></font></font></font></p>
<p style="margin-bottom: 0in; font-variant: normal; letter-spacing: normal; font-style: normal; font-weight: normal; orphans: 1">
<br/>

</p>
<p style="margin-bottom: 0in; font-variant: normal; letter-spacing: normal; font-style: normal; font-weight: normal; orphans: 1">
<font color="#000000"><font face="Calibri, Arial, Helvetica, sans-serif"><font size="3" style="font-size: 12pt">The
timestamps_link and data_link fields refer to links made between time
series, such as if timeseries A and timeseries B, each having
different data (or time) share time (or data). This is much more
important information as it shows structural associations in the
data.</font></font></font></p>
        """
      }
]
}}}

