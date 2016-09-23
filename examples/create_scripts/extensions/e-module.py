# Definitions of an extension defining a custom module

# In the NWB core format, each module can contain any number of interfaces
# and no particular interfaces are required.

# This extension shows how to create a custom module that specifies that
# two interfaces are required.  The two interfaces required are a custom
# interface named "MyNewInterface" and the BehavioralTimeSeries interface.

# The custom module is named "<MyNewModule>"

# All format specifications must be stored in dictionary "fs"

# "eint" is the schema id (or namespace) for this extension.

{"fs": { "new_mod": {

"info": {
    "name": "Example custom module extension",
    "version": "1.0",
    "date": "Sept. 22, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension defining a new Module type, named 'MyNewModule', that has"
        " two required interfaces")
    },
    
"schema": {
    "<MyNewModule>/": {
        "merge": ["core:<Module>/"],
        "description": ("A new module defined in extension e-module.py.  Requires two "
            "Interfaces (MyNewInterface and BehavioralTimeSeries)."),
        "include": { 
            "eint:MyNewInterface/": {},
            "core:BehavioralTimeSeries/": {} }}
    }
}}}
