
{"fs": {"genJson": {

"info": {
    "name": "json storage extension",
    "version": "0.9.0",
    "date": "Oct 28, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension for specifying storing of JSON formatted metadata in"
        " the general/json group.")
},

"schema": {
    "/general/json/": {
        "description": "Location for storing JSON encoded metadata as text",
        "<json_file>*": {
            "description": "Individual JSON file",
            "data_type": "text"
        }
    }
}
}}}
