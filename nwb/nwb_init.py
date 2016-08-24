import sys
import nwb.nwb_utils as ut

def nwb_init(f, mode, start_time, identifier, description, creating_file):
    """ Set initial metadata if creating a new file or set callback for
    updating modification time if modifying an existing file.  f is the
    h5gate File object.  creating_file is True if creating a new file.
    See file nwb_file for description of mode, start_time, identifier and
    description.
    """
    if mode in ('r+', 'a') and not creating_file:
        # modifying existing file.  Setup callback to update modification_time
        f.set_close_callback(nwb_close_callback)
    elif creating_file:
        # set initial metadata for new file
        version = f.ddef[f.default_ns]['info']['version']
#         vinfo = ["Specification(s):"]
#         vinfo.append("file name\tnamespace\tversion\tdate")
#         for file_name in f.spec_files:
#             for ns in f.fsname2ns[file_name]:
#                 version = f.ddef[ns]['info']['version']
#                 date = f.ddef[ns]['info']['date']
#                 info = "%s\t%s\t%s\t%s" % (file_name, ns, version, date)
#                 vinfo.append(info)
#         vinfo.append("Default namespace='%s'" % f.default_ns)
#         api_version = f.get_version()
#         vinfo.append("API: %s" % api_version)
#         version = "\n".join(vinfo)
        f.set_dataset("nwb_version", version)
        f.set_dataset("identifier", identifier)
        f.set_dataset("session_description", description)
        curr_time = ut.current_time()
        f.set_dataset("file_create_date", [curr_time, ])
        if not start_time:
            start_time = curr_time
        f.set_dataset("session_start_time", start_time)
        
           
def nwb_close_callback(f):
    """ Executed on close of nwb file.  Updates modification time"""
    if f.file_changed:
        if f.creating_file or f.options['mode'] not in ('r+', 'a'):
            print ("Unexpected condition when calling close_callback. "
                "creating_file=%s, mode=%s") %(f.creating_file, f.options['mode'])
            sys.exit(1)
        # file changed.  Append current time to modification time
        cd = f.get_node("/file_create_date", abort = False)
        if not cd:
            f.warning.append("Unable to append modification time to /file_create_date.  "
                " Dataset does not exist.")
        else:
            cur_time = ut.current_time()
            cd.append(cur_time)
    else:
        f.warning.append("Not updating modification time because file was not changed.")
            
# Below code used if modifications_time stored as attribute        
#         if "modification_time" in cd.h5attrs:
#             mod_times = cd.h5attrs["modification_time"]
#             if not isinstance(mod_times, (list,)):
#                 f.warning.append("Did not update modification time, because type "
#                     "was unexpected: %s") % type(mod_times)
#             else:
#                 cur_time = utils.current_time()
#                 mod_times = mod_times + [cur_time]  # don't use append to avoid changing original
#                 cd.set_attr("modification_time", mod_times)    
#                 print "Updated modification time."""
        
       

    