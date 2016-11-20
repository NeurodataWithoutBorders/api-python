
# define an extension to add metadata to the /general section
# 'rctn' is a key used to identify this extension
# rctn stands for "Redwood Center for Theoretical Neuroscience"
# (Any name could be used).


{"fs": {"rctn": {

"info": {
    "name": "RCTN extension",
    "version": "0.9.0",
    "date": "Feb 21, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Redwood Center for Theoretical Neuroscience extension for the NWB"
        " format.  Also includes some metadata for the AIBS cell types database")
},

"schema": {
    '/general/activity_level': {
        'data_type': 'text',
        'description': "Activity level of animal.  10 - very active; 1-asleep"},
    'time_since_fed': {
        'data_type': 'text',
        'description': "Time animal last fed prior to session"},
    "/general/": {
        "description": "Extension to core general",
        "include": {  'time_since_fed': {}},
        "_required": { # Specifies required member combinations",
            "test_req" :
                ["notes AND experiment_description",
                    "notes and experiment_description are both required"]},
        "experimenter": {
            "attributes": {
                "orcid_id": {
                    "description": "machine readable id, addeded with rctn schema",
                    "data_type": "text"}}},
        "rctn_info/": {
            "description": "Custom directory for rctn information",
            'seminars': {
                "description": "Names of speakers in some past seminars",
                'data_type': 'text',
                'dimensions': ["num_seminars"]},
            'attendance': {
                "description": "Number of people attending corresponding seminar",
                'data_type': 'int',
                'dimensions': ["num_seminars"]}}
    },
    # added metadata about the subject, from AIBS cell types database
    # 'aibs_' prefix was convention used in this instance but no particular naming
    # scheme is required
    "/general/subject/": {
        "aibs_specimen_id": {
            "data_type": "int",
            "description":"AIBS specific specimen ID"},
        "aibs_specimen_name": {
            "data_type": "text",
            "description": "AIBS specific specimen_name"},
        "aibs_dendrite_state": {
            "data_type": "text",
            "description": "AIBS specific dendrite_state"},
        "aibs_dendrite_type": {
            "data_type": "text",
             "description": "AIBS specific dendrite type"},
        "aibs_cre_line": {
            "data_type": "text",
            "description": "AIBS specific cre_line"}
    }
}
}}}