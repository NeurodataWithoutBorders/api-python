import sys
import time
import os.path
from . import h5gate as g
from . import nwb_init as ni

def open(file_name, start_time=None, mode="w-", identifier=None, description=None,
    core_spec="nwb_core.py", extensions=[], default_ns="core",
    keep_original=False, auto_compress=True, verbosity="all"):
    """
    Open NWB file.  Initialize identifier and description if "write" mode.
    Returns h5gate File object which is used by API to add content to the file.
    Inputs are:
    
    **file_name** - Name of file to create or open.  Text. Required.
    
    **start_time** - Starting time for the experiment.  Is used only if writing
    a file (mode="w").  If not specified, the current time is used.
    
    **mode** - Mode of file access.  One of:
        'r'  - Readonly, file must exist.  (currently only used for validation).
        'r+' - Read/write, file must exist.
        'w'  - Create file, replacing if exists. (Default)
        'w-' - Create file, fail if exists.
        'a'  - Read/write if exists, create otherwise.
    
    **identifier** - Unique identifier for the file.  Required if "w" mode.  Not
    used otherwise.
    
    **description** - A one or two sentence description of the experiment and what
    the data inside represents.  Required if "w" mode.  Not used otherwise.
    
    **core_spec** - Name of file containing core specification of NWB format.
    If "-", load saved spec from NWB file (used when opening an existing file).
    
    **extensions** - List of files containing extensions to the format that may
    be used.  Empty list if no extensions or if extension specifications should be
    loaded from NWB file.
    
    **default_ns** - Namespace of specification to use as default if no namespace
    specified when creating groups or datasets.  Normally, the default value ("core")
    should be used, since that is the namespace used in the default core_spec
    ("nwb_core.py")
    
    **keep_original** - If True and mode is "w" or "r+" or "a" (modes that can change
    and exiting file), a backup copy of any original file will be saved with the name
    "<filename>.prev".
    
    **auto_compress** - If true, data is compressed automatically through the API.
    Otherwise, the data is not automatically compressed.
    
    **verbosity** - Controls how much validation output is displayed.  Options are:
    'all' (default), 'summary', and 'none'.  'none' is mainly useful for unittests.
    """
    # set unicode to str if using Python 3 (which does not have unicode class)
    try:
        unicode
    except NameError:
        unicode = str
    # check for required fields
    errors = []
    if not file_name or not isinstance(file_name, (str, unicode)):
        errors.append("file_name must be specified and be type string or unicode")
    if not core_spec or not isinstance(core_spec, str):
        errors.append("core_spec must be specified and be a string")
    valid_modes = ("r", "r+", "w", "w-", "a")
    if mode not in valid_modes:
        errors.append("Invalid mode.  Must be one of: %s" % valid_modes)
    file_exists = os.path.isfile(file_name)
    if not file_exists and mode in ('r', 'r+'):
        errors.append("File not found.  File must exist to use mode 'r' or 'r+'")
    else:
        creating_file = mode=="w" or (mode in ('a', 'w-') and not file_exists)
        if creating_file:
            # must be creating a new file.  identifier and description required.
            if not identifier or not isinstance(identifier, str):
                errors.append("When creating a file, 'identifier' must be specified and be a string")
            if not description or not isinstance(description, str):
                errors.append("When creating a file, 'description' must be specified and be a string")
        if not isinstance(extensions, (list, tuple)) or (len(extensions) > 0 and
            not all(isinstance(item, str) for item in extensions)):
            errors.append("extensions must be a list or tuple, either empty or containing only strings")
#         if file_exists and mode == "w" and not overwrite:
#             errors.append("Cannot overwrite existing file if overwrite option is False")

    if errors:
        print ("Error(s) found:")
        print ("\n".join(errors))
        sys.exit(1)
    # setup options for h5gate
    options = {}
    options['mode'] = mode
    options['keep_original'] = keep_original
    options['auto_compress'] = auto_compress
    options['verbosity'] = verbosity
    # options['schema_id_attr'] = "neurodata_type"
    options['custom_node_identifier'] = ["neurodata_type", "Custom"]
    # options['custom_node_identifier'] = ["schema_id", "Custom"]
    spec_files = extensions + [core_spec] if core_spec != '-' else []
    # open file
    f = g.File(file_name, spec_files, default_ns, options)
    # set initial metadata and call_back for updating modification_time
    ni.nwb_init(f, mode, start_time, identifier, description, creating_file)
    return f
    
 

    
 
