# Definitions of AIBS cell types extension to NWB format

{"fs": {"aibs_ct_intra": {

"info": {
    "name": "AIBS Cell Types - intracellular metadata",
    "version": "0.9.2",
    "date": "Feb 22, 2016",
    "author": "Jeff Teeters, based on HDF5 created by Keith Godfrey using AIBS NWB API",
    "contact": "jteeters@berkeley.edu",
    "description": "NWB extension for intracellular metadata base onf AIBS cell types data base NWB files."
},

"schema": {
    "<VoltageClampSeries>/": {
        "description": ("AIBS specific VoltageClampSeries.  Includes AIBS sepcific metadata."),
        "aibs_stimulus_amplitude_mv": {
            "description": "AIBS specific stimulus_amplitude",
            "data_type": "float",
            "unit": "mv"},
        "aibs_stimulus_description": {
            "description": "AIBS specific stimulus description",
            "data_type": "text"},
        "aibs_stimulus_interval": {
            "description": "AIBS specific stimulus interval",
            "data_type": "float"},
        "aibs_stimulus_name": {
            "description": "AIBS specific stimulus name",
            "data_type": "text"},
    },
    "<CurrentClampSeries>/": {
        "description": ("AIBS specific CurrentClampSeries.  Includes AIBS sepcific metadata."),
        "aibs_stimulus_amplitude_pa": {
            "description": "AIBS specific stimulus_amplitude",
            "data_type": "float",
            "unit": "pa"},
        "aibs_stimulus_description": {
            "description": "AIBS specific stimulus description",
            "data_type": "text"},
        "aibs_stimulus_interval": {
            "description": "AIBS specific stimulus interval",
            "data_type": "float"},
        "aibs_stimulus_name": {
            "description": "AIBS specific stimulus name",
            "data_type": "text"},
    },
    "/stimulus/presentation/<CurrentClampStimulusSeries>/": {
		"description": ("AIBS specific CurrentClampStimulusSeries, only applies to "
		    "location /stimulus/presentation/, but not to location /stimulus/templates"),
		"aibs_stimulus_amplitude_pa": {
			"description": "AIBS specific stimulus_amplitude",
			"data_type": "float",
			"unit": "mv"},
		"aibs_stimulus_description": {
			"description": "AIBS specific stimulus description",
			"data_type": "text"},
		"aibs_stimulus_interval": {
			"description": "AIBS specific stimulus interval",
			"data_type": "float"},
		"aibs_stimulus_name": {
			"description": "AIBS specific stimulus name",
			"data_type": "text"},
    },
	"/stimulus/presentation/<VoltageClampStimulusSeries>/": {
		"description": ("AIBS specific VoltageClampStimulusSeries, only applies to "
		    "location /stimulus/presentation/, not to location /stimulus/templates"),
		"aibs_stimulus_amplitude_mv": {
			"description": "AIBS specific stimulus_amplitude",
			"data_type": "float",
			"unit": "mv"},
		"aibs_stimulus_description": {
			"description": "AIBS specific stimulus description",
			"data_type": "text"},
		"aibs_stimulus_interval": {
			"description": "AIBS specific stimulus interval",
			"data_type": "float"},
		"aibs_stimulus_name": {
			"description": "AIBS specific stimulus name",
			"data_type": "text"},
	}
}

}}}