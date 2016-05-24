# Definitions of extension to TimeSeries to store trajectory information
# All format specifications must be stored in dictionary "fs"
# "mnts2" is the "namespace" for this extension
# This extension explicitly specifies meaning for each column of dataset data

{"fs": {"mnts2": {

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
        "merge": ["core:<SpatialSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["3"],
                "value": ["TimeSeries", "SpatialSeries", "TrajectorySeries"],
                "const": True},
            "help": {
                "data_type": "text",
                "value": "Trajectory of hand movement positions",
                "const": True},
        },
        "data": {
            "description": ("Measurements of hand trajectory, recorded at each point of time."),
            "dimensions": ["num_times", "trajectories"],
            "data_type": "float32",
            "trajectories": {
                "type": "struct",
                # define components of trajectories dimension 
                "components": [
                    { "alias": "s1_x", "unit": "meter" },
                    { "alias": "s1_y", "unit": "meter" },
                    { "alias": "s1_z", "unit": "meter" },
                    { "alias": "s1_pitch", "unit": "radian" },
                    { "alias": "s1_roll", "unit": "radian" },
                    { "alias": "s1_yaw", "unit": "radian" },                   
                    { "alias": "s2_x", "unit": "meter" },
                    { "alias": "s2_y", "unit": "meter" },
                    { "alias": "s2_z", "unit": "meter" },
                    { "alias": "s2_pitch", "unit": "radian" },
                    { "alias": "s2_roll", "unit": "radian" },
                    { "alias": "s2_yaw", "unit": "radian" },                   
                    { "alias": "s3_x", "unit": "meter" },
                    { "alias": "s3_y", "unit": "meter" },
                    { "alias": "s3_z", "unit": "meter" },
                    { "alias": "s3_pitch", "unit": "radian" },
                    { "alias": "s3_roll", "unit": "radian" },
                    { "alias": "s3_yaw", "unit": "radian" },                   
                    { "alias": "s4_x", "unit": "meter" },
                    { "alias": "s4_y", "unit": "meter" },
                    { "alias": "s4_z", "unit": "meter" },
                    { "alias": "s4_pitch", "unit": "radian" },
                    { "alias": "s4_roll", "unit": "radian" },
                    { "alias": "s4_yaw", "unit": "radian" } ] },
        }
    }
}

}}}