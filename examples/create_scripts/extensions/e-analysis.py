
{"fs": {"aibs_ct_an": {


"info": {
    "name": "AIBS cell types - analysis",
    "version": "0.9.2",
    "date": "May 6, 2016",
    "author": "Jeff Teeters, based on Allen Institute cell types DB HDF5 file",
    "contact": "jteeters@berkeley.edu",
    "description": "NWB extension for AIBS cell types data base NWB files /analysis section."
},

"schema": {
    "/analysis/": {
        "aibs_spike_times/": {
            "description": "Group for storing AIBS specific spike times",
            "attributes": {
                "comments": {
                    "data_type": "text",
                    "value": "Spike times are relative to sweep start. The are NOT absolute times."}
            },
            "<aibs_sweep>": {
                "attributes": {
                    "comments": {
                        "data_type": "text",
                        "value": "Spike times are relative to sweep start. The are NOT absolute times."}
                },
                "description": "Times associated with a single sweep",
                "dimensions": ["numSamples"],
                "data_type": "float64!"
            }
        }
    }
}

}}}
