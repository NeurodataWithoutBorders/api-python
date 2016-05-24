# Definitions of extension to TimeSeries to store trajectory information
# All format specifications must be stored in dictionary "fs":
# "mnts" is the schema id or "namespace" for this extension.

{"fs": {"mnts": {

"info": {
    "name": "Sabes lab data trajectory series",
    "version": "1.0",
    "date": "May 2, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension to store timeseries of hand trajectories for Sabes lab data")
},

"schema": {
    "<TrajectorySeries>/": {
        "merge": ["core:<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value": ["TimeSeries", "TrajectorySeries"],
                "const": True},
            "help": {
                "data_type": "text",
                "value": "Trajectory of hand movement positions",
                "const": True},
            "measurement_names": {
                "description": "Names of measurements at each time point",
                "data_type": "text",
                "dimensions": ["num_measurements"]},
            "measurement_units": {
                "description": "Units of each measurement",
                "data_type": "text",
                "dimensions": ["num_measurements"]},
        },
        "data": {
            "description": ("Measurements of hand trajectory, recorded at each point of time."),
            "dimensions": ["num_times", "num_measurements"],
            "data_type": "float32"},
    }
}

}}}
