import time
import h5gate as g
import numpy as np

VERS_MAJOR = 0
VERS_MINOR = 1
VERS_PATCH = 1
FILE_VERSION_STR = "NWB-%d.%d.%d" % (VERS_MAJOR, VERS_MINOR, VERS_PATCH)
IDENT_PREFIX = "Neurodata h5gate testing " + FILE_VERSION_STR + ": "

def initialize_metadata(f, file_name, start_time):
    """ Set initial metadata in nwb file.  f is NWB_file object (inherits
    from h5gate) """     
    f.set_dataset("neurodata_version", FILE_VERSION_STR)
    hstr = IDENT_PREFIX + time.ctime() + "--" + file_name
    f.set_dataset("identifier", hstr)
    f.set_dataset("file_create_date", time.ctime())
    sess_start_time = time.ctime() if start_time == "" else start_time
    f.set_dataset("session_start_time", np.string_(sess_start_time))
        
    # def create_identifier(base_string):
    #    return base_string + " " + FILE_VERSION_STR + ": " + time.ctime()
    # if 'schema_id_attr' not in options:
    #  options['schema_id_attr'] = 'nwb_sid'