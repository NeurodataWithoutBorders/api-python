# This defines a new interface, called MyClosedInterface
# which is closed (does not allow new members to be added).

# "eci" is the schema id for this extension.

{"fs": { "eci": {

"info": {
    "name": "Example closed Interface extension",
    "version": "1.0",
    "date": "Sept. 22, 2016",
    "author": "Jeff Teeters",
    "contact": "jteeters@berkeley.edu",
    "description": ("Extension defining a new closed Interface")
    },
    
"schema": {
    "MyClosedInterface/": {
        "merge": ["core:<Interface>/"],
        "description": ("A new interface defined in extension e-closed-interface.py."
            "  This is closed (no new members can be added)."),
        "_properties": {"closed": True},  # specify that this group is closed (no new members can be added).
        "attributes": {
            "foo": {
                "description": "example text attributed for MyClosedInterface",
                "data_type": "text"}},
        "bar": {
            "description": ("Example dataset included with MyClosedInterface"),
            "data_type": "int",
            "dimensions": ["num_measurements"]},
        "bazc/": {
            "description": ("Example closed group in MyClosedInterface"),
            # "_closed": True,
            "_properties": {"closed": True}},
        "bazo/": {
            "description": ("Example open group in MyClosedInterface"),
            # "_closed": False,
            "_properties": {"closed": False}}
    }
}

}}}
