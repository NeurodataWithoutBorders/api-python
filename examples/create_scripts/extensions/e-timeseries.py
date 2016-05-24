# Example extension defining a new TimeSeries

# All format specifications must be stored in dictionary with top level key "fs":
# "mnts" is the "namespace" for this extension.


{"fs": {"mnts": {
"info": {
    "name": "Example TimeSeries extension",
    "version": "1.0",
    "date": "May 2, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension defining a new TimeSeries type, named 'MyNewTimeSeries'")
},

"schema": {
    "<MyNewTimeSeries>/": {
        "description": "A new timeseries, defined in extension e-timeseries.py",
        "merge": ["core:<TimeSeries>/"],
        "attributes": {
            "ancestry": {
                "data_type": "text",
                "dimensions": ["2"],
                "value": ["TimeSeries", "MyNewTimeSeries"],
                "const": True},
            "help": {
                "data_type": "text",
                "value": "Short description of MyNewTimeSeries goes here",
                "const": True},
            "foo": {
                "description": "example new text attributed for MyNewTimeSeries",
                "data_type": "text"}},
        "data": {
            "description": ("Multiple measurements are recorded at each point of time."),
            "dimensions": ["num_times", "num_measurements"],
            "data_type": "float32"},
        "bar": {
            "description": ("Example dataset included with MyNewTimeSeries"),
            "data_type": "int",
            "dimensions": ["num_measurements"]}
    }
}
}}}
