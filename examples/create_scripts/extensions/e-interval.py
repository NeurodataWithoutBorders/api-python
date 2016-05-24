# Definitions of extension to IntervalSeries

# "isc" is the schema id (or 'namespace')
# "fs" must always be the top level key

{"fs": {"isc": {

"info": {
    "name": "Interval series code descriptions",
    "version": "1.0",
    "date": "April 7, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension to NWB Interval Series to include a code and "
        "code_description dataset.")
},

"schema": {
    "<IntervalSeries>/": {
        "description": "Extension to IntervalSeries to include code descriptions.",
        "codes": {
            "description": "Codes that are used in the IntervalSeries",
            "data_type": "int",
            "dimensions": ["num_codes"] },
        "code_descriptions": {
            "description": "Description of each code",
            "data_type": "text",
            "dimensions": ["num_codes"] }}
}

}}}


