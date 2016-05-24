# Definitions of extension to BehavioralEpochs Interface


# behei is the schema id (or 'namespace')

{"fs": {"behei": {

"info": {
    "name": "BehavioralEpochs extra info",
    "version": "1.0",
    "date": "May 6, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Example extension to NWB BehavioralEpochs interface.")
},

"schema": {
    "BehavioralEpochs/": {
        "description": "Extension to BehavioralEpochs interface to include a new dataset.",
        "my_extra_info": {
            "description": "dataset which contains extra info",
            "data_type": "text",
            "attributes": {
                "eia": {
                    "description": "attribute for my_extra_info",
                    "data_type": "text"}}}
    }
}

}}}