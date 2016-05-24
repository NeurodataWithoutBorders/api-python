# Definitions of an extension defining a new interface

# This defines a new interface, called MyNewInterface
# All format specifications must be stored in dictionary "fs"

# "eint" is the schema id (or namespace) for this extension.

{"fs": { "eint": {

"info": {
    "name": "Example Interface extension",
    "version": "1.0",
    "date": "May 2, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension defining a new Interface type, named 'MyNewInterface'")
    },
    
"schema": {
    "MyNewInterface/": {
        "merge": ["core:<Interface>/"],
        "description": ("A new interface defined in extension e-interface.py.  Uses the "
            "new timeseries defined in extension e-timeseries.py"),
        "attributes": {
            "foo": {
                "description": "example text attributed for MyNewInterface",
                "data_type": "text"}},
        "<new_ts>/": {
            # use MyNewTimeSeries in the MyNewInterface
            "merge": ["mnts:<MyNewTimeSeries>/"]  
        },
        "bar": {
            "description": ("Example dataset included with MyNewTimeSeries"),
            "data_type": "int",
            "dimensions": ["num_measurements"]}
    }
}

}}}
