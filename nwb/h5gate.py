# Code to manage creation of hdf5 files based on specification language
# Modified to work with MatLab

import traceback
# import h5py
# import numpy as np
import sys
import re
import copy
import os.path
import imp

import pprint
pp = pprint.PrettyPrinter(indent=4)

class File(object):
    """ hdf5 file """
    def __init__(self, fname, ddef={}, dimp=[], default_ns="core", options=[]):
        """ Created file.
        fname - name of file
        ddef - Supplied data definition (written in h5gate specification language)
        dimp - Tuple of data definition files to import.  Can be used to import the
        core definitions and/or extensions.  Each element is a string with format:
	    "<file_name>":"<var_name>"
        where <file_name> is name of .py file defining the structures and locations,
        and <var_name> is the variable having the definitions in that file.
        default_ns - default name space for referencing data definition structures
        options - specified options.  Either a dictionary or a tuple that can be
        converted to a dictionary (with alternating keys and values).  See 
        'validate_options' below for possible options.
        """
        self.file_name = fname
        self.default_ns = default_ns  # ns == 'name space'
        self.options = self.cast_to_dict(options)
        self.validate_options()
        self.load_data_definitions(ddef, dimp)
        # self.validate_ddef()
        self.initialize_storage_method()
        self.id_lookups = self.mk_id_lookups()
        # print "id_lookup is:"
        # pp.pprint(self.id_lookups)
        self.all_nodes = {}
        self.path2node = {}
        self.custom_attributes = {}
        self.create_output_file()
        
    def validate_options(self):
        """Validate provided options and adds defaults for those not specified"""
        all_options = {
            'fspec_dir' : {
                'description': ('Default location for format specification files'
                    ' (defining the format using the specification language).  This'
                    ' used for loading specification files listed in the "dimp" parameter.'),
                'default': os.path.dirname(os.path.realpath(__file__))},
            'link_type': {
                'description': 'Type of links when linking one dataset to another',
                'values': { # following tuples have description, then 'Default' if default value
                    'hard': 'hdf5 hard links',
                    'string': 'make string dataset containing path to link'},
                'default': 'hard' },
            'include_schema_id': {
                'description': 'Include schema id as attributed in generated file',
                'values': {
                    True: 'yes, include id',
                    False: 'no, do not includ id'},
                'default': True },
            'schema_id_attr': {
                'description': 'Id to use attributes for schema id',
                'default': 'h5g8id', },
            'flag_custom_nodes': {
                'description': "Include schema_id: custom' in attributes for custom nodes",
                'values': {
                    True: 'yes, include id',
                    False: 'no, do not includ id'},
                'default': True },
            'default_compress_size': {
                'description': ('Compress datasets that have total size larger than this'
                    ' value, or 0 if should not do any compression based on size'),
                'default': 512, },
            'storage_method': {
                'description': ('Method used to store data.  This allows for storing'
                    ' data using different storage methods.'),
                'values': {
                    'hdf5': 'Data stored in hdf5 file using h5py',
                    'none': ('Data not stored using this code.  Commands to store data'
                        ' are saved in self.h5commands for processing by'
                        ' a calling program, e.g. MatLab.'),},
                'default': 'hdf5', },
        }
        errors = []
        for opt, value in self.options.iteritems():
            if opt not in all_options:
                errors.append("Invalid option specified (%s)" % opt)
            elif 'values' in all_options[opt] and value not in all_options[opt]['values']:
                errors.append(("Invalid value specified for option (%s), should be"
                    " one of:\n%s") % (opt, all_options[opt].keys()))
        if errors:
            print "\n".join(errors)
            print "valid options are:"
            pp.pprint(all_options)
            sys.exit(1)
        # Add default values for options that were not specified
        for opt in all_options:
            if opt not in self.options:
                self.options[opt] = all_options[opt]['default']
        # print "After adding defaults, options are:"
        # pp.pprint(self.options)
        # sys.exit(0) 
    
    def cast_to_dict(self, obj):
        """ obj should be a list type or a dictionary.  If a list, convert to a
        dictionary assuming elements are alternate keys and values """
        if type(obj) is dict:
            return obj
        elif type(obj) is tuple or type(obj) is list:
            # convert to dictionary
            return dict(zip(obj[0::2], obj[1::2]))
        else:
            print ('Invalid class (%s) for object.  Trying to convert to'
                ' dict.  Should be either dict, list or tuple.') % type(obj)
            print "object is:"
            pp.pprint(obj)
            traceback.print_stack()
            sys.exit(1)
          
    def load_data_definitions(self, ddef, dimp):
        """ Load any file format specifications included in 'dimp' parameter.  Merge
        with any specifications passed in using 'ddef' parameter.
        Save merged definitions in self.ddef """
        if ddef:
            errors = self.validate_fs(ddef)
            if errors:
                raise Exception("Provided format specification has"
                    " the following error(s):\n%s" % errors)
        self.ddef = ddef
        default_dir = self.options['fspec_dir']
        for fv in dimp:
            # fv format is: "<file_name>":"<var_name>"
            matchObj = re.match(r'^"([^"]+)":"([^"]+)"$', fv)        
            if not matchObj:
                raise Exception('** Error: Unable to find "<file_name>":"<var>" in ''%s''' % fv)
            fname = matchObj.group(1)
            var = matchObj.group(2)
            if not fname.endswith('.py'):
                fname += '.py'
            if not os.path.isfile(fname):
                fname = os.path.join(default_dir, fname)
                if not os.path.isfile(fname):
                    raise Exception('Unable to locate format specification file: %s' %
                        fname)
            dd = imp.load_source('temp_module_name', fname)
            if var not in dir(dd):
                raise Exception("Variable '%s' not defined in specification file '%s'" %
                    (var, fname))
            # get definitions that are in variable var
            ddefin = eval("dd.%s" % var)
            del sys.modules['temp_module_name']
            # check for "structures" and "locations"
            errors = self.validate_fs(ddefin)
            if errors:
                print ("Specification file '%s', variable '%s' has"
                    " the following errors:\n%s" % (fname, var, errors))
                sys.exit(1)
            # seems, ok, merge it with other definitions
            self.ddef.update(ddefin) 
        if not self.ddef:
            raise Exception("No file format specifications were provided.  At least one"
                 " is required.")
        if self.default_ns not in self.ddef.keys():
            raise Exception("Default name space ('%s') does not appear in data definitions"
                % self.default_ns)
               
    def validate_fs(self, fs):
        """ Validate a format specification.  Return description of any errors, or None
        if no errors"""
        if type(fs) is not dict:
            return ("Specification is not a Python"
                    " dictionary.  It must be, and have name space keys")
        if not fs.keys():
            return ("Specification does not have any name space keys")
        errors = []
        for ns in fs.keys():
            if 'structures' not in fs[ns].keys():
                errors.append("Namespace '%s' is missing ['structures'] definition" % ns)
            if 'locations' not in fs[ns].keys():
                errors.append("Namespace '%s' is missing ['locations'] definition" % ns)        
        if len(errors) > 0:
            errors =  "\n".join(errors)
            return errors
        return None       
    
#     def validate_ddef(self):
#         """ Make sure that each namespace has both a "structures" and "locations"
#             and that the default name space is defined """
#         if self.default_ns not in self.ddef.keys():
#             print "** Error"
#             print "Default name space ('%s') does not appear in data definitions" % self.default_ns
#             sys.exit(1)
#         errors = self.validate_fs(self.ddef)
#         errors = []
#         for ns in self.ddef.keys():
#             if 'structures' not in self.ddef[ns].keys():
#                 errors.append("Namespace '%s' is missing ['structures'] definition" % ns)
#             if 'locations' not in self.ddef[ns].keys():
#                 errors.append("Namespace '%s' is missing ['locations'] definition" % ns)        
#         if len(errors) > 0:
#             print "** Error"
#             print "\n".join(errors)
#             sys.exit(1)
                  
    def initialize_storage_method(self):
        """ Initialize method for storing data.  Currently only methods are
        'hdf5' and 'none'.  hdf5 uses h5py.  'none' saves commands for later
        processing by a calling script (for example, MATLAB)."""
        if self.options['storage_method'] == 'hdf5':
            import h5py
            import numpy as np
            global h5py, np
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.clear_storage_commands()
        else:
            raise Exception('Invalid storage_method (%s)' % storage_method)
            
    def clear_storage_commands(self):
        """ Clear list of storage commands.  This method is called by an external
        script (e.g. MATLAB) to clear commands after they are processed."""
        self.h5commands = []       
      
    def create_group(self, path):
        """ Creates a group using the selected storage_method option.  If storage_method
        is 'hdf5', group is created in the hdf5 file using h5py.  If storage method is
        'none', command to create the group is saved for later processing by a
        calling program, e.g. MatLab.  This is the only function used to create a group"""
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file_pointer.create_group(path)
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.h5commands.append(("create_group", path,))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
    
    def create_dataset(self, path, data, dtype=None, compress=False):
        """ Creates a dataset using the selected storage_method option.  If storage_method
        is 'hdf5', dataset is created in the hdf5 file using h5py.  If storage method is
        'none', command to create the group is saved for later processing by a
        calling program, e.g. MatLab.  This is the only function used to create a dataset"""
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            compress = "gzip" if compress else None
            self.file_pointer.create_dataset(path, data=data, dtype=dtype, 
                compression=compress)
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.h5commands.append(("create_dataset", path, data, dtype, compress))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
   
    def create_softlink(self, path, target_path):
        """ Creates a softlink using the selected storage_method option.  If storage_method
        is 'hdf5', softlink is created in the hdf5 file using h5py.  If storage method is
        'none', command is saved for later processing by a calling program, e.g. MatLab."""
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file_pointer[path] = h5py.SoftLink(target_path)
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.h5commands.append(("create_softlink", path, target_path))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
 
    def create_external_link(self, path, target_file, target_path):
        """ Creates an external link using the selected storage_method option.  If storage_method
        is 'hdf5', create using h5py.  If storage method is
        'none', command is saved for later processing by a calling program, e.g. MatLab."""
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file.file_pointer[self.full_path] =  h5py.ExternalLink(file,path)
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.h5commands.append(("create_external_link", path, target_file, target_path))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)

    def set_attribute(self, path, name, value):
        """ Set an attribute using the selected storage_method option.  If storage_method
        is 'hdf5', set using h5py.  If storage method is 'none', save command for later
        processing by a calling program, e.g. MatLab."""
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file_pointer[path].attrs[name] = value
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.h5commands.append(("set_attribute", path, name, value))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
                              
    def create_output_file(self):
        """ open output file and add initial structure
        """
        if self.options['storage_method'] == 'hdf5':
            try:
                fp = h5py.File(self.file_name, "w")
            except IOError:
                print "Unable to open output file '%s'" % self.file_name
                sys.exit(1)
            # remember file pointer
            self.file_pointer = fp
            print "Creating file '%s'" % self.file_name
        elif self.options['storage_method'] == 'none':
            # save command for later processing
            self.h5commands.append(("create_file", self.file_name))
                   
    def close(self):
        self.validate_file()
        if self.options['storage_method'] == 'hdf5':
            self.file_pointer.close()
        elif self.options['storage_method'] == 'none':
            self.h5commands.append(("close_file", ))

    def mk_id_lookups(self):
        """ Makes id_lookup for each namespace.  See "mk_id_lookup" (singular) for structure.
        """
        id_lookups = {}
        for ns in self.ddef.keys():
            id_lookups[ns] = self.mk_id_lookup(ns)
        return id_lookups

    def mk_id_lookup(self, ns):
        """ Creates dictionary mapping id's in definitions to dictionary of locations these
            items may be stored.  For each location, store a dictionary of allowed 
            quantity for the item ('*' - any, '?' - optional, '!' - required, 
            '+' - 1 or more) and
            list of actual names used to create item (used to keep track if required items
            are set.
        """
        if 'structures' not in self.ddef[ns].keys():
            print "** Error.  Namespace '%s' does not contain key 'structures'" % ns
            sys.exit(1)
        if 'locations' not in self.ddef[ns].keys():
            print "** Error.  Namespace '%s' does not contain key 'locations'" % ns
            sys.exit(1)
        # print "found structures and locations in " + ns
        id_lookup = {}
        referenced_structures = []
        for location in self.ddef[ns]['locations'].keys():
            ids = self.ddef[ns]['locations'][location]
            for id in ids:
                id_str, qty_str = self.parse_qty(id, "?")
                if id_str not in self.ddef[ns]['structures'] and id_str != '__custom':
                    print "** Error, in namespace '%s':" % ns
                    print "structure '%s' referenced in nwb['%s']['locations']['%s']," % (id_str, ns, location)
                    print "but is not defined in nwb['%s']['structures']" % ns
                    sys.exit(1)
                referenced_structures.append(id_str)
                type = 'group' if id_str.endswith('/') else 'dataset'
                if id_str not in id_lookup.keys():
                    id_lookup[id_str] = {}  # initialize dictionary of locations
                id_lookup[id_str][location] = {'type': type, 'qty': qty_str, 'created':[] }
                # print "Location=%s, id=%s, id_str=%s, qty_str=%s" % (location, id, id_str, qty_str)
        # make sure every structure has at least one location
        no_location = []
        for id in self.ddef[ns]['structures']:
            if id not in referenced_structures:
                no_location.append(id)
        if len(no_location) > 0:
            pass
            # print "** Warning, no location was specified for the following structure(s)"
            # print ", ".join(no_location)
            # print "This is not an error if they are referenced by a merge or include"            
        return id_lookup
        
    def get_sdef(self, qid, default_ns, errmsg=''):
        """ Return structure definition of item as well as namespace and id within
            name space.  If structure does not exist, display error message (if given)
            or return None.
            qid - id, possibly qualified by name space, e.g. "core:<timeStamp>/", 'core' is
                is the name space.
            default_ns - default namespace to use if qid does not specify
            errmsg - error message to display if item not found.
        """
        (ns, id) = self.parse_qid(qid, default_ns)
        if id in self.ddef[ns]['structures'].keys():
            df = self.ddef[ns]['structures'][id]
            type = 'group' if id.endswith('/') else 'dataset'
            sdef = { 'type': type, 'qid': qid, 'id':id, 'ns':ns, 'df': df, }
            return sdef
        if errmsg != "":
            print "Structure '%s' (in name space '%s') referenced but not defined." % (id, ns)
            print "(%s)" % errmsg
            traceback.print_stack()
            sys.exit(1)
        return None
        
    def parse_qty(self, qid, default_qty):
        """ Parse id which may have a quantity specifier at the end. 
        Quantity specifiers are: ('*' - any, '!' - required,
        '+' - 1 or more, '?' - optional, or '' - unspecified)
        """
        matchObj = re.match( r'^([^*!+?]+)([*!+?]?)$', qid)        
        if not matchObj:
            print "** Error: Unable to find match in pattern '%s'" % qid
            traceback.print_stack()
            sys.exit(1)
        id = matchObj.group(1)
        qty = matchObj.group(2)
        if qty is '':
            # quantity not specified, use default
            qty = default_qty
        return (id, qty)       
    
    def parse_qid(self, qid, default_ns):
        """ Parse id, which may be qualified by namespace
            qid - possibly qualified id, e.g. "core:<id>", 'core' is a namespace,
            default_ns - default namespace to use of qid not specified.
            Returns namespace and id as tuple (ns, id). """
        # matchObj = re.match( r'([^:*]*):?(.*)', qid)
        matchObj = re.match( r'^(?:([^:]+):)?(.+)', qid)        
        if not matchObj:
            print "** Error: Unable to find match in pattern '%s'" % qid
            traceback.print_stack()
            sys.exit(1)
        ns = matchObj.group(1)
        id = matchObj.group(2)
        if ns is None:
            # namespace not specified, use default
            ns = default_ns
        self.validate_ns(ns)
        return (ns, id)

    def validate_ns(self, ns):
        if ns not in self.ddef.keys():
            print "Namespace '%s' referenced, but not defined" % ns
            traceback.print_stack()
            sys.exit(1)                  
        
    def make_group(self, qid, name='', path='', attrs={}, link='', abort=True):
        """ Creates groups that are in the top level of the definition structures.
            qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
            name - name of group in case name is not specified by id (id is in <angle brackets>)
                *OR* Group node linking to
                *OR* pattern to specify link: link:path or extlink:file,path
            path - specified path of where group should be created.  Only needed if
                location ambiguous
            attrs - attribute values for group that are specified in API call.  Either
                dictionary or list that will be converted to a dictionary.
            link - specified link, of form link:path or extlink:file,path.  Only needed
                if name must be used to specify local name of group
            abort - If group already exists, abort if abort is True, otherwise return previously
                existing group."""
        gqid = qid + "/"
        sdef = self.get_sdef(gqid, self.default_ns, "referenced in make_group")
        id = sdef['id']
        ns = sdef['ns']
        path = self.deduce_path(id, ns, path)
        if not abort:
            id_noslash = id.rstrip('/')  # could be different from gqid if namespace present
            grp = self.get_existing_group(path, id_noslash, name)
            if grp:
                # found already existing group
                return grp            
        link_info = self.extract_link_info(name, link, Group)
        # create the group
        parent = None  # no parent since this node created from File object (top level)
        grp = Group(self, sdef, name, path, attrs, parent, link_info)
        return grp
        
    def get_existing_group(self, path, id, name):
        """ Return existing Group object if attempting to create group again, otherwise,
        return None.  This called by make_group to check for existing group if abort
        is False."""
        v_id = re.match( r'^<[^>]+>$', id) # True if variable_id (in < >)
        lookup_name = name if v_id else id
        full_path = path + "/" + lookup_name
        node = self.get_node(full_path, False)
        if node and node.sdef['type'] == 'group':
            # found already existing group
            return node
        else:
            return None
        
    def deduce_path(self, id, ns, path):
        """Deduce location based on id, namespace and specified_path
        and using locations section of namespace, which is stored in
        id_lookups.  Return actual path, or abort if none."""
        locations = self.id_lookups[ns][id]
        if path != '':
            if path not in locations.keys():
                print "** Error"
                print "Specified path '%s' not in name space '%s' locations for id '%s'" % (path, ns, id)
                traceback.print_stack()
                sys.exit(1)
        else:
            if len(locations) > 1:
                print "** Error"
                print "Path not specified for '%s', but must be since" %id
                print " there are multiple locations:" + ", ".join(locations.keys())
                traceback.print_stack()
                sys.exit(1)
            path = locations.keys()[0]
        return path
        
    def extract_link_info(self, val, link, node_type):
        """ Gets info about any specified link.
        Links can be specified in three ways:
            1. By setting the name of a group or the value of a dataset to a target node
            2. By setting the name of a group or the value of a dataset to a link pattern
            3. By specifying a link pattern explicitly (only for groups, since make_group
                does not have a "value" option, an extra parameter (link) is made available
                if needed to specify the link.  (Needed means the name is used to specify
                the name of the group).
        Function parameters are:
            val - name of group or value of dataset (used for methods 1 & 2)
            link - explicitly specified link pattern (used for method 3.
            node_type, type of node being linked.  Either Group or Dataset.  (used
            for method 1). """
        link_info = None
        if type(val) is node_type:
            # method 1
            link_info = {'node': val}
        else:
            # method 2
            link_info = self.extract_link_str(val)
            if not link_info:
                # method 3
                link_info = self.extract_link_str(link)
        return link_info
    
    def extract_link_str(self, link):
        """ Checks if link is a string matching a pattern for a link.  If so,
        return "linl_info" dictionary"""
        if type(link) is str:
            # import pdb; pdb.set_trace()
            if re.match( r'^link:', link):
                # assume intending to specify a link, now match for rest of pattern            
                matchObj = re.match( r'^link:([^ ]+)$', link)
                if matchObj:
                    path =  matchObj.group(1)
                    node = self.get_node(path)
                    link_info = {'node': node}
                    return link_info
                else:
                    print "** Error, invalid path specified in link string, must not have spaces"
                    print " link string is: '%s'" % link
                    traceback.print_stack()
                    sys.exit(1)
            elif re.match( r'^extlink:', link):
                # assume intending to specify an external link, now match for rest of pattern
                matchObj = re.match( r'^extlink:([^ ]*[^ ,])[ ,]([^ ]+)$', link)
                if matchObj:
                    file = matchObj.group(1)
                    path = matchObj.group(2)
                    link_info = {'extlink': (file, path)}
                    return link_info
                else:
                    print "** Error, invalid file or path specified in extlink string"
                    print " must not have spaces and file name must not end in comma"
                    print "extlink string is: '%s'"% link
                    traceback.print_stack()
                    sys.exit(1)
        return None             
                
    def validate_custom_name(self, name):
        """ Make sure valid name used for custom group or dataset"""
        if not re.match( r'(/?[a-zA-Z_][a-zA-Z0-9_]*)+$', name):
            raise ValueError('Invalid name for node (%s)' % name)
        return
        
    def validate_path(self, path):
        """ Make sure path is valid """
        return True  #  Allow anything in path, even spaces
        # pattern = r'(/?[a-zA-Z_][a-zA-Z0-9_]*)+$'  # require start with letter
        # pattern = r'(/?[a-zA-Z0-9_]*)+$'  # allow start with number
        pattern = r'^([^ ]+)$'       # allow anything except spaces
        if path == '' or re.match(pattern, path):
            return
        raise ValueError("Invalid path (spaces not allowed):\n'%s'" % path)

    def make_full_path(self, path, name):
        """ Combine path and name to make full path"""
        full_path = (path + "/" + name) if path != '' else name
        # remove any duplicate slashes
        full_path = re.sub(r'//+',r'/', full_path)
        self.validate_path(full_path)
        return full_path
    
    def get_custom_node_info(self, qid, gslash, name, path, parent=None):
        """ gets sdef structure, and if necessary modifies name and path to get
        sdef structure into format needed for creating custom node (group or dataset).
        gslash is '/' if creating a group, '' if creating a dataset.
        parent - parent group if creating node inside (calling from) a group."""
        gqid = qid + gslash
        sdef = self.get_sdef(gqid, self.default_ns)
        if sdef:
            # found id in structure, assume creating pre-defined node in custom location
            id = sdef['id']
            ns = sdef['ns']
            if path == '':
                print "** Error"
                print ("Path must be specified if creating '%s'"
                    " in a custom location using name space '%s'.") % (id, ns)
                traceback.print_stack()
                sys.exit(1)
            sdef['custom'] = True
        else:
            # did not find id in structures.  Assume creating custom node in custom location
            # in this case, name should be empty
            if name != '':
                raise ValueError(("** Error: name is '%s' but should be empty when setting "
                    "custom node '%s'") % (name, qid))
            (ns, id) = self.parse_qid(qid, self.default_ns)
            full_path = self.make_full_path(path, id)
            if parent:
                if full_path and full_path[0] == "/":
                    print ("** Error:  Specified absolute path '%s' when creating node\n"
                        "inside group, with namespace '%s'") % (full_path, ns)
                    traceback.print_stack()
                    sys.exit(1)
                # ok, relative path is specified, make full path using parent
                full_path = self.make_full_path(parent.full_path, full_path)                       
            else:
                # not creating from inside a group.  Require absolute path, or default to __custom location
                if full_path == '' or full_path[0] != "/":
                    if '__custom' not in self.id_lookups[ns]:
                        print ("** Error:  Attempting to make '%s' but path is relative and\n"
                            "'__custom' not specified in '%s' name space locations") % (full_path, ns)
                        print "id_lookups is"
                        pp.pprint(self.id_lookups)
                        traceback.print_stack()
                        sys.exit(1)
                    if len(self.id_lookups[ns]['__custom']) > 1:
                        raise ValueError(("** Error:  '__custom' is specified in more than location "
                            "in namespace '%s'") % ns)             
                    default_custom_path = self.id_lookups[ns]['__custom'].keys()[0]
                    full_path = self.make_full_path(default_custom_path, full_path)
            # split full path back to path and group name
            matchObj = re.match( r'^(.*/)([^/]*)$', full_path)
            if not matchObj:
                print "** Error: Unable to find match pattern for full_path in '%s'" % full_path
                sys.exit(1)
            path = matchObj.group(1).rstrip('/')
            if path == '':
                path = '/'
            id_str = matchObj.group(2)
            # make sdef for custom node.  Has empty definition (df)
            type = 'group' if gslash == '/' else 'dataset'
            sdef = { 'type': type, 'qid': qid, 'id':id_str + gslash, 'ns':ns, 'df': {}, 'custom': True }
            name = ''
        return (sdef, name, path)
            
    def make_custom_group(self, qid, name='', path='', attrs={}):
        """ Creates custom group.
            qid - qualified id of structure or name of group if no matching structure.
                qid is id with optional namespace (e.g. core:<...>).  Path can
                also be specified in id (path and name are combined to produce full path)
            name - name of group in case id specified is in <angle brackets>
            path - specified path of where group should be created.  If not given
                or if relative pateOnly needed if
                location ambiguous
            attrs - attribute values for group that are specified in API call"""
        gslash = "/"
        sdef, name, path = self.get_custom_node_info(qid, gslash, name, path)   
        parent = None  # no parent since this node created from File object (top level)
        grp = Group(self, sdef, name, path, attrs, parent)
        return grp
             
    def set_dataset(self, qid, value, name='', path='', attrs={}, dtype=None, compress=False):
        """ Creates datasets that are in the top level of the definition structures.
            qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
            value - value to store in dataset, or Dataset object (to link to another dataset,
               *OR* a string matching pattern: link:<path> or extlink:<file>,<path>
               to specify respectively a link within this file or an external link.
            name - name of dataset in case name is unspecified (id is in <angle brackets>)
            path - specified path of where dataset should be created.  Only needed if location ambiguous
            attrs - attributes (dictionary of key-values) to assign to dataset
            dtype - if provided, included in call to h5py.create_dataset
            compress - if True, compression provided in call to create_dataset
        """
        sdef = self.get_sdef(qid, self.default_ns, "referenced in set_dataset")
        id = sdef['id']
        ns = sdef['ns']
        path = self.deduce_path(id, ns, path)
        link_info = self.extract_link_info(value, None, Dataset)
        # create the dataset
        parent = None  # no parent since this node created from File object (top level)
        ds = Dataset(self, sdef, name, path, attrs, parent, value, dtype, compress, link_info)
        # print "created dataset, qid=%s, name=%s" % (qid, ds.name)
        return ds
       
    def set_custom_dataset(self, qid, value, name='', path='', attrs={}, dtype=None, compress=False):
        """ Creates custom datasets that are in the top level of the definition structures.
            qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
            name - name of dataset in case name is unspecified (id is in <angle brackets>)
            path - specified path of where dataset should be created if not specified in qid
            attrs - attributes (dictionary of key-values) to assign to dataset
            dtype - if provided, included in call to h5py.create_dataset
            compress - if True, compression provided in call to create_dataset
        """
        gslash = ""
        sdef, name, path = self.get_custom_node_info(qid, gslash, name, path)   
        parent = None  # no parent since this node created from File object (top level)
        ds = Dataset(self, sdef, name, path, attrs, parent, value, dtype, compress)
        return ds    

    def validate_file(self):
        """ Validate that required nodes are present.  This is done by checking
        nodes referenced in id_lookup structure (built from 'locations' section
        of specification language) and also by checking the tree of all nodes
        that are included in the "all_nodes" array. """
        print "\n******"
        print " Done creating file.  Validation messages follow."
        missing_nodes = {'group': [], 'dataset': []}
        custom_nodes = {'group': [], 'dataset': []}
        for ns in self.id_lookups:
            for id in self.id_lookups[ns]:
                for path in self.id_lookups[ns][id]:
                    qty = self.id_lookups[ns][id][path]['qty']
                    type = self.id_lookups[ns][id][path]['type']
                    count = len(self.id_lookups[ns][id][path]['created'])
                    if qty in ('!', '+') and count == 0:
                        missing_nodes[type].append("%s:%s/%s" % (ns, path, id))
        for path, node_list in self.all_nodes.iteritems():
            for root_node in node_list:
                self.validate_nodes(root_node, missing_nodes, custom_nodes)
        self.report_problems(missing_nodes, "missing")
        self.report_problems(custom_nodes, "custom")
        if self.custom_attributes:
            count = len(self.custom_attributes)
            print "%i nodes with custom attributes" % len(self.custom_attributes)
            if count > 20:
                print "Only first 20 shown;"
            names = self.custom_attributes.keys()[0:min(20, count)]
            nlist = []
            for name in names:
                nlist.append(name+ "->" +str(self.custom_attributes[name]))
            print nlist
        else:
            print "No custom attributes.  Good."     
           
    def validate_nodes(self, root_node, missing_nodes, custom_nodes):
        """ Check if node contains all required components or if it is custom."""
        to_check = [root_node]
        while len(to_check) > 0:
            node = to_check.pop(0)
            custom = 'custom' in node.sdef and node.sdef['custom']
            type = node.sdef['type']
            if custom:
                custom_nodes[type].append(node.full_path)
            if type == 'group':
                # check if any nodes required in this group are missing
                for id in node.mstats:
                    qty = node.mstats[id]['qty']
                    type = node.mstats[id]['type']
                    created = node.mstats[id]['created']
                    if not custom and qty in ('!', '+') and len(created) == 0:
                        missing_nodes[type].append("%s/%s" % (node.full_path, id))            
                    # add nodes to list to check
                    to_check.extend(created) 

    def report_problems(self, nodes, problem):
        """ Display nodes that have problems (missing or are custom)"""
        limit = 30
        for type in ('group', 'dataset'):
            count = len(nodes[type])
            if count > 0:
                if count > limit:
                    limit_msg = " (only the first %i shown)" % limit
                    endi = limit
                else:
                    limit_msg = ""
                    endi = count
                types = type + "s" if count > 1 else type
                print "------ %i %s %s%s:" % (count, types, problem, limit_msg)
                print nodes[type][0:endi]
            else:
                print "------ No %s %ss.  Good." % (problem, type)

    def get_node(self, full_path, abort=True):
        """ Returns node at full_path.  If no node at that path then
            either abort (if abort is True) or return None """
        if full_path in self.path2node:
            return self.path2node[full_path]
        elif abort:
            print "Unable to get node for path\n%s" % full_path
            # return None
            traceback.print_stack()
            sys.exit(1)
        else:
            return None

class Node(object):
    """ node (either group or dataset) in created file """
    def __init__(self, file, sdef, name, path, attrs, parent, link_info):
        """ Create node object
        file - file object
        sdef - dict with elements:
            type - 'group' or 'dataset'
            id - id in structures (or parent group) for node
            ns - namespace structure is in
            df - definition of node (dictionary)
        name - name of node in case id is in <angle brackets>
             *OR* another Group object if making link to that group
        path - path of where node should be created
        attrs - attribute values specified in API call creating node.  Either dictionary
            or list of key-values the can be converted to a dictionary.
        parent - parent Group object if this node was made inside another specified group
            None otherwise
        link_info - Either None, or info used to make link.  If linking to internal node,
            contains key "node".  If linking to external file, contains key: "extlink"
            and value is file,path (file, comma, then path).
        """
        self.file = file
        self.sdef = sdef
        id_noslash = sdef['id'].rstrip("/")  # remove trailing slash in case it's a group
        v_id = re.match( r'^<[^>]+>$', id_noslash) # True if variable_id (in < >)
        if type(name) is Group:
            # linking to a group
            self.link_node = name
            # if variable id, use name of target group, otherwise keep name the same
            name = name.name if v_id else id_noslash
        else:
            self.link_node = None
            if v_id:
                if name == '':
                    print "** Error: name for %s '%s' must be specified" % (sdef['type'], id_noslash)
                    traceback.print_stack()
                    sys.exit(1)
            else:
                if name != '':
                    print ("** Error: %s name '%s' is fixed.  Cannot create (or link)"
                        " with name '%s'") % (sdef['type'], id_noslash, name)
                    traceback.print_stack()
                    sys.exit(1)
                else:
                    name = id_noslash              
        self.name = name
        self.path = path
        self.full_path = self.file.make_full_path(path, name)
        self.attrs = self.file.cast_to_dict(attrs)
        self.attributes = {} # for attributes defined in specification language
        self.add_schema_attribute()
        self.parent = parent
        self.link_info = link_info
        self.create_link()   
        self.save_node()
  
    def create_link(self):
        """ If node is being linked to another node, create the link in the hdf5 file"""
        if self.link_info:
            link_type = self.file.options['link_type']
            if 'node' in self.link_info:
                target_path = self.link_info['node'].full_path
                if link_type == 'string':
                    # create string dataset containing link path
                    #- self.file.file_pointer.create_dataset(self.full_path, data="h5link:/" + target_path)
                    self.file.create_dataset(self.full_path, data="h5link:/" + target_path)
                elif link_type == 'hard':
                    # create hard link to target.  This implemented by h5py "Softlink".  Not sure why.
                    #- self.file.file_pointer[self.full_path] = h5py.SoftLink(target_path)
                    self.file.create_softlink(self.full_path, target_path)
                else:               
                    raise Exception('Invalid option value for link_type (%s)' % link_type)
            elif 'extlink' in self.link_info:
                file, path = self.link_info['extlink']
                # link to external file
                if link_type == 'string':
                    # create string dataset containing link path
                    target_path = "%s,%s" % (file, path)
                    #- self.file.file_pointer.create_dataset(self.full_path, data="h5extlink:/" + target_path)
                    self.file.create_dataset(self.full_path, data="h5extlink:/" + target_path)
                elif link_type == 'hard':
                    # create link to external file
                    #- self.file.file_pointer[self.full_path] =  h5py.ExternalLink(file,path)
                    self.file.create_external_link(self.full_path, file, path)               
                else:
                    raise Exception('Invalid option value for link_type (%s)' % link_type)
            else:
                raise SystemError("** Error: invalid key in link_info %s" % self.link_info)
         
    def save_node(self):
        """ Save newly created node in id_lookups (if node is defined structure created
        at top level) and in "all_nodes".  Nodes stored in both of these are later used
        for validating that required nodes are present.
        Also save in 'path2node' - that's used for file object get_node method"""
        # save node in path2node
        if self.full_path in self.file.path2node:
            print "** Error, created node with path twice:\n%s" % self.full_path
            traceback.print_stack()
            sys.exit(1)
        self.file.path2node[self.full_path] = self            
        # save node in id_lookups
        id = self.sdef['id']
        ns = self.sdef['ns']
        type = self.sdef['type']
        custom = 'custom' in self.sdef and self.sdef['custom']
        if self.parent is None and self.sdef['df'] and not custom:
            # structure (not custom) created at top level, save in id_lookups
            if id not in self.file.id_lookups[ns]:
                print "** Error: Unable to find id '%s' in id_lookups when saving node" % id
                traceback.print_stack()
                sys.exit(1)
            if self.path not in self.file.id_lookups[ns][id]:
                print ("** Error: Unable to find path '%s' in id_lookups when"
                    " saving node %s") % (self.path, id)
                print "self.sdef['df'] is:"
                pp.pprint (self.sdef['df'])
                traceback.print_stack()
                sys.exit(1)
            self.file.id_lookups[ns][id][self.path]['created'].append(self)
        # save node in all_nodes, either at top level (if no parent) or inside
        # mstats structure of parent node
        if self.parent is None:
            if self.path in self.file.all_nodes:
                self.file.all_nodes[self.path].append(self)
            else:
                self.file.all_nodes[self.path] = [self, ]
        else:
            if id not in self.parent.mstats:
                if custom:
                    # custom node created, add id to mstats of parent
                    self.parent.mstats[id] = { 'df': {}, 'type':type, 'ns': ns,
                        'created': [ self, ], 'qty':'?' }
                else:
                    print "** Error: Unable to find key '%s' in parent mstats" % id
                    print "self.parent.mstats is"
                    pp.pprint (self.parent.mstats)
                    traceback.print_stack()
                    sys.exit(1)
            else:          
                # append node to parent created mstats                   
                self.parent.mstats[id]['created'].append(self)

    def add_schema_attribute(self):
        """ Add in attribute specifying id in schema or custom if requested in options"""
        schema_id = self.file.options['schema_id_attr']
        if self.sdef['df'] and self.file.options['include_schema_id']:
            # Normal defined entity
            ns = self.sdef['ns']
            id = self.sdef['id']
            schema = ns + ":" + id
            self.attributes[schema_id] = {'value': schema}
        elif self.file.options['flag_custom_nodes']:
            self.attributes[schema_id] = {'value': 'custom'}

    def merge_attrs(self):
        """ Merge attributes specified by 'attrs=' option when creating node into
        attributes defined in specification language.  Save values using key 'nv'
        (stands for 'new_value')"""
        for aid in self.attrs:
            new_val = self.attrs[aid]
            if aid in self.attributes:
                if ('value' in self.attributes[aid] and
                    self.attributes[aid]['value'] != new_val):
                    pass
                    # print "Updating attribute %s[%s] %s -> %s" % (
                    #     self.name, aid, self.attributes[aid]['value'], new_val)
            else:
                # print "** Warning: non-declaired attribute %s['%s'] set to:\n'%s'" % (
                #    self.name, aid, new_val)
                self.remember_custom_attribute(self.name, aid, new_val)
                self.attributes[aid] = {}
            self.attributes[aid]['nv'] = new_val
         
    def set_attr_values(self):
        """ set attribute values of hdf5 node.  Values to set are stored in
        self.attributes, either in the values key (for values specified in
        the specification language or in the 'nv' key (for values specified
        via the API
        """
        ats = self.attributes  # convenient short name
        for aid in ats:
            value = ats[aid]['nv'] if 'nv' in ats[aid] else (
                ats[aid]['value'] if 'value' in ats[aid] else None)
            if value is not None:
#                 self.h5node.attrs[aid] = value
                #- self.file.file_pointer[self.full_path].attrs[aid] = value
                self.file.set_attribute(self.full_path, aid, value)
                #- self.file.h5save_attribute(self.full_path, aid, value)
                #- self.file.h5commands.append("set attribute(%s:%s)-%s" % (self.full_path,
                #-     aid, value))
                
    def set_attr(self, aid, value, custom=False):
        """ Set attribute with key aid to value 'value' """
        if aid not in self.attributes and not custom:
            # print "** Warning: non-declaired attribute %s['%s'] set to:\n'%s'" % (
            #    self.name, aid, value)
            self.remember_custom_attribute(self.name, aid, value)
            self.attributes[aid] = {}
        else:
            # TODO: validate data_type
            pass
        self.attributes[aid]['nv'] = value
        # self.h5node.attrs[aid] = value
        #- self.file.file_pointer[self.full_path].attrs[aid] = value
        self.file.set_attribute(self.full_path, aid, value)
        
    def remember_custom_attribute(self, node_name, aid, value):
        """ save custom attribute for later reporting """
        if node_name in self.file.custom_attributes:
            self.file.custom_attributes[node_name][aid]=value
        else:
            self.file.custom_attributes[node_name] = { aid: value}            

    def merge_attribute_defs(self, dest, source, changes = {}):
        """ Merge attribute definitions.  This used for merges, 'parent_attributes',
        and includes where attributes are specified.  Any changes to values are
        stored in "changes" as a dictionary giving old and new values for each changed
        attribute. The changes are used to update node attribute values in the hdf5 file
        for the case of the parent_attributes merge.  If attribute key already
        exist and merged attribute value starts with "+", append value, separated by
        a comma."""
        # print "in merge_attribute_defs, dest ="
        # pp.pprint(dest)
        # print "source ="
        # pp.pprint(source)
        for aid in source.keys():
            if aid not in dest.keys():
                # copy attribute, then check for append
                dest[aid] = copy.deepcopy(source[aid])
                if 'value' in dest[aid]:
                    if type(dest[aid]['value']) is str and dest[aid]['value'][0]=='+':
                        dest[aid]['value'] = dest[aid]['value'].lstrip('+')
                    changes[aid] = dest[aid]['value']
                continue               
            if 'value' not in dest[aid]:
                if 'value' in source[aid]:
                    dest[aid]['value'] = source[aid]['value']
                    if (type(dest[aid]['value']) is str and dest[aid]['value'][0] == '+'):
                        dest[aid]['value'] = dest[aid]['value'].lstrip('+')                              
                    changes[aid] = dest[aid]['value']
                    continue
                else:
                    print ("** Error, merging attribute '%s' but value not specified in source"
                        " or destination") % aid
                    traceback.print_stack()
                    sys.exit(1)                
            else:
                if 'value' in source[aid]:                       
                    # value given in both source and destination
                    self.append_or_replace(dest[aid], source[aid], 'value', "attribute %s" % aid)
                    changes[aid] = dest[aid]['value']  # save changed value
                else:
                    print ("** Warning, node at:\n%s\nmerging attribute '%s'" 
                        " but value to merge not specified.") % (self.full_path, aid)
                    print "source attributes:"
                    pp.pprint(source)
                    print "dest attributes:"
                    pp.pprint(dest)                         
  
    def append_or_replace(self, dest, source, key, ident):
        """ dest and source are both dictionaries with common key 'key'.  If both
        values of key are type str, and source[key] starts with "+", append the value
        to dest[key], otherwise replace dest[key].  This is to implement appends
        or replacing in 'include' directives.  ident is descriptive identifier
        used for warning or error message. """
        prev_val = dest[key] 
        new_val = source[key]
        if (type(prev_val) is str and type(new_val) is str and new_val[0] == '+'):
            # need to append
            new_val = new_val.lstrip('+')
            if prev_val != '':
                dest[key] = prev_val + "," + new_val
                return
		# replace previous value by new value
		# first do some validation
		if type(prev_val) != type(new_val):
			print ("** Error, type mismatch when setting %s, previous_type=%s,"
				" new type=%s; previous value=") %(ident, type(prev_val), type(val))
			pp.pprint(prev_val)
			print "New value="
			pp.pprint(new_val)
			traceback.print_stack()
			sys.exit(1)
		if not(type(new_val) is str or type(new_val) is int or type(new_val) is float
			or type(new_val) is long):
			print "** Error, invalid type (%s) assignd to %s" % (type(new_val), ident)
			print "Should be string, int or float.  Value is:"
			pp.pprint(new_val)
			traceback.print_stack()
			sys.exit(1)
		# TODO: check for data_type matching value type
		dest[key] = new_val

             
class Dataset(Node):
    def __init__(self, file, sdef, name, path, attrs, parent, value, dtype, compress, link_info=None):
        """ Create Dataset object
        file - file object
        sdef - dict with elements:
            type - 'group' or 'dataset'
            id - id in structures (or parent group) for node
            id_noslash - id without trailing slash (in case is a group)
            ns - namespace structure is in
            df - definition of node (dictionary)
        name - name of node in case id is in <angle brackets>
        path - path of where node should be created
        attrs - dictionary of attribute values specified in API call creating node
        parent - parent group if this node was made inside another specified group
            None otherwise
        value - value to store in dataset *OR* a Datasets object to make a link to
            an internal Dataset, *OR* a string matching either of the patterns:
            h5link:<path> or h5extlink:<file>,<path>
            to specify respectively a link within this file or an external link.
        dtype - if specified, datatype used in call to h5py.create_dataset
        compress - True if should do compression.  used in call to hfpy.create_dataset
        link_info - Either None, or info used to make link.  If linking to internal node,
            contains key "node".  If linking to external file, contains key: "extlink"
            and value is file,path (file, comma, then path).  
        """
        super(Dataset, self).__init__(file, sdef, name, path, attrs, parent, link_info)
        # print "Creating Dataset, sdef="
        # pp.pprint(sdef)
        if 'attributes' in self.sdef['df']:
            self.attributes = copy.deepcopy(self.sdef['df']['attributes'])
            # del self.sdef['df']['attributes']  # if do this, no need to check for attributes in mk_dsinfo
            # print "found attributes:"
        # else:
        #     print "did not find attributes:"
        # pp.pprint(self.attributes)
        # if self.sdef['df']:
        self.dsinfo = self.mk_dsinfo(value)
        self.merge_attribute_defs(self.attributes, self.dsinfo['atags'])
        # else:
            # definition empty, must be custom dataset
        #    self.dsinfo = {}
        self.merge_attrs()
        if self.link_info:
            # this dataset set to link to another.  Already done in Node.  Nothing to do here
            pass
        else:
            # creating new dataset (normally done)
            self.link_node = None
            # compress = "gzip" if compress else None
            # self.h5node = self.h5parent.create_dataset(self.name, data=value,
            #    dtype=dtype, compression=compress)
            #- self.file.file_pointer.create_dataset(self.full_path, data=value,
            #-     dtype=dtype, compression=compress)
            self.file.create_dataset(self.full_path, data=value, dtype=dtype,
                compress=compress)
            # self.file.h5commands.append("create_dataset(%s, %s)" % (self.full_path, value))
            # if dtype:
            #    self.h5node = self.h5parent.create_dataset(self.name, data=value, dtype=dtype)
            # else:  # should find out what default value for dtype used in h5py and use that, combine these
            #    self.h5node = self.h5parent.create_dataset(self.name, data=value)
        self.set_attr_values()


    def ds_atags(self):
        """ Returns tags in dataset definition that are mapped to attributes in
        hdf5 file.  Tags are in JSON like structure, giving the description and
        mapping (new name in attributes) of each tag."""
        atags = {
            'unit': {
                'atname': 'unit',
                'data_type': 'text',
                'description': 'Unit of measure for values in data'},
            'description': {
                'atname': 'description',
                'data_type': 'text',
                'description': 'Human readable description of data'},
            'comments': {
                'atname': 'comments',
                'data_type': 'text',
                'description': 'Comments about the data set'},
            'references': {
                'atname': 'references',
                'data_type': 'text',
                'description': 'path to group, diminsion index or field being referenced'},
            'semantic_type': {
                'atname': 'semantic_type',
                'data_type': 'text',
                'description': 'Semantic type of data stored'},
            'scale': {
                'atname': 'conversion',
                'data_type': 'float',
                'description': 'Scale factor to convert stored values to units of measure'},
        }
        return atags

    def mk_dsinfo(self, val):
        """ Make 'dsinfo' - dataset info structure.  This structure is saved and
        will later be used to validate relationship created by common dimensions and
        by references.  val (parameter) is the value being assigned to the dataset.
        The returned structure 'dsinfo' contains:
            dimensions - list of dimensions
            dimdef - definition of each dimension
                scope - local/global (local is local to containing folder)
                type - type of dimension (set, step, structure)
                parts - components of structure dimension
                len - actual length of dimension in saved dataset
            atags - values for special tags that are automatically mapped to
                attributes.  These are specified by structure defined in ds_atags.
                values are returned in a structure used for attributes which
                includes a data_type, value and description.
            dtype - data type
        """
        dsinfo = {}
        atags = self.ds_atags()
        # dsinfo['description'] = ''
        dsinfo['dimensions'] = {}
        dsinfo['dimdef'] = {}
        # dsinfo['ref'] = ''
        dsinfo['dtype'] = ''     # type actually present in val, e.g. 'int32'
        dsinfo['data_type'] = '' # type specified in definition, e.g. int, float, number, text
        dsinfo['shape'] = ''     # shape of array or string 'scalar'
        # dsinfo['unit'] = ''
        # dsinfo['semantic_type'] = '' 
        dsinfo['atags'] = {}
        df = self.sdef['df']
        # save all referenced atags
        for tag in atags:
            if tag in df and tag != 'description':  # don't save descriptions by default
                dsinfo['atags'][atags[tag]['atname']] = {
                    'data_type': atags[tag]['data_type'],
                    'description': atags[tag]['description'],
                    'value': df[tag],}      
        if self.link_info:
            # setting this dataset to another dataset by a link
            # get previously saved info about dataset linking to
            # import pdb; pdb.set_trace()
            if 'node' in self.link_info:
                # linking to node in current file
                node = self.link_info['node']
                dsinfo['shape'] = node.dsinfo['shape']
                dsinfo['dtype'] = node.dsinfo['dtype']
            elif 'extlink' in self.link_info:
                # linking to external file.  Cannot do validation of datatype
                # leave dsinfo['shape'] and dsinfo['dtype'] empty to indicate both are unknown
                pass
            else:
                raise SystemError("** Error: invalid key in link_info %s" % self.link_info)
        else:
            dsinfo['dtype'], dsinfo['shape'] = self.get_dtype_and_shape(val)
        if 'dimensions' in df.keys():
            dsinfo['dimensions'] = df['dimensions']
            if dsinfo['shape'] == 'scalar':
                print ("** Warning, expecting array value because dimensions defined"
                    " for dataset, but value assigned is scalar with type '%s'."
                    " Dimensions are:" % dsinfo['dtype'])
                # pp.pprint(df['dimensions'])
                # print('Scalar value is:')
                # pp.pprint(val)
                # traceback.print_stack()
                # sys.exit(1)
            else:             
				if dsinfo['shape'] and len(dsinfo['dimensions']) != len(dsinfo['shape']):
					print ("** Warning, %i dimensions defined in data set, but number of"
						" dimensions in value assigned is %i.  Shape is:") % (
						len(dsinfo['dimensions']), len(dsinfo['shape']))
					pp.pprint(dsinfo['shape']);
					# print "if dimensions are Nx1 and using MatLab, consider transpose (') to make 1xN"; 
					# traceback.print_stack()
					# sys.exit(1)
				else:               
					# check for any dimensions defined in dataset
					i = 0
					for dim in dsinfo['dimensions']:
						if dim.endswith('^'):
							scope = 'global'
						else:
							scope = 'local'
						dsinfo['dimdef'][dim] = {'scope':scope, 'len': dsinfo['shape'][i]}
						if dim in df.keys():
							dsinfo['dimdef'][dim].update(df[dim])
						i = i + 1
        if 'attributes' in df.keys():
            pass  # do nothing here, attributes moved to self.attributes     
        if 'data_type' in df.keys():
            dsinfo['data_type'] = df['data_type']
        else:
            if not df:
                # nothing specified for dataset definition.  Must be custom dataset
                # (being created by "set_custom_dataset").  Do no validation
                return dsinfo
            print "** Error: 'data_type' not specified in dataset definition"
            print "definition is:"
            pp.pprint(df)
            traceback.print_stack()
            sys.exit(1)
        # Now, some simple validation
        if dsinfo['dtype'] and not valid_dtype(dsinfo['data_type'], dsinfo['dtype']):
            raise ValueError(("** Error, expecting type '%s' assinged to dataset, but"
                    " value being stored is type '%s'") % (dsinfo['data_type'], dsinfo['dtype']))     
        # make sure everything defined in dataset definition is valid
        for key in df.keys():
            if (key in ('dimensions', 'data_type', 'attributes') or
                key in atags or key in dsinfo['dimensions']):
                continue
            print "** Error, invalid key (%s) in dataset definition" % key
            print "dataset definition is:"
            pp.pprint(df)
            traceback.print_stack()
            sys.exit(1)              
        return dsinfo                                 

    def get_dtype_and_shape(self, val):
        """ Return data type and shape of value val, as a tuple"""
        # get type of object as string
        val_type = str(type(val))
        matchObj = re.match(r"<(type|class) '([^']+)'>", val_type)
        if not matchObj:
            raise SystemError("** Error: Unable to find type in %s" % val_type)
        val_type = matchObj.group(2)
        # check for "value_info" passed in through calling script (e.g. Matlab)
        # if so, then type and shape is given in val (it does not contain the actual data
        # to store.
        if val_type == 'str' and self.file.options['storage_method'] == 'none':
            # value_info string looks like the following:
            # value_info: type="float", shape="[5]"  *OR*
            # value_info: type="float", shape="[scalar]"
            matchObj = re.match(r'^value_info: type="([^"]+)", shape="\[([^\]]+)\]"$', val)
            if matchObj:
                dtype = matchObj.group(1)
                shape = matchObj.group(2)
                if shape != 'scalar':
                    # convert dimensions from string (like '4 5') to integer list
                    shape = map(int, shape.split())
                return (dtype, shape)
        # check data shape and type            
        if val_type in ('str', 'int', 'float', 'long', 'unicode', 'bool'):
            shape = "scalar"
            dtype = val_type
        elif val_type == 'list':
            # convert from list to np array to get shape
            a = np.array(val)
            shape = a.shape
            dtype = str(a.dtype)
            # print "found list, dtype is %s, shape is:" % dtype
            # pp.pprint (shape)
        elif 'numpy' in val_type or type(val) is h5py._hl.dataset.Dataset:             
            shape = val.shape
            dtype = str(val.dtype)
            # print "found numpy or h5py dataset, dtype is %s", dtype
        else:
            print "** Error, unable to determine shape of value assiged to dataset"
            print "value type is '%s'" % val_type
            traceback.print_stack()
            sys.exit(1)
        return (dtype, shape)

def valid_dtype(expected, found):
    """ Return True if found data type is consistent with expected data type.
    found - data type generated by python dtype converted to a string.
    expected - one of: 'bool', 'byte', 'text', 'number', 'int', 'float' or 'any' """
    if expected not in ('bool', 'byte', 'text', 'number', 'int', 'float', 'any'):
       raise SystemError(("** Error: invalid value (%s) in definition file "
          "for expected data type") % expected)
    if expected == 'any':
        return True
    if found in ('str', 'unicode') or re.match( r'^\|S\d+$', found) or 'byte' in found:
        # print "found dtype '%s', interpreting as string" % dtype
        dtype = 'text'
    elif 'bool' in found:
        dtype = 'bool'
    elif 'int' in found or 'long' in found:
        dtype = 'int'
    elif 'float' in found or 'double' in found:
        dtype = 'float'
    else:
        raise ValueError(("** Error: unable to recognize data type (%s) for validation."
            "expecting compatable with '%s'") % (found, expected))
    valid = (dtype == expected or (dtype in ('int', 'float', 'bool', ) and expected == 'number'))
    return valid
    
    
class Group(Node):
    """ hdf5 group object """
    def __init__(self, file, sdef, name, path, attrs, parent, link_info=None):
        """ Create group object
        file - file object
        sdef - dict with elements:
            type - 'group' or 'dataset'
            id - id in structures (or parent group) for node
            id_noslash - id without trailing slash (in case is a group)
            ns - namespace structure is in
            df - definition of node (dictionary)
        name - name of node in case id is in <angle brackets>, OR other Group
            object if making link to that group, OR pattern for linking.  See link (below)
        path - path of where node should be created
        attrs - attribute values specified when creating group
        parent - parent group if this node was made inside another specified group
            None otherwise
        link_info - Either None, or info to to make link.  If linking to internal node,
            contains key "node".  If linking to external file, contains key: "extlink"
            and value is file,path (file, comma, then path). 
        """
        super(Group, self).__init__(file, sdef, name, path, attrs, parent, link_info)
        self.description = []
        self.parent_attributes = {}
        self.get_expanded_def_and_includes()
        # print "after get_expanded_def_and_includes, includes="
        # pp.pprint(self.includes)
        self.get_member_stats()
        self.add_parent_attributes()
        self.merge_attrs()
        if self.link_info:
            # this group is linking to another.  Already done in Node class.  Nothing to do here
            pass
        else:
#             self.h5node = self.h5parent.create_group(self.name)
            #- self.file.file_pointer.create_group(self.full_path)
            #- self.file.h5commands.append("create_group(%s)" % self.full_path)
            self.file.create_group(self.full_path)
        # add attribute values to node
        self.set_attr_values()


    def add_parent_attributes(self):
        """ Add any parent attributes to parent group"""
        if len(self.parent_attributes) == 0:
            return
        dest = self.parent.attributes
        source = self.parent_attributes
        changes = {}
        self.merge_attribute_defs(dest, source, changes)
        for aid, value in changes.iteritems():
#             self.parent.h5node.attrs[aid] = value
            # may need modifying for MATLAB
            #- if self.path not in self.file.file_pointer:
            if self.file.get_node(self.path, abort=False) is None:
                # create parent node since it does not exist
                print "trying to set parent attributes on non-registered parent node:"
                print "Non-registered parent node is: '%s'", self.path
                traceback.print_stack()
                sys.exit(1)
            #- self.file.file_pointer[self.path].attrs[aid] = value
            self.file.set_attribute(self.path, aid, value)
               
#     def old_add_attributes(self, node, attributes):
#         """ Add attributes to node.  If attribute key already exist and attribute
#             value starts with "+", append value, separated by a comma."""
#         print "in add_attributes, attributes ="
#         pp.pprint(attributes)
#         for key, val in attributes.items():
#             if key in node.attrs.keys():
#                 prev_val = node.attrs[key]
#                 if type(prev_val) != type(val):
#                     print ("** Error, type mismatch when setting attribute %s "
#                         "previous_type=%s, new type=%s; previous value=") %(key, type(prev_val), type(val))
#                     pp.pprint(prev_val)
#                     print "New value="
#                     pp.pprint(val)
#                     traceback.print_stack()
#                     sys.exit(1)
#                 if type(val) is str and (val[0] == "+" or prev_val == ''):
#                         node.attrs[key] = node.attrs[key] + "," + val.lstrip("+")
#                 else:
#                     print ("** Error, attempting to set attribute '%s' to '%s', but"
#                         " it already has value '%s'") % (key, str(val), str(pre_val))
#                     traceback.print_stack()
#                     sys.exit(1)
#             elif type(val) is str or type(val) is int or type(val) is float or type(val) is long:
#                 node.attrs[key] = val
#             else:
#                 print "** Error, invalid type (%s) assignd to attribute %s" % (type(val), key)
#                 print "Should be string, int or float.  Value is:"
#                 pp.pprint(val)
#                 traceback.print_stack()
#                 sys.exit(1)
                                
    def get_expanded_def_and_includes(self):
        """ Process any 'merge', 'parent_attribute' or 'description' entities.
            Save copy of definition with merges done in self.expanded_def
            Save all includes in self.includes"""
        self.expanded_def = {}
        self.includes = {}
        if 'merge' in self.sdef['df'].keys():
            self.process_merge(self.expanded_def, self.sdef['df']['merge'], self.includes)
        self.merge_def(self.expanded_def, self.sdef, self.includes)
        # merge any attributes to self.attributes for later processing
        if 'attributes' in self.expanded_def:
           self.attributes.update(self.expanded_def['attributes'])
           del self.expanded_def['attributes']
        
    def get_member_stats(self):
        """Build dictionary mapping key for each group member to information about the member.
           Also processes includes.  Save in self.mstats """
        self.mstats = {}
        # add in members from expanded_def (which includes any merges)
        for qid in self.expanded_def.keys():
            # check for trailing quantity specifier (!, *, +, ?).  Not for name space.
            # ! - required (default), * - 0 or more, + - 1 or more, ? - 0 or 1
            id, qty = self.file.parse_qty(qid, "!")
            if id in self.mstats.keys():
                print "** Error, duplicate (%s) id in group" % id
                traceback.print_stack()
                sys.exit(1)
            type = 'group' if id.endswith('/') else 'dataset'
            self.mstats[id] = { 'ns': self.sdef['ns'], 'qty': qty,
                'df': self.expanded_def[qid], 'created': [], 'type': type }
        # add in members from any includes
        # print "** processing includes"
        for qidq in self.includes:
            qid, qty = self.file.parse_qty(qidq, "!")
            # print "processing include", qid
            sdef = self.file.get_sdef(qid, self.sdef['ns'], "Referenced in include")
            # print "obtained sdef:"
            # pp.pprint(sdef)
            modifiers = self.includes[qidq]
            if len(modifiers) > 0:
                # need to incorporate modifications to definition of included child members
                df = copy.deepcopy(sdef['df'])
                # self.modify(df, modifiers)
                self.merge(df, modifiers)  # merges modifiers into definition
                # print "df after merging modifiers:"
            else:
                df = sdef['df']
                # print "df after copy:"
            id = sdef['id']
            type = sdef['type']
            # pp.pprint(df)
            # qty = '!'  # assume includes are required
            if id in self.mstats.keys():
                print "** Error, duplicate (%s) id in group, referenced by include" % id
                traceback.print_stack()
                sys.exit(1)
            self.mstats[id] = { 'ns': self.sdef['ns'], 'qty': qty,
                'df': df, 'created': [], 'type': type }
        # print "after processing all includes, mstats is:"
        # pp.pprint(self.mstats)

        
    def display(self):
        """ Displays information about group (used for debugging)"""
        print "\n\n***********************\n"
        print "Info about group %s, name=%s, path=%s" % (self.sdef['id'], 
            self.name, self.path)
        print "sdef="
        pp.pprint(self.sdef)
        print "expanded_def="
        pp.pprint (self.expanded_def)
        print "includes="
        pp.pprint (self.includes)
        print "parent_attributes="
        pp.pprint (self.parent_attributes)
        print "attributes="
        pp.pprint (self.attributes)
        print "mstats="
        pp.pprint (self.mstats)
                             
    def process_merge(self, expanded_def, initial_to_merge, to_include):
        all_to_merge = self.find_all_merge(initial_to_merge)
        for qid in all_to_merge:
            # print "-- process merge, qud=", qid
            sdef = self.file.get_sdef(qid, self.sdef['ns'], "Referenced in merge")
            self.merge_def(expanded_def, sdef, to_include)
    
    def find_all_merge(self, initial_to_merge):
        """ Builds list of all structures to be merged.
            Includes merges containing a merge """
        to_check = copy.copy(initial_to_merge)
        checked = []
        while len(to_check) > 0:
            qid = to_check.pop(0)
            if qid in checked:
                continue
            sdef = self.file.get_sdef(qid, self.sdef['ns'], "Referenced in merge")
            if 'merge' in sdef['df'].keys():
                to_check.extend(sdef['df']['merge'])
            checked.append(qid)
        return checked
        
    def merge_def(self, expanded_def, sdef, to_include = {}):
        """ Merge structure defined by sdef into expanded_def.  Also
            Also sets to_include to set of structures to include. """
        for id in sdef['df'].keys():
            if (((id == 'description' and type(sdef['df'][id]) is str)
                and '_description' not in sdef['df'].keys()) or id == '_description'):
                # append this description to any other descriptions specified by previous merge
                description = "%s:%s- %s" % (sdef['ns'], sdef['id'], sdef['df'][id])
                self.description.append(description)
                continue
            if id == 'merge':
                continue
            # if id == 'attributes':
            #     self.attributes.update(sdef['df'][id])
            #    continue
            if id == 'parent_attributes':
                self.parent_attributes.update(sdef['df'][id])
                continue
            if id == 'include':
                # save includes for processing later
                # print "in merge_def, found include:"
                # pp.pprint(sdef['df'][id])
                to_include.update(sdef['df'][id])
                continue
            if id in expanded_def.keys():
                # means id from previous merge conflicts
                if id == 'attributes':
                    self.merge_attribute_defs(expanded_def[id], sdef['df'][id])
                # if value for both are dictionaries, try recursive merge
                elif isinstance(expanded_def[id], dict) and isinstance(sdef['df'][id], dict):
                    # print "conflicting key (%s) in merge" % id
                    # print "attempting to recursively merge expanded_def['%s]:" % id
                    # pp.pprint(expanded_def[id])
                    # print "with sdef['df']['%s']:" % id
                    # pp.pprint(sdef['df'][id])
                    self.merge(expanded_def[id], sdef['df'][id])
                else:
                    print "** Error"
                    print "Conflicting key (%s) when merging '%s' when doing" % (id, sdef['id'])
                    print "make_group(%s, %s, path=%s)" % (self.sdef['id'], self.name, self.path)
                    print "expanded_def is:"
                    pp.pprint(expanded_def)
                    print "sdef is:"
                    pp.pprint(sdef)
                    traceback.print_stack()
                    sys.exit(1)
            else:
                # no conflict, just copy definition for id
                # deep copy so future merges do not change original
                expanded_def[id] = copy.deepcopy(sdef['df'][id])
            
    def merge(self, a, b, path=None):
        """merges b into a
        from: http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
        """
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    if key == 'attributes':
                        self.merge_attribute_defs(b, a)
                    else:
                        self.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
                    self.append_or_replace(a,b,key, '/'.join(path + [str(key)]));
            else:
                a[key] = b[key]
        return a
                        
    def make_group(self, id, name='', attrs={}, link='', abort=True ):
        """ Create a new group inside the current group.
        id - identifier of group
        name - name of group in case name is not specified by id (id is in <angle brackets>)
            *OR* Group node linking to
            *OR* pattern specifying a link: link:path or extlink:file,path
        attrs - attribute values for group that are specified in API call
        link - specified link, of form link:path or extlink:file,path.  Only needed
            if name must be used to specify local name of group
        abort - If group already exists, abort if abort is True, otherwise return previously
            existing group."""           
        gid = id + "/"
        sgd = self.get_sgd(gid, name)
        path = self.full_path
        link_info = self.file.extract_link_info(name, link, Group)
        if not abort:
            # id = sgd['id'].rstrip('/')  # not sure if need this
            grp = self.file.get_existing_group(path, id, name)
            if grp:
                return grp
        grp = Group(self.file, sgd, name, path, attrs, self, link_info)
        # self.mstats[gid]['created'].append(grp)
        return grp
   
    def make_custom_group(self, qid, name='', path='', attrs={}):
        """ Creates custom group.
            qid - qualified id of structure or name of group if no matching structure.
                qid is id with optional namespace (e.g. core:<...>).  Path can
                also be specified in id (path and name are combined to produce full path)
            name - name of group in case id specified is in <angle brackets>
            path - specified path of where group should be created.  If not given
                or if relative path.  Only needed if location ambiguous
            attrs - attribute values for group that are specified in API call"""
        gslash = "/"
        parent = self
        sdef, name, path = self.file.get_custom_node_info(qid, gslash, name, path, parent)   
        grp = Group(self.file, sdef, name, path, attrs, parent)
        return grp
        
    def get_node(self, path, abort=True):
        """ returns node inside current group.  If node not present, return None,
        (if abort == False), otherwise return True """
        if path.startswith('/'):
            return self.file.get_node(path, abort)
        else:
            return self.file.get_node(self.full_path + "/" + path, abort)
                
        
    def get_sgd(self, id, name):
        """ Get definition of group or dataset being created inside a group)"""
        # check if id exists in group definition
        if id in self.mstats.keys() and 'df' in self.mstats[id].keys():
            # print "id %s in mstats" % id
            type = 'group' if id.endswith('/') else 'dataset'
            sgd = {'id': id, 'type': type, 'ns':self.sdef['ns'], 'df': self.mstats[id]['df'],}
            # print "found definition for %s in mstats, mstats=" % id
            # pp.pprint(self.mstats)
            return sgd
        else:
            # see if parent group is specified in locations; if so, check for id in 
            # locations list of members of parent group.  Example for nwb format is are
            # "UnitTimes/" inside <module>/.  <module> is parent group
            pid = self.sdef['id']  # parent id, e.g. "<module>"
            ns = self.sdef['ns']
            if pid in self.file.ddef[ns]['locations']:
                if id in self.file.ddef[ns]['locations'][pid]:
                    type = 'group' if id.endswith('/') else 'dataset'
                    # add id to mstats so can register creation of group
                    self.mstats[id] = {'ns':ns, 'created': [], 'qty': '+', 
                        'type': type} # todo: jeff, need to check df
                    sgd = self.file.get_sdef(id, ns, "referenced in make_subgroup")
                    # print "id %s in %s location ns %s structures" % (id, pid, ns)
                    # example output: id UnitTimes/ in <module>/ location ns core structures
                    # traceback.print_stack()
                    return sgd
                else:
                    print "found parent %s in locations, but %s not inside" % (pid, id)
                    print "locations contains:"
                    pp.pprint(self.file.ddef[ns]['locations'][pid])
            else:
                print "did not find parent %s in locations for namespace %s" % (pid, ns)
        print "** Error, attempting to create '%s' (name='%s') inside group:" % (id, name)
        print self.full_path
        print "But '%s' is not a member of the structure for the group" % id
        print "Valid options are:", self.mstats.keys()
        # print "Extra information (for debugging):  Unable to find definition for node %s" % id
        # print "mstats="
        # pp.pprint(self.mstats)
        traceback.print_stack()
        sys.exit(1)       

        
    def set_dataset(self, id, value, name='', attrs={}, dtype=None, compress=False):
        """ Create dataset inside the current group.
            id - id of dataset.
            name - name of dataset in case id is in <angle brackets>
            value - value to store in dataset, or Dataset object (to link to another dataset,
                *OR* a string matching pattern: link:<path> or extlink:<file>,<path>
                *OR* a string matching pattern: link:<path> or extlink:<file>,<path>
                to specify respectively a link within this file or an external link.
            path - specified path of where dataset should be created.  Only needed if location ambiguous
            attrs = attributes specified for dataset
            dtype - if provided, included in call to h5py.create_dataset
            compress - if True, compression provided in call to create_dataset
        """
        sgd = self.get_sgd(id, name)
        link_info = self.file.extract_link_info(value, None, Dataset)
        path = self.full_path
        ds = Dataset(self.file, sgd, name, path, attrs, self, value, dtype, compress, link_info)
        # self.mstats[id]['created'].append(ds) 
        return ds 

       
    def set_custom_dataset(self, qid, value, name='', path='', attrs={}, dtype=None, compress=False):
        """ Creates custom dataset that is inside the current group.
            qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
            name - name of dataset in case name is unspecified (id is in <angle brackets>)
            path - specified path of where dataset should be created if not specified in qid
            attrs - attributes (dictionary of key-values) to assign to dataset
            dtype - if provided, included in call to h5py.create_dataset
            compress - if True, compression provided in call to create_dataset
        """
        gslash = ""
        parent = self
        sdef, name, path = self.file.get_custom_node_info(qid, gslash, name, path, parent)   
        ds = Dataset(self.file, sdef, name, path, attrs, parent, value, dtype, compress)
        return ds    

