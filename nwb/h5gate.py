# Code to manage creation and perform validation of hdf5 files using
# format specification written in the specification language.
# This was developed for the NWB format, but can be used for other
# file formats based on HDF5.

import traceback
# import h5py
# import numpy as np
import sys
import re
import copy
import os.path
import imp
import ast
import shutil
import array
import find_links
import combine_messages as cm

import pprint
pp = pprint.PrettyPrinter(indent=4)

class File(object):
    """ hdf5 file """
    def __init__(self, fname, spec_files, default_ns="core", options=[]):
        """ Created file.
        fname - name of file
        spec_files - list of format specification files to load (written in h5gate 
        specification language).  Each specification file must be a python file
        that defines a variable named "fs", that contains a dictionary of the
        specification for one or more name space.  If the empty list, then specifications
        are loaded from the file (works only when reading).
        default_ns - default name space for referencing data definition structures
        options - specified options.  Either a dictionary or a tuple that can be
        converted to a dictionary (with alternating keys and values).  See 
        'validate_options' below for possible options.
        """
        # self.test_filter_sigs()
        # sys.exit("all done")
        self.file_name = fname
        self.spec_files = spec_files
        self.default_ns = default_ns  # ns == 'name space'
        self.options = self.cast_to_dict(options)
        self.validate_options()
        self.fsname2ns = {}
        self.file_already_exists = self.file_name and os.path.isfile(self.file_name)
        self.initialize_storage_method()
        self.load_format_specifications(spec_files)
        self.make_ordered_name_spaces()
        self.reformat_structures()
#         for ns in self.ddef:
#             print "**** structures for namespace %s" % ns
#             pp.pprint(self.ddef[ns]['structures'])
#         print "done for now"
#         sys.exit(0)
        self.find_subclasses()
        self.initialize_subclassed_node_list()
        self.reading_file = True
        self.create_scratch_group()
        self.reading_file = False
        self.idlookups = self.mk_idlookups()
#         print "idlookups is:"
#         pp.pprint(self.idlookups)
    #    self.loce = self.make_locations_explicit()  # remove since locations no longer used
#           print "loce="
#           pp.pprint(self.loce)
#           print "---- loce above----"
        self.path2node = {}
        self.autogen = []   #  find_links.initialize_autogen()
        if self.options['mode'] == 'no_file':
            # not reading or writing a file
            return
        self.creating_file = self.options['mode'] == 'w' or not self.file_already_exists 
        self.custom_attributes = []
        self.error =[]
        self.warning = []
        self.links = find_links.initialize()
        self.file_changed = False
        self.close_callback = None
        self.open_file()
        if not self.creating_file:
            # reading file
            self.reading_file = True  # this prevents saving data to hdf5 file when reading
          #  self.lidsigs = self.make_lidsigs()  # remove since locations not used anymore
#             print "lidsigs="
#             pp.pprint(self.lidsigs)
#             print "-------- lidsigs above"
            self.idsigs = self.make_idsigs()
#             print "idsigs="
#             pp.pprint(self.idsigs)
            find_links.find(self.file_pointer, self.links)
#             find_links.show_stats(self.links)
#             sys.exit("all done for now")
            self.load_node_tree()
            self.reading_file = False
        else:
            self.reading_file = False
            self.initialize_node_tree()
            self.links = find_links.initialize()
            # self.save_format_specifications(dimp)
            self.save_format_specifications(spec_files)

    def get_version(self):
        """Returns version information for this software and also version
        information for definition files."""
        version = "h5gate 0.8.0; Feb 1, 2016"
        return version
    
    def set_close_callback(self, callback):
        """ Save function callback so it will be called before closing the file.
        This is to enable client software to perform actions needed at
        close time, such as saving the modification time if the file was
        modified."""
        self.close_callback = callback
        
    def validate_options(self):
        """Validate provided options and adds defaults for those not specified"""
        all_options = {
            'spec_dir' : {
                'description': ('Default location for format specification files'
                    ' (defining the format using the specification language).  This'
                    ' used for loading specification files listed in the "spec_files" parameter.'),
                'default': os.path.dirname(os.path.realpath(__file__))},
                # 'default': './',
            'link_type': {
                'description': 'Type of links when linking one dataset to another',
                'values': { # following tuples have description, then 'Default' if default value
                    'soft': 'hdf5 soft links',
                    'string': 'make string dataset containing path to link'},
                'default': 'soft' },
            'identify_custom_nodes': {
                'description': ('Add and attribute to custom nodes (groups and datasets not '
                    'described by a schema) to indicate they are custom.'),
                'values': {
                    True: 'yes, identify them by including the custom_node_identifier',
                    False: 'no, do not include the custom node identifier'},
                'default': True },
            'custom_node_identifier': {
                'description': ('Attribute name and value to assign to custom nodes '
                    'to identify them as custom.  If None, or if "identify_custom_nodes" is'
                    'not True, then custom nodes are not identified.'),
                'default': ['schema_id', 'Custom']}, # for NWB will be "neurodata_type", "Custom"
            'identify_extension_nodes': {
                'description': ('Add and attribute to nodes (groups and datasets) defined in '
                    'an extension (schema not in the default namespace) to indicate they are '
                    'defined by the extension.'),
                'values': {
                    True: 'yes, identify them by including the extension_node_identifier',
                    False: 'no, do not include the extension node identifier'},
                'default': True },
            'extension_node_identifier': {
                'description': ('Attribute name to assign to nodes (groups and datasets) '
                    'defined by extensions to indicate they are defined by extensions. '
                    'The attribute value will be the identifier of the extension'),
                'default': 'schema_id'},
            'identify_normal_nodes': {
                'description': ('Include attribute and value identifying normal nodes'
                    ' (not custom and not defined by extension)'),
                'values': {
                    True: 'yes, include attribute identifying normal nodes',
                    False: 'no, do not include id'},
                'default': False },
            'normal_node_identifier': {
                'description': ('Attribute to use for storing value identifying normal '
                    '(not custom and not extension) nodes.'),
                'default': 'schema_id', },
            'auto_compress': {
                'description': ('Automatically compress datasets.'),
                'values': {
                    True: 'yes, compress',
                    False: 'no, do not compress'},
                'default': True },
            'storage_method': {
                'description': ('Method used to store data.  This allows for storing'
                    ' data using different storage methods.'),
                'values': {
                    'hdf5': 'Data stored in hdf5 file using h5py',
                    'commands': ('Data not stored using this code.  Commands to store data'
                        ' are saved in self.h5commands for processing by'
                        ' a calling program, e.g. MatLab.'),},
                'default': 'hdf5', },
            'mode': {
                'description': ('Mode used to access file.  Currently only "w" or "w-" works'
                    ' with matlab front-end (that uses storage_method "commands").'),
                'values': {
                    'r': 'Readonly, file must exist.  (currently only used for validation).',
                    'r+': 'read/write, file must exist.',
                    'w': 'Create file, replacing if exists.',
                    'w-': 'Create file, fail if exists.',
                    'a': 'Read/write if exists, create otherwise',
                    'no_file': ('Do not read or open a file.  This used for generating '
                        'documentation from specification files'), 
                    },
                'default': 'w', },
            'copy_append': {
                'description': ('Indicates whether to make a copy of the file before '
                    'appending to it if using mode "r+" or "a" to append to an existing '
                    'file.'),
                'values': {
                    True: 'Make a copy of file before appending to it.',
                    False: 'Do not make a copy.  Append directly to the exiting file.'},
                'default': True },
            'keep_original': {
                'description': ('If True, and mode is "r+", "w", or "a" (i.e. a mode that can '
                    'change or replace a file), keep a backup copy of any original.  The '
                    'backup will be saved with the name "<filename>.prev".'),
                'values': {
                    True: 'Keep backup copy',
                    False: 'Do not keep backup copy'},
                'default': True },
            'use_default_size': {
                'description': ('When creating a dataset (via call to "set_dataset") and '
                    'if the dtype parameter is not specified, should the default data type '
                    'size be used?  If the data sizes are already optimized before calling '
                    'set_dataset, then this option could be set to False to avoid having to '
                    'always specify the dtype explicitly in the calls to set_dataset.  If '
                    'automatic conversion to the default sizes are desired if dtype is not '
                    'specified, then this should be set True'),
                'values': {
                    True: 'Yes, do automatic conversion to default data type and size',
                    False: 'No.  Do not automatically convert data types'},
                'default': True},
            'save_specs': {
                'description': ('If True, and if a dataset with id "<specification_file>" '
                    'is defined in one of the name spaces, the contents of the format '
                    'specifications files will be saved into the HDF5 file in the '
                    '"<specification_file>" dataset(s).  The name of each dataset will be '
                    'the name of the specification file, and attribute namespaces will be '
                    'set to the namespaces defined in that specification file.  '
                    'If the this is False, or if a dataset with id "<specification_file>" '
                    'is not found, then the format specification files are not saved '
                    'in the hdf5 file.'),
                'values': {
                    True: 'Save specification files in HDF5 file',
                    False: 'Do not save specification files in HDF5 file.' },
                'default': True},
            'specs_location': {
                'description': ('Group within hdf5 file that will contain format specification '
                    'files.  This used when loading specification files from a created '
                    'hdf5 file (when reading).  If empty, or if format specifications are provided '
                    'in parameter "spec_files" then format specifications will not be read '
                    'from the hdf5 file.'),
                'default': '/general/specifications' # used in NWB format
            },
            'verbosity': {
                'description': ('Controls how much is displayed in validation report.'),
                'values': {
                    'none': 'Display nothing.  (Useful for unit tests).',
                    'summary': 'Display summary of validation report.',
                    'all': 'Display everything.'},
                'default': 'all' },
        }
        errors = []
        for opt, value in self.options.iteritems():
            if opt not in all_options:
                errors.append("Invalid option specified (%s)" % opt)
            elif 'values' in all_options[opt] and value not in all_options[opt]['values']:
                errors.append(("Invalid value specified for option (%s), should be"
                    " one of:\n%s") % (opt, all_options[opt]['values'].keys()))
            elif opt == 'custom_node_identifier':
                # validate 'custom_node_identifier' separately
                if not (isinstance(value, (list, tuple)) and len(value) == 2 
                    and isinstance(value[0], str) and isinstance(value[1], str)):
                    errors.append(("Invalid value for option 'custom_node_identifer', "
                        "must be [attribute_id, value], is: %s") % value)
        if errors:
            print "\n".join(errors)
            print "valid options are:"
            pp.pprint(all_options)
            error_exit()
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
            error_exit()
    
    def get_spec_file_path(self, file_name):
        """ Return path to format specification file.  Abort if file not found."""
        path = file_name
        if not os.path.isfile(path):
            default_dir = self.options['spec_dir']
            path = os.path.join(default_dir, file_name)
            if not os.path.isfile(path):
                raise Exception('Unable to locate format specification file: %s' %
                    file_name)
        return path
                    
    def load_format_specifications(self, spec_files):
        """ Load format specification files, specified by "spec_files" parameter.
        Save in self.ddef (ddef stands for data definitions)"""
        self.ddef = {}  # ddef == "data definitions", loaded from format specification files
        fs_var = "fs"  # variable that must be defined in format specification files
        if not spec_files:
            self.load_specifications_from_h5_file(fs_var)
        for file_name in spec_files:
            path = self.get_spec_file_path(file_name)
            with file(path) as f:
                file_contents = f.read()
            try:
                # use use ast.literal_eval rather than eval to prevent potential security problems
                # vals = eval(file_contents)
                vals = ast.literal_eval(file_contents)
            except Exception, e:
                print ("** Invalid format in specification file '%s' (should "
                    "be mostly JSON)") % file_name
                print "Error is: %s" % e
                error_exit()
            patch_json_vals(vals, {"float('NaN')": float('NaN')})
            if fs_var not in vals:
                raise Exception("Variable '%s' not defined in specification file '%s'" %
                    (fs_var, file_name))
            # get definitions that are in variable fs_var
            ddefin = vals[fs_var]
            # validate that components of definition are present
            errors = self.validate_fs(ddefin)
            if errors:
                print ("Specification file '%s', has"
                    " the following errors:\n%s" % (file_name, errors))
                error_exit()
            # save map from file name to name spaces stored in that file
            name_spaces = ddefin.keys()  # e.g. "core".  Usually only one namespace, but could be more
            self.fsname2ns[file_name] = name_spaces
            # find_links.add_item(self.fsname2ns, file_name, name_spaces)
            # also save map from name space to file name
            for ns in name_spaces:
                ddefin[ns]['file_name'] = file_name
            # Merge definition in with others
            # todo: check to be sure name spaces not defined more than once
            self.ddef.update(ddefin)
        if not self.ddef:
            raise Exception("No file format specifications were provided.  At least one"
                 " is required.")
        if self.default_ns not in self.ddef.keys():
            raise Exception(("Default name space ('%s') was not defined in any format "
                "specification file") % self.default_ns)
                
                
    def save_format_specifications(self, spec_files):
        """ If requested and if write mode, save format specification files into hdf5 file"""
        if not self.creating_file:
            # don't save  # todo: check for new specification if appending to a file
            return
        if not self.options['save_specs']:
            # saving format specification files in not requested, don't save
            return
        # look for "<specification_file>" id in name spaces
        sid = "<specification_file>"
        match = False
        for sns in self.idlookups.keys():  # spec name space
            if sid in self.idlookups[sns]:
                match = True
                break
        if not match:
            # did not find "<specification_file>" defined in any namespace.
            # so don't save specifications
            self.warning.append(("Option 'save_specs' specified, but did not find id "
                "'%s' in any namespace definition.  So format specfication files not "
                "saved in HDF5 file.") % sid)
            return
        # now save each format specification file in the HDF5 file
        # make qualified id (qualified by namespace if not default)
        qsid = sid if sns == self.default_ns else "%s:%" % (sns, sid)
        for file_name in spec_files:
            path = self.get_spec_file_path(file_name)
            fp = open(path, "r")
            content = fp.read()
            fp.close()
            name_spaces = self.fsname2ns[file_name]
            base_name = os.path.basename(file_name)
            self.set_dataset(qsid, content, name=base_name, attrs={'namespaces': str(name_spaces)})
            
    def load_specifications_from_h5_file(self, fs_var):
        # load specifications from created hdf5 file
        if not self.file_already_exists:
            msg = "Unable to load format specifications from hdf5 file because file not found: %s" % (
                self.file_name)
            error_exit(msg)
        specs_location = self.options['specs_location'];
        if not specs_location:
            msg = ("Cannot load format specifications because parameter spec_files is empty and "
                "option 'specs_location' is empty.")
            error_exit(msg)
        try:
            fp = h5py.File(self.file_name, 'r')
        except IOError:
            msg = "Unable to open file '%s' to read specifications" % self.file_name
            error_exit(msg)
        try:
            specs_group = fp[specs_location]
        except KeyError:
            print "Format specifications location (%s) not found in file '%s'" % (
                specs_location, self.file_name)
        # Now load each specification
        for file_name in specs_group:
            file_contents = specs_group[file_name].value
            try:
                # vals = eval(file_contents)
                vals = ast.literal_eval(file_contents)
            except Exception, e:
                print ("** Invalid format in specification file '%s' (should "
                    "be mostly JSON)") % file_name
                print "Error is: %s" % e
                error_exit()
            patch_json_vals(vals, {"float('NaN')": float('NaN')})
            if fs_var not in vals:
                raise Exception("Variable '%s' not defined in specification file '%s'" %
                    (fs_var, file_name))
            # get definitions that are in variable fs_var
            ddefin = vals[fs_var]
            # validate that components of definition are present
            errors = self.validate_fs(ddefin)
            if errors:
                msg = ("Saved specification file '%s', has"
                    " the following errors:\n%s" % (file_name, errors))
                error_exit(msg)
            # save map from file name to name spaces stored in that file
            name_spaces = ddefin.keys()  # e.g. "core".  Usually only one namespace, but could be more
            self.fsname2ns[file_name] = name_spaces
            # find_links.add_item(self.fsname2ns, file_name, name_spaces)
            # also save map from name space to file name
            for ns in name_spaces:
                ddefin[ns]['file_name'] = file_name
            # Merge definition in with others
            # todo: check to be sure name spaces not defined more than once
            self.ddef.update(ddefin)
        if not self.ddef:
            raise Exception("No file format specifications were provided.  At least one"
                 " is required.")
        if self.default_ns not in self.ddef.keys():
            raise Exception(("Default name space ('%s') was not defined in any saved format "
                "specification file") % self.default_ns)
        # print "Loaded format specifications %s from file '%s'" % (specs_group.keys(), self.file_name) 

                   
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
            # for part in ('structures', 'locations', 'info'):
            for part in ('info', 'schema'):
                if part not in fs[ns].keys():
                    errors.append("Namespace '%s' is missing ['%s'] definition" % (ns, part))
            if 'info' in fs[ns].keys():
                for part in ('version', 'date', 'author', 'contact', 'description'):
                    if part not in fs[ns]['info']:
                        errors.append("Namespace '%s' ['info'] is missing ['%s']" % (ns, part))
            if not errors:
                # convert from "schema" to "structures" and add empty "locations" to match
                # original way h5gate was written
                fs[ns]['structures'] = fs[ns]['schema']
                del fs[ns]['schema']
                fs[ns]['locations'] = {}
        # method.             
        if len(errors) > 0:
            errors =  "\n".join(errors)
            return errors
        return None       
    
                  
    def initialize_storage_method(self):
        """ Initialize method for storing data.  Currently, methods are
        'hdf5' and 'commands'.  hdf5 uses h5py.  'commands' saves commands
        for later processing by a calling script (for example, MATLAB). """
        if self.options['storage_method'] == 'hdf5':
            import h5py
            import numpy as np
            global h5py, np
        elif self.options['storage_method'] == 'commands':
            if self.options['mode'] in ['r', 'r+']:
                raise Exception(("Invalid option combination.\nmode='%s', but only "
                    "mode 'w' allowed with storage method 'commands'" )% self.options['mode'])
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
        'commands', command to create the group is saved for later processing by a
        calling program, e.g. MatLab.  This is the only function used to create a group"""
        if self.reading_file or self.options['mode'] == 'no_file':
            return
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file_pointer.create_group(path)
        elif self.options['storage_method'] == 'commands':
            # save command for later processing
            self.h5commands.append(("create_group", path,))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
        self.file_changed = True
    
    def create_dataset(self, path, data, dtype=None, compress=False, maxshape=None):
        """ Creates a dataset using the selected storage_method option.  If storage_method
        is 'hdf5', dataset is created in the hdf5 file using h5py.  If storage method is
        'commands', command to create the group is saved for later processing by a
        calling program, e.g. MatLab.  This is the only function used to create a dataset"""
        if self.reading_file or self.options['mode'] == 'no_file':
            return
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            # compress if requested
            compress = "gzip" if compress else None
            # Need to check for dtype type string because could be special h5py dtype
            # used for a text type with dimension is *unlimited*
            # set in function get_default_dtype  
            if isinstance(dtype, str) and dtype == 'binary':
                # binary data.  use np.void on data as described in:
                # http://docs.h5py.org/en/latest/strings.html
                sdata = np.void(data)
                dtype = None
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], unicode) and dtype is None:
                # assume data is a list of elements type unicode.  Convert to list of strings as described in
                # https://github.com/h5py/h5py/issues/289
                # other option is to specify dtype, described in: http://docs.h5py.org/en/latest/strings.html
                # dtype = h5py.special_dtype(vlen=unicode)  # does not work for unicode type
                sdata = [s.encode('utf8') if isinstance(s, unicode) else s for s in data]
#             elif 'int' in str(dtype) and np.issubdtype(type(data), np.float) and np.isnan(data):
#                 # attempting to save float (nan) but dtype is int.  Change dtype to None
#                 # this happend when saving a nan to an integer.  Need to leave type as float
#                 # for NWB project, it happens if autogen cannot determine length of timestamps
#                 # for num_samples
#                 dtype = None
#                 sdata = data
            else:
                sdata = data
            if isinstance(dtype, str) and dtype == '':
                # fix for matlab calls in which dtype is empty string
                dtype = None
            self.file_pointer.create_dataset(path, data=sdata, dtype=dtype, 
                compression=compress, maxshape=maxshape)
        elif self.options['storage_method'] == 'commands':
            # save command for later processing
            self.h5commands.append(("create_dataset", path, data, dtype, compress, maxshape))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
        self.file_changed = True
   
    def create_softlink(self, path, target_path):
        """ Creates a softlink using the selected storage_method option.  If storage_method
        is 'hdf5', softlink is created in the hdf5 file using h5py.  If storage method is
        'commands', command is saved for later processing by a calling program, e.g. MatLab."""
        if self.reading_file or self.options['mode'] == 'no_file':
            return
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file_pointer[path] = h5py.SoftLink(target_path)
        elif self.options['storage_method'] == 'commands':
            # save command for later processing
            self.h5commands.append(("create_softlink", path, target_path))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
        self.file_changed = True
 
    def create_external_link(self, path, target_file, target_path):
        """ Creates an external link using the selected storage_method option.  If storage_method
        is 'hdf5', create using h5py.  If storage method is
        'commands', command is saved for later processing by a calling program, e.g. MatLab."""
        if self.reading_file or self.options['mode'] == 'no_file':
            return
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            # self.file.file_pointer[self.full_path] =  h5py.ExternalLink(file,path)
            self.file_pointer[path] =  h5py.ExternalLink(target_file, target_path)
        elif self.options['storage_method'] == 'commands':
            # save command for later processing
            self.h5commands.append(("create_external_link", path, target_file, target_path))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
        self.file_changed = True

    def set_attribute(self, path, name, value):
        """ Set an attribute using the selected storage_method option.  If storage_method
        is 'hdf5', set using h5py.  If storage method is 'commands', save command for later
        processing by a calling program, e.g. MatLab."""
        if self.reading_file or self.options['mode'] == 'no_file':
            return
        if self.options['storage_method'] == 'hdf5':
            # execute h5py command
            self.file_pointer[path].attrs[name] = value
        elif self.options['storage_method'] == 'commands':
            # save command for later processing
            self.h5commands.append(("set_attribute", path, name, value))
        else:
            raise Exception('Invalid option value for storage_method (%s)' % storage_method)
        self.file_changed = True
                              
    def get_file_to_open(self):
        """ Checks if should open a temporary file in order to preserve the original file as
        a backup."""
        mode = self.options['mode']
        self.file_exists = os.path.isfile(self.file_name)
        if self.file_exists:
            if mode == "w-":
                print "Mode 'w-' specified, but cannot be used because the file (%s) exists." % self.file_name
                error_exit()
        else:
            if mode in ("r", "r+"):
                print "File '%s' not found.  File must exist to use mode 'r' or 'r+'" % self.file_name
                error_exit()
        if mode == 'w' and self.options['keep_original'] and self.file_exists:
            # need to create temporary file rather than original
            self.temp_name = self.file_name + ".tmp"
            file_to_open = self.temp_name
        elif mode in ('r+', 'a') and self.file_exists and (
            self.options['keep_original'] or self.options['copy_append']):
            # need to make copy of original and open the copy
            self.temp_name = self.file_name + ".tmp"
            # make backup copy before modifying anything
            # copy2 preserves file metadata (eg, create date)
            shutil.copy2(self.file_name, self.temp_name)
            file_to_open = self.temp_name
        else:
            # just open original file
            self.temp_name = None
            file_to_open = self.file_name
        return file_to_open
        
    def save_temporary_file(self):
        """ If a temporary file was created, move it to file_name.  Also, save backup of
        original file if that was requested."""
        if self.temp_name:
            # temporary file was created
            if self.options['keep_original']:
                # make backup copy of original with suffix '.prev'
                assert os.path.isfile(self.file_name), ("Temporary file created, but "
                    "original file not found when saving: %s" % self.file_name)
                shutil.move(self.file_name, self.file_name + ".prev")
            # move temporary file to original file_name
            shutil.move(self.temp_name, self.file_name)
                              
    def open_file(self):
        """ open file """
        if self.options['storage_method'] == 'hdf5':
            file_to_open = self.get_file_to_open()
            if os.path.isfile(file_to_open) and self.options['mode'] == 'w':
                # remove existing file so can open in matlab if was open before
                try:
                    os.remove(file_to_open)
                except IOError:
                    print "Unable to remove previously existing file '%s'\nbefore opening with mode '%s'\n" % (
                        file_to_open, self.options['mode'])
                    error_exit() 
            try:
                fp = h5py.File(file_to_open, self.options['mode'])
            except IOError:
                print "Unable to open file '%s' with mode '%s'" % (file_to_open,
                    self.options['mode'])
                error_exit()
            # remember file pointer
            self.file_pointer = fp
            # print "Opened file '%s'" % file_to_open
        elif self.options['storage_method'] == 'commands':
            # save command for later processing.  Must be creating new file
            self.h5commands.append(("create_file", self.file_name))
                   
    def close(self):
        """ Close the file after executing finalization routines ."""
        if self.options['mode'] == 'no_file':
            # not reading or writing a file.  So do nothing
            return
        # execute close callback if provided by client software
        # this used to update the modification_date in the nwb format api
        if self.close_callback:
            self.close_callback(self)
        if self.options['mode'] in ['w', 'r+']:
            # file opened in write mode.  Update links information, then update autogen
            find_links.build_links_dicts(self.links)
            # find_links.show_links(self.links)
            find_links.process_autogen(self)
        else:
            # file opened in read mode.  No need to build links dicts (was already built)
            find_links.process_autogen(self)
        self.prune_unused_subclasses()
        validation_result = self.validate_file()
        if self.options['storage_method'] == 'hdf5':
            self.file_pointer.close()
            self.save_temporary_file()
        elif self.options['storage_method'] == 'commands':
            self.h5commands.append(("close_file", ))
        return validation_result
            
    def __del__(self):
        """ Close file if not already closed.  This called when the File object is
        deleted.  File might not have been closed if an error was found.
        """
        print "python __del__ called"
        if self.file_pointer:
            try:
                file_pointer.close()
                print "python __del__ closed file"
            except (RuntimeError):
                pass
        
            
    def process_merge_into(self):
        """ Go through all id's defined in all extensions and look for groups containing
        a "merge_into" directive, or groups that have the same id as a group in the 
        default namespace.  If found, append the extension id to the "merge" directive
        in the default namespace so that the extensions will be added to the structures
        defined in the default namespace.  This should be done before calling mk_idlookups
        so the extensions are incorporated into the definitions used to make the idlookups.
        """
        dns_structures = self.ddef[self.default_ns]['structures']
        for ns in self.ddef.keys():
            if ns == self.default_ns:
                # this is not a default namespace
                continue
            # found an extension
            for id in self.ddef[ns]['structures']:
                if not id.endswith('/'):
                    # not a group.  Ignore since cannot have 'merge_into' clause
                    # todo: may relax this to allow merging of datasets, for attributes?
                    continue
                idef = self.ddef[ns]['structures'][id]
                if 'merge_into' in idef:
                    for qtid in idef['merge_into']:
                        if ":" in qtid:
                            tns, tid = qtid.split(':')
                            if tns != self.default_ns:
                                print ("Namespace %s, id %s has 'merge_into' listing '%s', but "
                                    "namespaces specified in merge_into must be the default namespace (%s)") % (
                                    ns, id, qtid, self.default_ns)
                                error_exit()
                        else:
                            tid = qtid
                        if tid not in dns_structures:
                            print ("'%s' referenced in '%s:%s' 'merge_into' but not found in default "
                                "namespace '%s'") % (tid, ns, id, self.default_ns)
                            error_exit()
                        self.append_to_merge(tid, ns, id)
                elif id in dns_structures:
                    # name matches id in default_ns.  Assume this should be merged.
                    self.append_to_merge(id, ns, id)
                else:
                    print ("** Warning: Id '%s' in namespace '%s' does not match id in default namespace '%s' "
                        "and 'merge_into' not present") %(id, ns, self.default_ns)
                    print "It might not be used unless it is referenced from another id (by merge or include)"
        
    def append_to_merge(self, tid, ns, id):
        """ Append id in namespace ns to 'merge' directive in target id tid that is in the
        default namespace"""
        # make qualified id
        qid = "%s:%s" % (ns, id)
        tdef = self.ddef[self.default_ns]['structures'][tid]
        if 'merge' in tdef:
            tdef['merge'].append(qid)
        else:
            # merge not in target definition.  Add it.
            tdef['merge'] = [qid,]
        
    def mk_idlookups(self):
        """ Makes idlookups for default namespace.  Old version made for each namespace,
        but now everything should be merged into the default namespace.  So only need
        to start with root.
        """
        idlookup = {}
        path = "/"
        self.save_path_in_idlookup(path, idlookup)
        ns = self.default_ns
        sdef = self.get_sdef(path, ns, errmsg='Referenced in mk_idlookups')
        self.save_members_in_idlookup(path, sdef, idlookup)
        idlookups = {ns: idlookup}
        return idlookups
        
                
    def save_members_in_idlookup(self, path, sdef, idlookup):
        """ save members of definition sdef in idlookup.  path is an absolute
        path that is in structures """
        parent_path, name = self.get_name_from_full_path(path)
        name = ""  # name not specified because id is non-variable and is in sdef
#         print "\nin save_members_in_idlookups, calline get_expanded_def with parent_path='%s', id='%s' sdef=" % (
#             parent_path, sdef['id'])
#         pp.pprint(sdef)
        expanded_def = self.get_expanded_def(sdef, name, parent_path)
        mstats = expanded_def['mstats']
        for mid in mstats:
            self.add_entry_to_idlookup(path, mid, idlookup)
            mtype = mstats[mid]['type']
            v_id = re.match( r'^<[^>]+>/?$', mid) # True if variable_id (in < >)
            if mtype == 'group' and not v_id:
                # Need to add members of this group too
                mdf = mstats[mid]['df']
                mlink = 'link' in mdf  # should not need this
                if mlink:
                    print "found link at top level when making idlookup.  Not allowed.  Path is: %s" % path
                    error_exit()
                mns = mstats[mid]['ns']
                msdef = { 'type': mtype, 'id':mid, 'ns':mns, 'df': mdf}
                new_path = self.make_full_path(path, mid)
                # make recursive call to save these members
                self.save_members_in_idlookup(new_path, msdef, idlookup)
            

    def save_path_in_idlookup(self, path, idlookup):
        """ Given an absolute path corresponding to a definition of a node (group or
        dataset) in the "structures" section of a specification, generate the id's
        that would be generated by the path to save in idlookups, for possible use in
        make_group or set_dataset, using components of the path.
        idlookup has the following structure:
        { id: [path1, path2, ...], id2: [path3, path4, ...] }
        where:
         - "id" is an id of a group that is part of the path that could be
           referenced in a call to make_group.
         - "path" is the path to the parent of where the id is located in that
           instance of the id.
        """
        if path == "/":
            # root
            idlookup[path] = [path,]
            return
        type = 'group' if path.endswith('/') else 'dataset'
        path_parts = path.strip("/").split("/")
        num_parts = len(path_parts)
        if type == 'group':
            # put slash suffix back on last part if this is a group
            path_parts[num_parts - 1] = path_parts[num_parts - 1] + "/"
        loc = "/"
        i = 0
        for part in path_parts:
            i = i + 1
            # id has slash to indicate group if not last part of path
            id = part + "/" if i < num_parts else part
            self.add_entry_to_idlookup(loc, id, idlookup)
            loc = loc + part if loc == "/" else loc + "/" + part
    
    def add_entry_to_idlookup(self, path, id, idlookup):
        """ add path to idlookup"""
        if id in idlookup:
            if path not in idlookup[id]:
                idlookup[id].append(path)
        else:
            idlookup[id] = [path,]
            
    def get_name_from_full_path(self,full_path):
        """ Get parent path and name from a full path.  Full path may end with '/' if
        it's not the root.  This does the reverse of "make_full_path."""
        if full_path == "/":
            parent_path = ""
            name = "/"
        else:
            gslash = "/" if full_path.endswith('/') else ""
            if full_path[0] != '/':
                full_path = '/' + full_path
            parent_path, name = full_path.rstrip("/").rsplit('/', 1)
            name = name + gslash
            if parent_path == "":
                parent_path = "/"
        return (parent_path, name)        
            
    def add_namespace_to_ids(self, ids, ns):
        """ ids is a list of id's, possibly qualified with a namespace e.g. core:general/
        "core:" is the namespace.  Return a list with all id's qualified, made by qualifying
        any that are not using namespace 'ns'"""
        qids = ["%s:%s" % (ns,x) if not ':' in x else x for x in ids]
        dqids = {}  # for now make dictionary to match current 'includes' syntax.  Todo, change to list.
        for id in qids:
            dqids[id]={}
        return dqids
    
  
    def reformat_structures(self):
        """ Replace any structures that have a key followed by a quantity by
        by removing the quantity and placing it in the "_qty" key of the structure
        dictionary.  i.e. replace keys like: "/acquisition/timeseries/?": { ...}
        with "/acquisition/timeseries/": { "_qty": "?", ...}
        to enable looking up structure id without having quantity.
        This is recursive so it does this with keys inside of structures,
        not just the at the top level.
        Also, create a new entry "_source" in each dictionary in the structure
        set to the qualified id for the structure, that is: ns:id, where
        ns is the namespace and id is the the id for the structure, e.g.:
        core:/general/ or ext:<TimeSeries>.  The "_source" is used to create
        field "source" which is an array of ancestry (of subclasses) for each
        component;  That's used when creating documentation showing which namespace
        each component is from.
        """
        for ns in self.ddef:
            structures = self.ddef[ns]['structures']
            for top_id in structures.keys():
                id, qty = self.parse_qty(top_id, "!")
                source = "%s:%s" % (ns, id)
                self.reformat_structure(structures, top_id, source)
                
    def reformat_structure(self, structure, top_id, source):
        """ reformat top level structure with id top_id.  Reformat means to change keys that
        have a quantity suffix to a key that does not, and add the "_source" key with value
        source.
        """
        # recursively reformat all members of structure
        self.reformat_def(structure[top_id], source)
        # change top level key-value if needed (key for structure)
        self.reformat_sid(structure, top_id, source)
        
    
    def reformat_def(self, df, source):
        """ recursively reformat all members of df by removing any qty following id, and
        adding _source key.
        """
        to_check = [df]
        while to_check:
            df = to_check.pop(0)
            for idq in df.keys():
                if isinstance(df[idq], dict):
                    to_check.append(df[idq])
                    self.reformat_sid(df, idq, source)
                 
    def reformat_sid(self, df, idq, source):
        """ reformat a single key-value pair by removing any quantity from the key and
        moving it into the value ("_qty") and adding "_source" to value.  value
        must be a dict.
        """
        qty_flags = ('!', '^', '?', '+', '*')
        if idq[-1] in qty_flags and len(idq) > 1:
            # found quantity flag. Replace key with version without qty
            qty = idq[-1]
            id = idq[0:len(idq)-1]
            assert id not in df, ("namespace '%s', source '%s': id '%s' appears at "
                "the same level more than once") % (ns, source, id)
            sval = df.pop(idq)
            sval["_qty"] = qty
            df[id] = sval
        else:
            id = idq
        # set _source key if id is not 'attributes'
        if id not in ('attributes', 'include'):
            df[id]['_source'] = source
 
    
    def find_subclasses(self):
        """ find all subclasses in format specification.  This used to implement
        includes with option "subclasses": True.  Subclasses are defined by a
        a group with a relative id (not an absolute path location) that has a
        top level "merge".  The id merged is the superclass.
        """
        merges = {}
        for ns in self.ddef.keys():
            structures = self.ddef[ns]['structures']
            for id in structures:
                if id[0] != "/" and id[-1] == '/' and 'merge' in structures[id]:
                    merge = structures[id]['merge']
                    # qid = id if ns == self.default_ns else "%s:%s" % (ns, id)
                    qid = "%s:%s" % (ns, id)
                    merges[qid] = self.make_qualified_ids(merge, ns)
        # Now expand targets
        expanded_merges = self.expand_targets(merges)
        subclasses = self.reverse_dict_array(expanded_merges)
        self.add_concrete_bases(subclasses)
        self.subclasses = subclasses
        
    def add_concrete_bases(self, subclasses):
        """ subclasses is a dict with each key a base class and values a list
        of subclasses for that base.  Check each base to see if it's not an
        abstract class (i.e. a concrete class).  If so, than add the base to
        the list of subclasses for that base.  This is because an include that
        includes subclasses for that base should also include the base class."""
        for qid in subclasses.keys():
            sdef = self.get_sdef(qid, self.default_ns, "called from add_concrete_bases")
            df = sdef['df']
            abstract = self.is_abstract(df)
            if not abstract:
                # add the base class to the list.
                # Put it in front for aesthetics, but order should not matter
                subclasses[qid].insert(0, qid)  
        
    def is_abstract(self, df):
        """ Return true if a definition is for an abstract class (which cannot be
        created, but must be subclassed.  This uses the "_properties" key of the
        definition.
        """
        abstract = ("_properties" in df and "abstract" in df['_properties'] and
            df['_properties']['abstract'])
        return abstract
        
    def initialize_subclassed_node_list(self):
        """ Initialize list of nodes that have members added by either include with
        _options, "subclasses": True, e.g.:
        "include":  {"<TimeSeries>/*":{"_options": {"subclasses": True}}}
        or with a "merge+", e.g.:  "merge+": ["<ImageSeries>/", ]
        Both of the above result in entries for the base class and subclasses
        being added to the node "mstats" dictionary.  The list of nodes is
        saved so that the unused members can be removed before validating the
        file, so the added entries will not cause spurious errors (required
        or recommended member missing) when doing the validation."""
        self.subclassed_nodes = {"include": [], "merge": []}
        
    def prune_unused_subclasses(self):
        """ Remove unused mstats entries that are created by subclass includes and
        subclass merges.  This done so they do not cause spurious errors
        during validation"""
        # prune "include" subclasses
        for node in self.subclassed_nodes["include"]:
            # Build cu dict, mapping base class(s) to {'created': [...], 'unused': [...]}
            # where each [...] is respectively the list of created and unused subclasses
            cu = {}
            for id in node.mstats:
                if 'include_info' not in node.mstats[id]:
                    continue
                inc_info = node.mstats[id]['include_info']
                # include_info dict made in function File.save_include
                if inc_info['source'] != "subclass":
                    continue
                base_class = inc_info["base"]
                if base_class not in cu:
                    cu[base_class] = {'created': [], 'unused': []}
                cu_idx = 'created' if len(node.mstats[id]["created"]) > 0 else 'unused'
                cu[base_class][cu_idx].append(id)
            # prune unused members for each base_class
            # If no members were used, keep the base_class member
            # otherwise remove all unused members
            for base_class in cu:
                keep_base_class = len(cu[base_class]['created']) == 0
                for id in cu[base_class]['unused']:
                    if not keep_base_class or id != base_class:
                        del node.mstats[id]
        # prune "merge" subclasses
        for node in self.subclassed_nodes["merge"]:
            if not hasattr(node, 'subclass_merge_ids'):
                # subclasses were already removed by function prune_subclass_merges
                continue
            # remove all except the base subclass
            for id in node.subclass_merge_ids[1:]:
                created = len(node.mstats[id]["created"]) > 0
                assert not created, "prune unused subclass found id actually used: %s %s" % (
                    node.full_path, id)
                del node.mstats[id]           
    
    def make_qualified_ids(self, ids, ns):
        # ids is a list of ids, ns is a name space
        # create a new list of ids, with all of them qualified by the namespace, e.g. ns:id
        qids = []
        for id in ids:
            qid = id if ":" in id else "%s:%s" % (ns, id)
            qids.append(qid)
        return qids 
    
    def expand_targets(self, source_to_target):
        """ Make dictionary mapping each source to an expanded list of targets.
        The expanded list of targets is formed by finding any targets the targets
        in the initial list may map too. """ 
        source_to_expanded_targets = {}
        for source in source_to_target:
            tlist = source_to_target[source][:]  # make copy
            est = tlist[:]  # makes a copy of the copy
            while tlist:
                target = tlist.pop()
                if target in source_to_target:
                    tlist2 = source_to_target[target]
                    for item in tlist2:
                        if item not in est:
                            est.append(item)
                            tlist.append(item)
            source_to_expanded_targets[source] = sorted(est)
        return source_to_expanded_targets
        
    def reverse_dict_array(self, da):
        """ Make reverse dictionary array.  da is a dictionary with each key
        mapped to an array of values.  Return (dout) is is a dictionary with keys equal to the
        values of din mapped to the list of keys in din.
        """
        dout = {}
        for key in da:
            values = da[key]
            for value in values:
                self.add_to_dict_array(dout, value, key)
        return dout
        
    def add_to_dict_array(self, da, key, value):
        """ da is a "dict_array", ie a dictionary mapping each key to an array of values.
        Add key and value to it."""
        if key in da:
            if value not in da[key]:
                da[key].append(value)
        else:
            da[key] = [value,]
        
        
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
#             if id[0] == "/" and id != "/":
#                 # is absolute path, set id to basename
#                 parent_path, basename = self.get_name_from_full_path(id)
#                 id = basename
            sdef = { 'type': type, 'qid': qid, 'id':id, 'ns':ns, 'df': df, }
            return sdef
        if errmsg != "":
            print "Error: Structure '%s' (in name space '%s') referenced but not defined." % (id, ns)
            print "(%s)" % errmsg
            # import pdb; pdb.set_trace()
            error_exit()
        return None
        
    
    def get_idlocs(self, qid, default_ns, errmsg=''):
        """ Return location information corresponding to qid from idlookups.
        If location info does not exist, display error message (if given)
        or return None.
            qid - id, possibly qualified by name space, e.g. "core:<timeStamp>/", 'core' is
                is the name space.
            default_ns - default namespace to use if qid does not specify
            errmsg - error message to display if item not found.
        This is only using the self.default_ns namespace of idlookups, unlike the
        original version (get_idlocs_orig) which used other namespaces.  Id's that
        were in those other namespaces are now merged into the default_ns index, but
        qualified by the namespace prefix.
        """
        (ns, id) = self.parse_qid(qid, default_ns)
        quid = "%s:%s" % (ns, id) if ns != self.default_ns else id
        if quid in self.idlookups[self.default_ns]:
            idloc = self.idlookups[self.default_ns][quid]
            return idloc
        if errmsg != "":
            idp = id.rstrip('/')
            type = "group" if id.endswith('/') else 'dataset'
            msg = "Id '%s' (%s) not found in name space '%s'. (%s)" % (
                idp, type, ns, errmsg)
            possible_matches = self.check_for_misspellings(quid, 
                self.idlookups[self.default_ns].keys())
            # self.show_possible_matches(possible_matches, id)
            pm_msg = self.make_possible_matches_message(possible_matches, id)
            if pm_msg:
               msg += "\n" + pm_msg
            raise SchemaIdError(msg)
            # import pdb; pdb.set_trace()
        return None
        
        
    def check_for_misspellings(self, word, choices):
        """This function called when input word is supposed to match an element
        of choices.  Check to see if the is a match based on changing the case,
        stripping off leading / trailing slashes, then misspellings."""
        simp_word = word.strip("/<>").lower()
        if simp_word == "":
            # if empty sting, just return
            return None
        possible_matches = []
        sc = {}
        for choice in choices:
            simp_choice = choice.strip("/<>").lower()
            # save map from simp_choice to choice for possible use later
            if simp_choice in sc:
                sc[simp_choice].append(choice)
            else:
                sc[simp_choice] = [choice]
            if simp_word == simp_choice:
                possible_matches.append(choice)
        if possible_matches:
            return (possible_matches, "case")
        # match not found based on case, now try spelling changes
        import suggest_spellings
        spm = suggest_spellings.get_possible_matches(simp_word, sc.keys())
        if spm:
            possible_matches = []
            for simp_choice in spm:
                original_choices = sc[simp_choice]
                possible_matches.extend(original_choices)
            return (possible_matches, 'spelling')
        return None
        
    def make_possible_matches_message(self, possible_matches, id):
        """ Make message listing possible matches if there are any.
        possible_matches is a tuple, first element is a list of
        possible matches, second element is the method by which they
        were found, either 'case' (for case change) or 'spelling'
        (for spelling change).  type is the type of the misspelled
        id (group or dataset).  id is the original (misspelled) id.
        Return is a message (string) or None
        """
        if not possible_matches:
            return None
        pm, method = possible_matches
        pm = [m.rstrip('/') for m in pm]  # removing any trailing slash, they are not used in calls
        meth_msg = " (Ids are case sensitive)" if method == 'case' else ""
        if len(pm) == 1:
            if id.rstrip('/') == pm[0].rstrip('/'):
                id_type = "group" if id.endswith("/") else "dataset"
                possible_call = ("set_dataset(\"%s\", ...)" % id if id_type == "group" 
                    else "make_group(\"%s\", ...)" % id) 
                pm_msg = "Could you have meant to call: %s" % possible_call
            else:
                pm_msg = "Could you have meant \'%s\'? %s\n" % (pm[0], meth_msg)
        elif len(pm) > 1:
            pm_msg = "Could you have meant one of: %s?\n" % pm
        return pm_msg
             
    def retrieve_qty(self, df, default_qty):
        """ Retrieve quantity specified by key '_qty' or 'qty' from dict df.  Return
        default_qty if not specified.  'qty' is used for attributes that are
        merged and also mstats entries.  '_qty' is used for unprocessed structures
        (that is, only processed by function "reformat_structures")."""
        qty = df['_qty'] if '_qty' in df else (
            df['qty'] if 'qty' in df else default_qty)
        return qty
          
        
    def parse_qty(self, qid, default_qty):
        """ Parse id which may have a quantity specifier at the end. 
        Quantity specifiers are: ('*' - any, '!' - required, '^'-recommended,
        '+' - 1 or more, '?' - optional, or '' - unspecified)
        """
        matchObj = re.match( r'^([^*!^+?]+)([*!^+?]?)$', qid)        
        if not matchObj:
            error_exit("** Error: Unable to find match in pattern '%s'" % qid)
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
            error_exit("Unable to find match in pattern '%s'" % qid)
        ns = matchObj.group(1)
        id = matchObj.group(2)
        if ns is None:
            # namespace not specified, use default
            ns = default_ns
        self.validate_ns(ns)
        return (ns, id)
        
    def make_qid(self, id, ns):
        """ add namespace to id if not present"""
        if ":" in id:
            return id
        else:
            return "%s:%s" % (ns, id)
            
    def validate_ns(self, ns):
        if ns not in self.ddef.keys():
            error_exit("Namespace '%s' referenced, but not defined" % ns)
    
    def make_group(self, qid, name='', path='', attrs={}, link='', abort=True, attrs_shape=None):
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
                existing group.
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
                """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.deflatten_attrs(attrs, attrs_shape)
        # (ns, id) = self.parse_qid(qid, self.default_ns)
        if ':' in qid:
            (ns, id) = self.parse_qid(qid, self.default_ns)
        else:
            id = qid
            ns = None
        # gqid = qid + "/"
        gid = id + "/"
        # idlocs = self.get_idlocs(gqid, ns, "referenced in make_group")
        idlocs = self.get_idlocs(gid, self.default_ns, "referenced in make_group")
        # path = self.select_path(qid, ns, idlocs, path)
        path = self.select_path(gid, self.default_ns, idlocs, path)
        # print "called make_group, qid='%s', idloc='%s', path=%s" % (qid, idlocs, path)
        # parent = self.get_parent_group(path, ns, self.default_ns)
        parent = self.get_parent_group(path, self.default_ns, self.default_ns)
        if not abort:
            id_noslash = id.rstrip('/')  # could be different from gqid if namespace present
            grp = self.get_existing_group(path, id_noslash, name)
            if grp:
                # found already existing group
                return grp
        link_info = self.extract_link_info(name, link, Group)
        # for now assume can create group using definition inside mstats
        assert hasattr(parent, 'mstats'), "mstats not found in file make_group of %s" % path
        if gid not in parent.mstats:
            msg = "Did not find '%s' in parent mstats in file make_group for: %s" % (gid, path)
            error_exit(msg)
        if 'df' not in parent.mstats[gid]:
            msg = "Did not find df in mstats[%s] in file make_group for: %s" %(gid, path)
            error_exit(msg)
        # assert parent.mstats[gid]['ns'] == ns, "namespace mismatch in file make_group for: %s" % path
        if ns is not None and ns != parent.mstats[gid]['ns']:
            msg = "Supplied namespace '%s' in make_group '%s' does not match that of definition (%s)" % (
                ns, gid, parent.mstats[gid]['ns'])
            error_exit(msg)
        # make new node, saves it in node_tree.
        cns = parent.mstats[gid]['ns']
        qid = "%s:%s" % (cns, id)
        sgd = { 'id': gid, 'type': 'group', 'ns':cns, 'qid':qid, 'df':parent.mstats[gid]['df'] }
        grp = Group(self, sgd, name, path, attrs, parent, link_info)
        return grp
                
        
#     def make_group_old(self, qid, name='', path='', attrs={}, link='', abort=True):
#         """ Creates groups that are in the top level of the definition structures.
#             qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
#             name - name of group in case name is not specified by id (id is in <angle brackets>)
#                 *OR* Group node linking to
#                 *OR* pattern to specify link: link:path or extlink:file,path
#             path - specified path of where group should be created.  Only needed if
#                 location ambiguous
#             attrs - attribute values for group that are specified in API call.  Either
#                 dictionary or list that will be converted to a dictionary.
#             link - specified link, of form link:path or extlink:file,path.  Only needed
#                 if name must be used to specify local name of group
#             abort - If group already exists, abort if abort is True, otherwise return previously
#                 existing group."""
#         gqid = qid + "/"
#         sdef = self.get_sdef(gqid, self.default_ns, "referenced in make_group")
#         sdef['top'] = True  # flag this corresponds to a top-level node for a structure
#         id = sdef['id']
#         ns = sdef['ns']
#         path = self.deduce_path(id, ns, path)
#         if not abort:
#             id_noslash = id.rstrip('/')  # could be different from gqid if namespace present
#             grp = self.get_existing_group(path, id_noslash, name)
#             if grp:
#                 # found already existing group
#                 return grp
#         link_info = self.extract_link_info(name, link, Group)
#         # create the group
#         # parent = None  # no parent since this node created from File object (top level)
#         parent = self.get_parent_group(path)
#         grp = Group(self, sdef, name, path, attrs, parent, link_info)
#         return grp
        
    def get_existing_group(self, path, id, name):
        """ Return existing Group object if attempting to create group again, otherwise,
        return None.  This called by make_group to check for existing group if abort
        is False."""
        v_id = re.match( r'^<[^>]+>$', id) # True if variable_id (in < >)
        lookup_name = name if v_id else id
        full_path = self.make_full_path(path, lookup_name)
        node = self.get_node(full_path, False)
        if node and node.sdef['type'] == 'group':
            # found already existing group
            return node
        else:
            return None
    
    
    def select_path(self, id, ns, idlocs, path):
        """Select path from list of paths in idlocs and specified_path.
        idlocs is an array possible paths.
        if idlocs has more than one element, then parameter
        path must match one of them in order to disambiguate which
        one is correct.  Note: entries in idlocs are absolute paths WITH
        a trailing slash.
        Return matching path or abort if no match found."""
        possible_paths = idlocs
        if path != '':
            path_sl = path if path.endswith("/") else path + "/"
            if path_sl not in idlocs:
                print "** Error"
                print "Specified path '%s' not in name space '%s' locations for id '%s'" % (path, ns, id)
                print "expected one of: %s" % possible_paths
                error_exit()
        else:
            if len(idlocs) > 1:
                print "** Error"
                print "Path not specified for '%s', but must be since" % id
                print " there are multiple possible locations: %s" % possible_paths
                error_exit()
            path_sl = idlocs[0]
        return path_sl
        
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
            for method 1).
        Return value(link_info) is either:
            None - no link
            { 'node': <node_linking_to> }  - linking to an internal node
            { 'extlink': (file, path) } - linking to a path within an external file
        """
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
        return "link_info" dictionary"""
        if isinstance(link, (str, unicode)):
            if re.match( r'^link:', link):
                # assume intending to specify a link, now match for rest of pattern            
                matchObj = re.match( r'^link:([^\n\t]+)$', link)
                if matchObj and len(link) < 512:
                    path =  matchObj.group(1)
                    node = self.get_node(path)
                    link_info = {'node': node}
                    return link_info
                else:
                    # accept pretty much any characters in link path
                    print ("** Error, invalid path specified in link string, must be "
                        "less than 512 chars and not have new line or tabs")
                    print " link string is: '%s'" % link
                    error_exit()
            elif re.match( r'^extlink:', link):
                # assume intending to specify an external link, now match for rest of pattern

                # using tab as separator (allows spaces and comma's in name or path:
                matchObj = re.match( r'^extlink:\s*([^\t]+)\t([^\t]+)$', link)
                if not matchObj:
                    # using comma or comma and space
                    matchObj = re.match( r'^extlink:\s*([^,]*[^ ,])[ ,]([^,]+)$', link)               
                if matchObj:
                    file = matchObj.group(1)
                    path = matchObj.group(2)
                    link_info = {'extlink': (file, path)}
                    return link_info
                else:
                    print "** Error, invalid file or path specified in extlink string"
                    print " must not have spaces and file name must not end in comma"
                    print "extlink string is: '%s'"% link
                    error_exit(1)
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
        parent - parent group if creating node inside (calling from) a group """
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
                error_exit()
            sdef['custom'] = True
            if parent is None:
                sdef['top'] = True
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
                    msg = ("Specified absolute path '%s' when creating node\n"
                        "inside group, with namespace '%s'") % (full_path, ns)
                    error_exit(msg)
                # ok, relative path is specified, make full path using parent
                full_path = self.make_full_path(parent.full_path, full_path)                       
            else:
                # not creating from inside a group.  Require absolute path, or default to __custom location
                if full_path == '' or full_path[0] != "/":
                    custom_ns = ns if '__custom' in self.idlookups[ns] else (
                        self.default_ns if '__custom' in self.idlookups[self.default_ns] else None)
                    if not custom_ns:
                        print ("** Error:  Attempting to make '%s' but path is relative and\n"
                            "'__custom' not specified in namespace '%s' or default namespace '%s'") % (
                            full_path, ns, self.default_ns)
                        print "id_lookups is"
                        pp.pprint(self.idlookups)
                        error_exit()
                    custom_loc = self.idlookups[custom_ns]['__custom']
                    if len(custom_loc) > 1:
                        raise ValueError(("** Error:  '__custom' is specified in more than location "
                            "in namespace '%s'") % custom_ns)             
                    default_custom_path = custom_loc[0]
                    full_path = self.make_full_path(default_custom_path, full_path)
            # split full path back to path and group name
            matchObj = re.match( r'^(.*/)([^/]*)$', full_path)
            if not matchObj:
                msg = "** Error: Unable to find match pattern for full_path in '%s'" % full_path
                error_exit(msg)
            path = matchObj.group(1).rstrip('/')
            if path == '':
                path = '/'
            id_str = matchObj.group(2)
            # make sdef for custom node.  Has empty definition (df)
            type = 'group' if gslash == '/' else 'dataset'
            sdef = { 'type': type, 'qid': qid, 'id':id_str + gslash, 'ns':ns, 'df': {}, 'custom': True }
            if parent is None:
                sdef['top'] = True
            name = ''
        return (sdef, name, path)
            
    def make_custom_group(self, qid, name='', path='', attrs={}, attrs_shape=None):
        """ Creates custom group.
            qid - qualified id of structure or name of group if no matching structure.
                qid is id with optional namespace (e.g. core:<...>).  Path can
                also be specified in id (path and name are combined to produce full path)
            name - name of group in case id specified is in <angle brackets>
            path - specified path of where group should be created.  If not given
                created in group with dataset named "__custom" specified in schema.
            attrs - attribute values for group that are specified in API call.
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
            """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.deflatten_attrs(attrs, attrs_shape)
        gslash = "/"
        sdef, name, path = self.get_custom_node_info(qid, gslash, name, path) 
        # parent = self.get_parent_group(path)
        parent = self.get_parent_group(path, self.default_ns, self.default_ns)
        grp = Group(self, sdef, name, path, attrs, parent)
        return grp
        
    def deflatten(self, value, shape):
        """Convert value from type array.array to numpy array and reshape if shape
        specified.  This included to convert values passed in from matlab
        (which have type array.array, and cannot have more than one dimension)
        to numpy array types that are handled by h5py.  Background: matlab
        does not pass multidimensional arrays into Python, only 1-d arrays.
        To solve this, the multidimensional array is converted to a 1-d array,
        then converted back to a multidimensional array (done here).
        """
        assert isinstance(value, (array.array, tuple)), "deflatten value (%s) is unexpected type: '%s'" % (
            value, type(value))
        if isinstance(value, tuple) and len(value) == 0:
            npval = []  # set to empty list so will generate empty 1-D array in HDF5
            return npval
        else:
            npval = np.array(value)
        if isinstance(shape, (tuple, list, array.array)):
            # reverse shape to switch ordering from matlab (column major) to python (row major)
            # rshape = list(reversed(shape))
            # print "before reshape to shape %s, vals=%s" % (shape, npval[0:15])
            npval = npval.reshape(shape)
        return npval
        
    def deflatten_attrs(self, attrs, attrs_shape):
        """ Convert attribute values passed in from matlab from 1-d array back to
        original array size.  This done because multidimensional arrays cannot be
        passed from matlab to python, only 1-d arrays.  So multidimensional arrays
        are converted to 1-d in matlab (by function flatten_attrs) and converted
        back to the original shape by this function."""
#         print "in deflatten_attrs, attrs="
#         print attrs
#         print "attrs_shape="
#         print attrs_shape
        for i in range(len(attrs_shape)):
            cvs_shape = attrs_shape[i]
            if cvs_shape:
                # this attribute may need to be converted
                if cvs_shape.endswith(',') and cvs_shape.count(',') == 1:
                    # this is either empty, scalar or 1-d.  Shape not needed in
                    # deflatten.  But must call deflatten to convert value type
                    # e.g. from tuple or array.array to numpy array.
                    shape = ''
                else:
                    # this is a multidimensional array.  Need to provide shape 
                    # (which is encoded as a cvs string, e.g. "3,4") to
                    # the deflatten function as a list of integer values
                    shape = [int(x) for x in cvs_shape.split(',')]
                ival = (i*2)+1
                attrs[ival] = self.deflatten(attrs[ival], shape)
                

    def set_dataset(self, qid, value, name='', path='', attrs={}, dtype=None, compress=False,
         shape=None, attrs_shape = None):
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
            shape - only used when called from matlab.  Specifies shape that 1-d value
                should be converted ot.  (matlab can only pass in 1-d arrays).
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
        """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.deflatten_attrs(attrs, attrs_shape) 
#         print "called f.set_dataset, qid='%s', name='%s', dtype='%s', shape='%s'" % (
#                 qid, name, dtype, shape)
        if isinstance(value, (array.array, tuple)):
            value = self.deflatten(value, shape)
        # (ns, id) = self.parse_qid(qid, self.default_ns)
        if ':' in qid:
            (ns, id) = self.parse_qid(qid, self.default_ns)
        else:
            id = qid
            ns = None
        # idlocs = self.get_idlocs(qid, ns, "referenced in make_group")
        idlocs = self.get_idlocs(id, self.default_ns, "referenced in set_dataset")
        # path = self.select_path(qid, ns, idlocs, path)
        path = self.select_path(id, self.default_ns, idlocs, path)
        link_info = self.extract_link_info(value, None, Dataset)
#         print "called set_dataset, qid='%s', idloc='%s', path=%s" % (qid, idlocs, path)
        # parent = self.get_parent_group(path, ns, self.default_ns)
        parent = self.get_parent_group(path, self.default_ns, self.default_ns)
#         print "in set_dataset, parent full_path=%s" % parent.full_path
        # for now assume can set dataset using definition inside mstats
        assert hasattr(parent, 'mstats'), "mstats not found in file set_dataset of %s" % path
        if id not in parent.mstats:
            msg = "Did not find '%s' in parent mstats in file set_dataset for: %s" % (id, path)
            error_exit(msg)
        if 'df' not in parent.mstats[id]:
            msg = "Did not find df in mstats[%s] in file make_group for: %s" %(id, full_path)
            error_exit(msg)
        # namespace mismatch allowed when using extensions
        if ns is not None and ns != parent.mstats[id]['ns']:
            msg = "Supplied namespace '%s' in set_dataset '%s' does not match that of definition (%s)" % (
                ns, qid, parent.mstats[id]['ns'])
            error_exit(msg)
        # assert parent.mstats[qid]['ns'] == ns, "namespace mismatch in file set_dataset for: %s" % path
        # make new node, saves it in node_tree.
        cns = parent.mstats[id]['ns']
        qid = "%s:%s" % (cns, id)
        sgd = { 'id': id, 'type': 'dataset', 'ns':cns, 'qid':qid, 'df':parent.mstats[id]['df'] }
        ds = Dataset(self, sgd, name, path, attrs, parent, value, dtype, compress, link_info)
#         print "created dataset, id=%s, full_path=%s" % (id, ds.full_path)
        return ds        
             
             
#     def set_dataset_old(self, qid, value, name='', path='', attrs={}, dtype=None, compress=False):
#         """ Creates datasets that are in the top level of the definition structures.
#             qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
#             value - value to store in dataset, or Dataset object (to link to another dataset,
#                *OR* a string matching pattern: link:<path> or extlink:<file>,<path>
#                to specify respectively a link within this file or an external link.
#             name - name of dataset in case name is unspecified (id is in <angle brackets>)
#             path - specified path of where dataset should be created.  Only needed if location ambiguous
#             attrs - attributes (dictionary of key-values) to assign to dataset
#             dtype - if provided, included in call to h5py.create_dataset
#             compress - if True, compression provided in call to create_dataset
#         """
#         sdef = self.get_sdef(qid, self.default_ns, "referenced in set_dataset") 
#         sdef['top'] = True  # flag created from file object; corresponds to top-level node of a structure 
#         id = sdef['id']
#         ns = sdef['ns']
#         path = self.deduce_path(id, ns, path)
#         link_info = self.extract_link_info(value, None, Dataset)
#         # create the dataset
#         # parent = None  # no parent since this node created from File object (top level)
#         parent = self.get_parent_group(path)
#         ds = Dataset(self, sdef, name, path, attrs, parent, value, dtype, compress, link_info)
#         # print "created dataset, qid=%s, name=%s" % (qid, ds.name)
#         return ds
       
    def set_custom_dataset(self, qid, value, name='', path='', attrs={}, dtype=None, 
        compress=False, shape=None, attrs_shape=None):
        """ Creates custom datasets that are in the top level of the definition structures.
            qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
            name - name of dataset in case name is unspecified (id is in <angle brackets>)
            path - specified path of where dataset should be created if not specified in qid
            attrs - attributes (dictionary of key-values) to assign to dataset
            dtype - if provided, included in call to h5py.create_dataset
            compress - if True, compression provided in call to create_dataset
            shape - only used when called from matlab.  Specifies shape that 1-d value
                should be converted ot.  (matlab can only pass in 1-d arrays).
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
        """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.deflatten_attrs(attrs, attrs_shape) 
        if isinstance(value, (array.array, tuple)):
            value = self.deflatten(value, shape)
        gslash = ""
        sdef, name, path = self.get_custom_node_info(qid, gslash, name, path)
        # parent = self.get_parent_group(path) 
        parent = self.get_parent_group(path, self.default_ns, self.default_ns)
        ds = Dataset(self, sdef, name, path, attrs, parent, value, dtype, compress)
        return ds    
    
    
    def validate_file(self):
        """ Validate that required nodes are present.  This is done by checking
        nodes referenced in id_lookup structure (built from 'locations' section
        of specification language) and also by checking the tree of all nodes
        that are included in the "node_tree" array. """
        # explanations are used in print_message_list
        global explanations
#         print "\n******"
#         print "Validation messages follow."
        # find_links.show_links(self.links)
        # find_links.show_autogen(self)
        find_links.validate_autogen(self)
         # vi == validation information.  Used to store information about validation  
        vi = {
            # errors
            'missing_nodes': {'group': [], 'dataset': []},
            'missing_attributes': [],
            'incorrect_attribute_values': [],
            # 'added_nodes_missing_flag': {'group': [], 'dataset': []},
            'custom_nodes_missing_flag': {'group': [], 'dataset': []},
            'extension_nodes_missing_flag': {'group': [], 'dataset': []},
            # 'schema_id_errors': [],
#             'node_identification_errors': [],
            # warnings
            # 'dangling_external_links': [],
            'missing_recommended': {'group': [], 'dataset': []},
            'recommended_attributes_missing': [],
            'recommended_attributes_empty': [],
            'required_attributes_empty': [],
            'added_attributes_not_described_by_extension': [],
            # Info
            # 'added_nodes_with_flag': {'group': [], 'dataset': []},
            'identified_custom_nodes': {'group': [], 'dataset': []},
            'identified_extension_nodes': {'group': [], 'dataset': []},
            'added_attributes_described_by_extension': [],
            'links': {},
            'ext_links': {},
            'explanations': {}
            }
        # check "locations" section of specification(s) for missing nodes
        # 'id_lookups' has information about nodes created there
#         for ns in self.id_lookups:
#             for id in self.id_lookups[ns]:
#                 for path in self.id_lookups[ns][id]:
#                     qty = self.id_lookups[ns][id][path]['qty']
#                     type = self.id_lookups[ns][id][path]['type']
#                     count = len(self.id_lookups[ns][id][path]['created'])
#                     if qty in ('!', '+') and count == 0:
#                         node_info = self.format_node_info(ns, path, id)
#                         vi['missing_nodes'][type].append(node_info)
        # check entire node_tree (all nodes created)
        self.validate_nodes(self.node_tree, vi)
        # to_check = [self.node_tree, ]
        while False:  #  to_check:  # former code if have top and locations
            group = to_check.pop(0)
            if 'top' in group.sdef and group.sdef['top']:
            #    self.validate_nodes(group, missing_nodes, custom_nodes, links)
                self.validate_nodes(group, vi)
            elif group.link_info:
                # for now, ignore links.  TODO: validate link target is correct type
                continue
            else:
#                 if (group.full_path != "/" and not
#                     ('location' in group.sdef and group.sdef['location'])):
#                     # group is not at top, also does not have location flag.  Is unknown
#                     vi['unknown_nodes']['group'].append(group.full_path)
                for id in group.mstats:
                    if group.mstats[id]['type'] == 'group':
                        to_check.extend(group.mstats[id]['created'])
                    else:
                        # is dataset
                        for ds in group.mstats[id]['created']:
                            if 'top' in ds.sdef and ds.sdef['top']:
                                self.validate_nodes(ds, vi)
#                             else:
#                                 # dataset not in top, I think this should not happen
#                                 vi['unknown_nodes']['dataset'].append(ds.full_path)
        # check ids that are an absolute path for missing
        self.check_path_ids_for_missing(vi)
        # display reports
        # print "links {target: [sources]}"
        # pp.pprint(vi['links'])
        # self.print_message_list(vi['links'], "Links {target: [sources]}")
        # pass by global variable for now.
        explanations = vi['explanations']
        # display results
        # errors
        total_errors = (len(self.error) 
            + len(vi['missing_nodes']['group']) + len(vi['missing_nodes']['dataset'])
            + len(vi['missing_attributes'])
            + len(vi['incorrect_attribute_values'])
            # + len(vi['added_nodes_missing_flag']['group'])
            + len(vi['custom_nodes_missing_flag']['group'])
            + len(vi['custom_nodes_missing_flag']['dataset'])
            + len(vi['extension_nodes_missing_flag']['group'])
            + len(vi['extension_nodes_missing_flag']['dataset'])
            # + len(vi['added_nodes_missing_flag']['dataset'])
            # + len(vi['schema_id_errors'])
#             + len(vi['node_identification_errors'])
            )
        if self.options['verbosity'] == 'all':
            print "\n******"
            print "Validation messages follow."
            self.display_report_heading(total_errors, "error", zero_msg="Good")
            self.print_message_list(self.error, "Miscellaneous errors", zero_msg="Good")
            self.report_problems(vi['missing_nodes'], "missing", zero_msg="Good")
            self.print_message_list(vi['missing_attributes'], "attributes missing", zero_msg="Good")
            self.print_message_list(vi['incorrect_attribute_values'], 
                "Incorrect attribute values", zero_msg="Good")
            if self.options['identify_custom_nodes']:
                aid, val = self.options['custom_node_identifier']
                cni_msg = "custom missing attribute %s=%s" % (aid, val)
                self.report_problems(vi['custom_nodes_missing_flag'], cni_msg, zero_msg="Good")
            if self.options['identify_extension_nodes']:
                aid = self.options['extension_node_identifier']
                eni_msg = "defined in extension, but missing attribute %s" % aid
                self.report_problems(vi['extension_nodes_missing_flag'], eni_msg, zero_msg="Good")            
    #         schema_id_attr = self.options['schema_id_attr']
#         cnms_msg = "added missing attribute '%s=Custom'" % schema_id_attr
#         self.report_problems(vi['added_nodes_missing_flag'], cnms_msg, zero_msg="Good")
#         self.print_message_list(vi['schema_id_errors'], 
#             "Errors with attribute '%s'" % schema_id_attr, zero_msg="Good")
#         self.print_message_list(vi['node_identification_errors'], 
#             "Errors with node identification attribute", zero_msg="Good")

        # warnings
        total_warnings = (len(self.warning)
            + len(vi['missing_recommended']['group'])
            + len(vi['missing_recommended']['dataset'])
            + len(vi['recommended_attributes_missing'])
            + len(vi['recommended_attributes_empty'])
            + len(vi['required_attributes_empty'])
            + len(vi['added_attributes_not_described_by_extension']))
        if self.options['verbosity'] == 'all':
            self.display_report_heading(total_warnings, "warning", zero_msg="Good")
            self.print_message_list(self.warning, "Miscellaneous warnings", zero_msg="Good")
            self.report_problems(vi['missing_recommended'], "missing", 
                 zero_msg="Good", qualifier="recommended")
            self.print_message_list(vi['recommended_attributes_missing'],
                "recommended attributes missing", zero_msg="Good")
            self.print_message_list(vi['recommended_attributes_empty'],
                "recommended attributes empty", zero_msg="Good")
            self.print_message_list(vi['required_attributes_empty'],
                "required_attributes_empty", zero_msg="Good")
            self.print_message_list(vi['added_attributes_not_described_by_extension'], 
                'added attributes not described by extension', zero_msg="Good")
            # Information about added items:
        total_added_correctly = (len(vi['identified_custom_nodes']['group'])
            + len(vi['identified_custom_nodes']['dataset'])
            + len(vi['identified_extension_nodes']['group'])
            + len(vi['identified_extension_nodes']['dataset'])
            + len(vi['added_attributes_described_by_extension']))
        if self.options['verbosity'] == 'all':
            self.display_report_heading(total_added_correctly, "addition")
            if self.options['identify_custom_nodes']:
                caid, cval = self.options['custom_node_identifier']
                self.report_problems(vi['identified_custom_nodes'], 
                    "custom and identifieed by attribute %s=%s" % (caid, cval))
            if self.options['identify_extension_nodes']:
                eaid = self.options['extension_node_identifier']
                self.report_problems(vi['identified_extension_nodes'], 
                    "defined by extension and identified by attribute %s" % eaid)           
            self.print_message_list(vi['added_attributes_described_by_extension'], 
                "added attributes described by extension")
            print "** Summary"
        if self.options['verbosity'] in ('all', 'summary'):
            print "%i errors, %i warnings, %i additions" %(total_errors, total_warnings, total_added_correctly)
            if total_errors == 0:
                print "passed validation check (no errors)"
            else:
                print "failed validation check (at least one error)"
        # return dict giving number of total errors, warnings and added
        validation_result = {'errors':total_errors, 'warnings':total_warnings,
            'added': total_added_correctly}
        return validation_result   
        

    def display_report_heading(self, count, name, zero_msg = None):
        # Create message text like:  "** No errors.  - Great!" or "** One error."
        # or "34 errors.".  count is the number of errors or other count.
        # zero_msg is the message to append if count is zero
        if count == 0:
            msg = "** No %ss." % name
            if zero_msg:
                msg = msg + " -- %s" % zero_msg
        elif count == 1:
            msg = "** one %s." % name
        else:
            msg = "** %i %ss." % (count, name)
        print msg
            

    def check_path_ids_for_missing(self, vi):
        """Checks all path id's for missing.  These only checked here if parent
        was never made (thus would not be in node_tree).  Those that have parent
        node in node_tree are checked by validate_nodes.
        """
        for ns in self.ddef:
            structures = self.ddef[ns]['structures']
            for id in structures:
                if id[0] != '/' or id == "/":
                    # not absolute path or not root
                    continue
                parent_path, basename = self.get_name_from_full_path(id)
                if parent_path not in self.path2node:
                    # get quantity, default is required
                    qty = structures[id]['_qty'] if '_qty' in structures[id] else '!'
                    if qty in ('+', '!', '^'):
                        lkey = 'missing_recommended' if qty == "^" else 'missing_nodes'
                        type = 'group' if id.endswith('/') else 'dataset'
                        ns_prefix = ns+":" if ns != self.default_ns else ""
                        path_msg = ns_prefix + id
                        vi[lkey][type].append(path_msg)

    
    def format_node_info(self, ns, path, id):
        """ Formats information about a node (namespace, path, id), suppressing
        namespace if it matches the default namespace"""
        sns = ns + ":" if ns != self.default_ns else ""
        spath = path if path != "/" else ""
        ninfo = "%s%s/%s" % (sns, spath, id)
        return ninfo
        
       
    def validate_nodes(self, root_node, vi):
        """ Check if node contains all required components or if it is custom."""
        to_check = [root_node]
        while len(to_check) > 0:
            node = to_check.pop(0)
            custom = 'custom' in node.sdef and node.sdef['custom']
            type = node.sdef['type']
#             if node.full_path == "/stimulus/templates/locally_sparse_noise_image_stack":
#                 import pdb; pdb.set_trace()
            if custom:
                if (self.options['identify_custom_nodes']):
                    caid, cval = self.options['custom_node_identifier']
                    if not (caid in node.h5attrs and cval == node.h5attrs[caid]):
                        if type not in ('group', 'dataset'):
                            # type must be external link.  Ignore here. Warning will be
                            # displayed elsewhere
                            # print "TMP: %s, type='%s', sdef=" % (node.full_path, type)
                            # pp.pprint(node.sdef)
                            pass 
                        else:
                            vi['custom_nodes_missing_flag'][type].append(node.full_path)
                            if 'h5nsig' in node.sdef:
                                # this was inside a non-custom node.  Create explanation
                                # for why is was not detected as non-custom
                                explanation = self.explain_why_custom(node)
                                if explanation:
                                    vi['explanations'][node.full_path] = explanation
                    else:
                        vi['identified_custom_nodes'][type].append(node.full_path)
            elif node.sdef['ns'] != self.default_ns and self.options['identify_extension_nodes']:
                # this node defined in an extension and should be identified by an attribute
                eaid = self.options['extension_node_identifier']
                found_match = False
                if eaid in node.h5attrs:
                    found_val = node.h5attrs[eaid]
                    expected_val = "%s:%s" % (node.sdef['ns'], node.sdef['id'])
                    if found_val == expected_val or found_val == node.sdef['ns']:
                        found_match = True
                if found_match:
                    vi['identified_extension_nodes'][type].append(node.full_path)
                else:
                    vi['extension_nodes_missing_flag'][type].append(node.full_path)
            self.validate_attributes(node, vi)
            if node.link_info:
                # this node is link to another node
                link_info = node.link_info
                if 'node' in link_info:
                    if link_info['node'] is None:
                        # link was expected but not present. Error should already be generated for this
                        continue
                    # normal link
                    target_path = node.link_info['node'].full_path
                    find_links.add_item(vi['links'], target_path, node.full_path)
                elif 'extlink' in link_info:
                    # external link
                    target = link_info['extlink']
                    # See if can access attribute in external link
                    try:
                        tnode = self.file_pointer[node.full_path]
                    except KeyError:
                        # unable to open extlink
                        msg = "%s: external link target not found: file='%s', path='%s'" % (
                            node.full_path, target[0], target[1])
                        self.warning.append(msg)
                    find_links.add_item(vi['ext_links'], target, node.full_path)
                else:
                    error_exit("Unknown link_info type: %s" % link_info)
            elif type == 'group':
                # check if any nodes required in this group are missing using local qty info
                # first, get list of id's that are referenced in "_required" specification
                required_info = self.get_required_info(node)
                required_referenced = required_info['id_status'] if required_info else {}
                exclude_info = self.get_exclude_info(node)
                for id in sorted(node.mstats.keys()):
                    idinfo = node.mstats[id]
                    qty = idinfo['qty']
                    type = idinfo['type']
                    created = idinfo['created']
                    is_excluded = exclude_info and id in exclude_info['ids']
                    if is_excluded:
                        if not created:
                            # is excluded and was not created.  Good.
                            continue
                        else:
                            # is excluded but was created.  That may be an error or warning
                            ex_qty = exclude_info['ids'][id]
                            assert ex_qty in ('?', '!', '^')
                            if ex_qty == '?':
                                # creating is optional, so no error or warning
                                continue
                            verb = "must" if ex_qty == "!" else "should"
                            msg = "%s - '%s' %s not be present within '%s'" % (
                                created[0].full_path, id, verb, exclude_info['path'])
                            if ex_qty == '!':
                                self.error.append(msg)
                            else:
                                self.warning.append(msg)
                    if id.rstrip('/') not in required_referenced and not custom and len(created) == 0:
                        # this id not referenced in "_required" spec
                        # if it was, don't create error / warning here; let function check_required validate 
                        id_full_path = self.make_full_path(node.full_path, id)
                        if qty in ('!', '+'):
                            vi['missing_nodes'][type].append(id_full_path)
                        elif qty == "^":
                            vi['missing_recommended'][type].append(id_full_path)
                    # add nodes to list to check
                    to_check.extend(sorted(created))
                # check for "_required" specification
                self.check_required(node)
            elif type == "dataset":
                self.validate_dataset(node)
            else:
                # should never happen
                error_exit("unknown type in validation: %s" %type)

     
    def validate_attributes(self, node, vi):
        """ Check for any attributes that are required or recommended but do not
        have a value *or* are const and have an incorrect value.  Also record
        any described by an extension"""
        if not hasattr(node, "attributes"):
            # this node does not have any attributes
            return
        ats = node.attributes  # convenient shorthand
        # get custom_node_identifier and extension_node_identifier in list so can easily
        # skip checking these (assume they are checked for when validating node)
        added_nodes_identifiers = []
        if self.options['identify_extension_nodes']:
            added_nodes_identifiers.append(self.options['extension_node_identifier'])
        if self.options['identify_custom_nodes']:
            cni = self.options['custom_node_identifier'][0]
            if cni not in added_nodes_identifiers:
                added_nodes_identifiers.append(cni)
        for aid in ats:
            if 'autogen' in ats[aid]:
                # values in autogen attributes automatically included
                continue
#             if 'optional' in ats[aid] and ats[aid]['optional']:
#                 # this attribute is optional.  Don't check if it's present
#                 continue
            qty = ats[aid]['qty']
            if qty == "custom":
                # attribute added but not described by extension
                msg = "%s: (%s) %s" %(node.full_path, node.sdef['type'], aid)
                vi['added_attributes_not_described_by_extension'].append(msg)
                continue
            assert qty in ('?', '!', '^'), "attribute qty must be one of: '!', '^', '?' or 'custom'"
            const = 'const' in ats[aid] and ats[aid]['const']
            if const:
                assert 'nv' not in ats[aid], "%s: attribute [%s] is type const, but nv specified" % (
                    node.full_path, aid)
                const_val = ats[aid]['value']
            val_present = aid in node.h5attrs
            if val_present:
                aval = node.h5attrs[aid]  # actual value
            # check if described by extension
            last_source_ns = ats[aid]['source'][-1].split(':')[0] if 'source' in ats[aid] else None
            if val_present and last_source_ns and last_source_ns != self.default_ns:
                msg = "%s: (%s) %s" %(node.full_path, node.sdef['type'], aid)
                vi['added_attributes_described_by_extension'].append(msg)
            # if attribute is required or recommended, check if present
            if qty in ('!', '^'):           
                if not val_present:
                    if aid in added_nodes_identifiers:
                        # this attribute id is one used for identifying added nodes (custom or extension)
                        # don't flag the value missing here.  Assume that will be done in routine "validate_node"
                        continue
                    if const:
                        msg = "%s: (expected %s='%s')" %(node.full_path, aid, eval)
                    else:
                        msg = "%s - %s" % (node.full_path, aid)
                    elist = 'missing_attributes' if qty == "!" else 'recommended_attributes_missing'
                    vi[elist].append(msg)
                    continue
                if find_links.values_match(node.h5attrs[aid], ""):
                    # is present but empty; generate a warning or error.
                    msg = "%s - %s" % (node.full_path, aid)
                    elist = 'required_attributes_empty' if qty == "!" else 'recommended_attributes_empty'
                    vi[elist].append(msg)
                    continue
            # either qty == '?' or value is present or both
            # if value is present and const, check to see if it matches expected value
            if val_present and const and not find_links.values_match(aval, const_val):
                msg = "%s: %s\nexpected: '%s'\nfound: '%s', " % (node.full_path, aid, const_val, aval)
                vi['incorrect_attribute_values'].append(msg)
                
    def validate_dataset(self, node):
        """ Check dataset in hdf5 file conforms to specification definition.
        """
        if self.options['storage_method'] == 'commands':
            # unable to check if called from matlab bridge because h5py not available
            return
        if 'custom' in node.sdef and node.sdef['custom']:
            # custom node.  No specification to validate with
            return
        if 'autogen' in node.dsinfo:
            # this dataset generated by autogen.  Validation done in validate_autogen, not here
            return
        ddt = node.dsinfo['ddt']  # decoded data type (from specification)
        found_dtype = str(self.file_pointer[node.full_path].dtype)
        # check for type match
        if re.match(r'^\|V\d+$', found_dtype):
            # if found dtype like "|V537350" it's type "opaque".  This corresponds to binary
            found_dtype = "binary"
        types_match = valid_dtype(ddt, found_dtype)
        if not types_match:
            # types do not match.  This might be caused by a string type, stored
            # as a dtype "object" which routine "valid_dtype" cannot interpret.
            # first see if expected value is string
            if ddt['type'] == 'text':
                # Yes, expected type is text. Check for string using low-level h5py
                nid = self.file_pointer[node.full_path].id
                h5type = nid.get_type()
                if isinstance(h5type, h5py.h5t.TypeStringID):
                    # yes, hdf5 type is string.  Data types match
                    return
            if ddt['type'] == 'binary':
                # binary data can also be stored as integer rather than opaque
                if 'int' in found_dtype:
                    # binary type stored as integer, this is ok
                    return
            # types don't match, or there is another unknown type
            msg = ("%s -- data type in hdf5 file (%s) does not match specification type (%s)" %
                (node.full_path, found_dtype, ddt['type']))
            # sometimes might be 'object_'.  What is this?
            self.error.append(msg)
            return
        # Now check for minimum size requirement
        if found_dtype == 'string_':
            return
        min_size = node.dsinfo['ddt']['minimum_size']
        if not min_size:
            # minimum size was not specified, so don't check
            return
        pat = "([a-z]+)(\d+)"
        match = re.match(pat, found_dtype)
        if not match:
            msg = "%s: unable to split hdf5 dtype (%s) into type and size." % (node.full_path, found_dtype)
            f.warning.append(msg)
            return
        typ = match.group(1)
        siz = int(match.group(2))
        if siz < min_size:
            msg = "%s: Data type (%s) has size (%i) less than minimum (%i)" % (node.full_path,
                found_dtype, siz, min_size)
            self.error.append(msg)
            
    def get_required_info(self, node):
        """ Return information about _required specification for this node.
        required_info is:
        { 'spec': { <required_specification> }
          'id_status': { 'id1': <status1>, 'id2': <status2>, ... }}
        where
          'spec' are the _required specification elements that are not excluded (see below)
          '<statusN>  == True if id is present, False otherwise
        The list of id's is used to prevent checking for required based
        on local specification (e.g. qty == "!" or "^", or "?") and instead, let
        the check_required function test for required based on the 'global'
        i.e. presence / absences of other members in the group.
        If all variables in a condition_string are excluded (by a
        exclude_in specification), don't return these variables and the specification for
        them (e.g. condition_string, message) since these variables should not be present).
        If there is no required_spec, return None
        """
        if not hasattr(node, 'required'):
            # no 'required' specification.
            return None
        exclude_info = self.get_exclude_info(node)
        excluded_ids = set(exclude_info['ids'].keys()) if exclude_info else set()
        r_ref = set()
        spec = {}
        pattern = re.compile(r'([^\d\W][^/\W]*/?)') # finds identifiers
        ops = set(['AND', 'and', 'XOR', '^', 'OR', 'or', 'NOT', 'not'])
        for rid in node.required.keys():
        # for cm in node.required:
            cm = node.required[rid]
            condition_string = cm[0]
            error_message = cm[1]
            # get each identifier in condition string
            ids_and_ops = set(re.findall(pattern, condition_string))
            ids = ids_and_ops - ops
            if not (ids <= excluded_ids):
                # copy spec
                spec[rid] = cm
                r_ref.update(ids)
        if len(r_ref) == 0:
            assert excluded_ids, "did not find any ids in _required spec, and none were excluded: %s" % node.required
            return None
        id_status = {}
        for id in list(r_ref):
            if id not in node.mstats:
                print ("%s identifier (%s) in _required specification not found "
                        "in group") %(node.full_path, id)
                print "valid options are:\n%s" % node.mstats.keys()
                error_exit()
            present = len(node.mstats[id]['created']) > 0
            id_status[id] = present
        required_info = { "spec": spec, "id_status": id_status }
        return required_info
        
#     def get_required_var_status(self, node):
#         """ Checks if node (which should be a group) has a '_required' specification.
#         If so returns a dictionary mapping each variable in the required spec
#         to True if the member is present, or False if it's not.
#         If there is no required specification, return an empty dictionary"""
#         r_ref = self.get_required_referenced(node)
#         var_status = {}
#         for var in r_ref:
#             if var not in node.mstats:
#                 print ("%s identifier (%s) in _required specification not found "
#                         "in group") %(node.full_path, var)
#                 print "valid options are:\n%s" % node.mstats.keys()
#                 error_exit()
#             present = len(node.mstats[var]['created']) > 0
#             var_status[var] = 'True' if present else 'False'
#         return var_status


    def check_required(self, node):
        """ Check _required specification for required members.
        The "_required" specification allows specifying combinations of members
        in a groups that are required.  Append any error message to file.error"""
        required_info = self.get_required_info(node)
        if not required_info:
            # no 'required' specification.  Do nothing.
            return
        required_spec = required_info['spec']
        id_status = required_info['id_status']
        ce = self.eval_required(required_spec, id_status)
        if ce:
            [condition_string, error_message] = ce
            msg = "%s: %s - %s" % (node.full_path, condition_string, error_message)
            # vi['required_err']['group'].append(msg)
            self.error.append(msg)    
            
        
        # requirement specification has [ [condition, error_message], ...].  i.e.looks like:
        # "_required": { # Specifies required member combinations",
        #     [ ["starting_time XOR timestamps",
        #         "Only one of starting_time and timestamps should be present"],
        #       ["(control AND control_description) OR (NOT control AND NOT control_description)",
        #         "If either control or control_description are present, then both must be present"]],
#         pattern = re.compile(r'([^\d\W][^/\W]*/?)') # finds identifiers
#         for rid in node.required.keys():
#         # for cm in node.required:
#             cm = node.required[rid]
#             condition_string = cm[0]
#             error_message = cm[1]
#             subs = {'AND': 'and', 'XOR': '^', 'OR': 'or', 'NOT': 'not'}
#             # get each identifier in condition string, make dictionary mapping to 'True'
#             # (if item is present) or 'False' (item not present)
#             for id in re.findall(pattern, condition_string):
#                 if id not in subs:
#                     if id not in node.mstats:
#                         print ("%s identifier (%s) in _required specification not found "
#                         "in group") %(node.full_path, id)
#                         print "valid options are:\n%s" % node.mstats.keys()
#                         error_exit()
#                     present = len(node.mstats[id]['created']) > 0
#                     ps = 'True' if present else 'False'
#                     subs[id] = ps
#             result = self.eval_required(condition_string, subs)
#             
#             # use subs array to build boolean expression
# #             text = condition_string + " " # condition string binary, add space to end for re.sub
# #             for key in subs:
# #                 pat = r'\b%s(?=[\) ])' % key  # (pattern requires space or closing ")" after each id
# #                 text = re.sub(pat, subs[key], text)
# #             # now try to evaluate condition string
# #             try:
# #                 result = eval(text)
# #             except SyntaxError:
# #                 print "%s Invalid expression for _required clause:" % node.full_path
# #                 print condition_string
# #                 print "evaluated as: '%s'" % text
# #                 error_exit()
#             if not result:
#                 msg = "%s: %s - %s" % (node.full_path, condition_string, error_message)
#                 # vi['required_err']['group'].append(msg)
#                 self.error.append(msg)          
# #             else:
# #                 print "%s: required OK: %s" %(node.full_path, condition_string)

    

    def eval_required(self, required_spec, var_status):
        """ evaluate the condition strings in required_spec to determine if the all the
        condition strings evaluate to True given the state of variables in var_status.
        required_spec is the '_required' specification in the format specification for
        the group.  var_status is a dictionary mapping each variable referenced in the
        required_spec to either True (if the variable is present) or False if it's not.
        Returns None if all the conditions evaluate to True (e.g. no error) or returns
        a tuple with (condition_string, error_message) if any conditions evaluate to 
        False (indicating an error).
        """
        subs = {'AND': 'and', 'XOR': '^', 'OR': 'or', 'NOT': 'not'}
        # convert var_status from having boolean values to strings "True" or "False"
        sv_status = {key: ("True" if var_status[key] else "False") for key in var_status}
        subs.update(sv_status)
        for rid in required_spec.keys():
            cm = required_spec[rid]
            condition_string = cm[0]
            error_message = cm[1]
            # use subs array to build boolean expression
            text = condition_string + " " # condition string binary, add space to end for re.sub
            for key in subs:
                pat = r'\b%s(?=[\) ])' % key  # (pattern requires space or closing ")" after each id
                text = re.sub(pat, subs[key], text)
            # now try to evaluate condition string
            try:
                result = eval(text)
            except SyntaxError:
                print "%s Invalid expression for _required clause:" % node.full_path
                print condition_string
                print "evaluated as: '%s'" % text
                error_exit()
            if not result:
                return (condition_string, error_message)
        # no errors, return None
        return None
        
    def get_exclude_info(self, node):
        """ Return info about ids referenced in the "exclude_in" specification
        of this node for a location matching the node location.  If found, returns
        exclude_info:
        { 'path': "/path/excluded"
          'ids': { 'id1': <qty1>, 'id2': <qty2>, ...}}
        where <qty> is either:
            '!' - must not be present (error if it is).  Default
            '^' - recommended not be present (warning if it is)
            '?' - optional (can be present or not)
        If no exclude_in found, returns None
        """
        if not hasattr(node, 'exclude_in'):
            # no 'exclude_in' specification.
            return None
        ex_spec = node.exclude_in
        for path in ex_spec:
            assert path.startswith('/'), '_exclude_in path must start with "/": %s in %s' % (
                path, ex_spec)
            if node.full_path.startswith(path):
                # found matching path
                ids = {}
                for id in ex_spec[path]:
                    qty = id[-1]
                    if qty in ('!', '^', '?'):
                        id = id[:-1]
                    else:
                        qty = "!"
                    ids[id] = qty
                exclude_info = { "path": path, "ids": ids }
                return exclude_info
        # no match exclude_info found
        return None
        
    def explain_why_custom(self, node):
        """ Generate explanation for why node was detected as custom (e.g. not recognized).
        Returns explanation or None (if explanation for this not implemented yet).
        """
        msigs = node.parent.msigs    # signature of members this node could have been
        h5nsig = node.sdef['h5nsig'] # signature of this node
#         print "in explain_why_custom for %s" % node.full_path
#         print "msigs="
#         pp.pprint(msigs)
#         print "h5nsig="
#         pp.pprint(h5nsig)
        # find all id's with names matching the node
        matching_ids = []
        for id in msigs:
            idsig = msigs[id]
            if idsig['name'] == h5nsig['name']:
                matching_ids.append(id)
        if not matching_ids:
            # don't give an explanation now
            return None
        # if reach here, must have multiple possibilities with the same
        # name, e.g. a merge with subclasses.  Get the subclass names
        # and constant attributes.  Subclasses will be in parent mstats, 'df' like:
        # {'description': 'Image stack with frames shifted to the common coordinates.','merge': ['<ImageSeries>/']}
        parent = node.parent
        mstats = parent.mstats
        options = []
        for id in matching_ids:
            # subclass = mstats[id]['df']['merge'][0]
            attrs = msigs[id]['attrs']
            options.append(self.get_const_attributes_option(attrs))
        found = str(h5nsig['attrs'])
        msg = "expected one of:\n%s\nfound attributes: %s" % ("\n".join(options), found)
        return msg

    
    def get_const_attributes_option(self, attrs):
        # return dict of attributes with const values
        cattrs = {}
        for aid in attrs:
            if 'const' in attrs[aid] and attrs[aid]['const']:
                value = attrs[aid]['value']
                cattrs[aid] = value
        option = "-- attributes: %s" % (cattrs)
        return option
        
        

        
#     def is_excluded(self, df, loc):
#         """ Checks to see if the node with definition "df" is excluded from location
#         specified by absolute path "loc".  Details: first check to see if definition "df"
#         has an "exclude_in" specification.  If so, check to see if any of the path's
#         specified in the "exclude_in" specification match loc.  Returns one of:
#         False - not excluded
#         Tuple of: (rec_char, location)
#             rec_char is either:
#                 "^" - excluded as a recommendation
#                 "!" - excluded as a requirement
#         """
#         ex_key = "exclude_in"
#         if ex_key not in df:
#             # no exclude_in specification
#             return False
#         ex_spec = df[ex_key]
#         for pspec in ex_spec:
#             assert len(pspec) > 1, "_exclude specification is too short: %s" % df
#             last_char = pspec[-1]
#             if last_char in ('!', '^'):
#                 pspec = pspec[:-1]
#             else:
#                 last_char = "!"
#             if (pspec.startswith('/') and loc.startswith(pspec)) or pspec in loc:
#                 return (last_char, pspec)
#         # did not find matching path spec
#         return False
    
    
    def print_message_list(self, messages, description, quote="", zero_msg=None):
        """Prints description and messages.  "messages" is a list of messages.
        quote is set to a quote character used to enclose each message.
        zero_msg is append to description message for the case of no messages,
        e.g. zero_msg = "Good" to produce:  No errors.  -- Good.
        """
        global explanations
        if not messages:
            msg = "No %s." % description
            if zero_msg:
                msg = msg + " -- %s" % zero_msg
            print msg
        else:
            cmsg = cm.combine_messages(messages)
            if len(cmsg) != len(messages):
                print "%i %s (%i combined):" %(len(messages), description, len(cmsg))
            else:
                print "%i %s:" % (len(messages), description)
            i = 0
            for m in cmsg:
                if m in explanations:
                    m += "\n" + explanations[m]
                i = i + 1
                mt = m.replace("\n", "\n     ")  # insert tab after new line char
                print "%3i. %s%s%s" % (i, quote, mt, quote)
                
                
    def report_problems(self, nodes, problem, zero_msg = None, qualifier=None):
        """ Display nodes that have problems (missing or are custom).
        qualifier is text to put in front of word "group" or "dataset" in
        generated message.  e.g. "recommended" 
        """
        quote = "'"
        for type in ('group', 'dataset'):
            types = type + "s"
            if qualifier:
                description = "%s %s %s" % (qualifier, types, problem)
            else:
                description = "%s %s" % (types, problem)
            self.print_message_list(nodes[type], description, quote, zero_msg)


    def get_node(self, full_path, abort=True):
        """ Returns node at full_path.  If no node at that path then
            either abort (if abort is True) or return None """
        if full_path in self.path2node:
            return self.path2node[full_path]
        elif abort:
            error_exit("Unable to get node for path\n%s" % full_path)
        else:
            return None
            
#     def get_parent_group_scratch(self, path_to_parent):
#         """ Return node for parent group (specified by path to parent).  If parent
#         group does not exist (in node_tree), create sequence of groups (nodes) that
#         goes from root group to the parent.  This done to create groups
#         in node_tree so the parent group exists.
#         Definitions are all assumed to be in ddef default namespace structure.
#         Merged in there by "process_merge_into".
#         This is scratch code.  May be made into new version later.
#         """
#         path_to_parent_no_slash = path_to_parent.strip('/')  # remove slash at end of path_to_parent
#         if path_to_parent_no_slash in self.path2node:
#             return self.path2node[path_to_parent_no_slash]
#         path_parts = path_to_parent_no_slash.split('/')
#         parent = self.node_tree  # root node
#         path = ""
#         # Use an empty attrs dict for all created groups.  
#         attrs = {}
#         ns = self.default_namespace  # use default_namespace for everything
#         for i in range(len(path_parts)):
#             id = path_parts[i]
#             full_path = path + "/" + id
#             if full_path in self.path2node:
#                 parent = self.path2node[full_path]
#             else:
#                 # check for definition of parent group in namespace ns or default_ns
#                 pdef_ns = None
#                 full_path_g = full_path + "/"  # add slash at end to indicate group
#                 if full_path_g in self.ddef[ns]['structures']:
#                     pdef_ns = ns
#                 elif ns != default_ns and full_path_g in self.ddef[default_ns]['structures']:
#                     pdef_ns = default_ns
#                 if pdef_ns:
#                     # found definition in one of the name spaces
#                     pdef = self.ddef[pdef_ns]['structures'][full_path_g]
#                 else:
#                     pdef = None       
#                 # check for definition inside mstats
#                 mstats_df = None
#                 gid = id + "/"
#                 if gid in parent.mstats:
#                     mstats_df = parent.mstats[gid]['df']
#                     mstats_ns = parent.mstats[gid]['ns']
#                 if mstats_df and pdef:
#                     print "Conflicting definitions found for '%s'" % gid
#                     print "Defined in namespace '%s' path: '%s'" % (pdef_ns, full_path_g)
#                     print "and also in namespace '%s' as member of group '%s'" % (mstats_ns, parent.full_path)
#                     error_exit()
#                 if pdef:
#                     sdef = {'id': gid, 'type': 'group', 'qid': None, 'ns':pdef_ns, 'df':pdef}
#                 elif mstats_df:
#                     sdef = {'id': gid, 'type': 'group', 'qid': None, 'ns':mstats_ns, 'df':mstats_df}
#                 else:
#                     # parent not defined.  Must be a custom location.
#                     # make new node, saves it in node_tree.  'location':True indicates
#                     # group created only to complete path to location of parent 
#                     sdef = {'id': gid, 'type': 'group', 'qid': None, 'ns':None, 'df':{}, 'location':True}
#                 name = ""  # name always empty.  It's only used to specify name for variable named group
#                 if path == "":
#                     path = "/"
#                 parent = Group(self, sdef, name, path, attrs, parent)
# #                 print "made parent group: path='%s', gid='%s'" % (path, gid)
#             path = full_path
#         return parent
 
             
    def get_parent_group(self, path_to_parent, ns, default_ns):
        """ Return node for parent group (specified by path to parent).  If parent
        group does not exist (in node_tree), create sequence of groups (nodes) that
        goes from root group to the parent.  This done to create groups
        in node_tree so the parent group exists.
        ns - namespace for definition
        default_ns - namespace to use if definitions to make parent groups
           not found in namespace ns.
        """
#         if path_to_parent == '/acquisition/timeseries/':
#             import pdb; pdb.set_trace()
        path_to_parent_ns = path_to_parent.strip('/')
        if path_to_parent_ns in self.path2node:
            return self.path2node[path_to_parent_ns]
        path_parts = path_to_parent_ns.split('/')
        parent = self.node_tree  # root node
        path = ""
        # Use an empty attrs dict for all created groups.  
        attrs = {}
        for i in range(len(path_parts)):
            id = path_parts[i]
            full_path = path + "/" + id
            if full_path in self.path2node:
                parent = self.path2node[full_path]
            else:
                # check for definition of parent group in namespace ns or default_ns
#                 pdef_ns = None
#                 full_path_g = full_path + "/"  # add slash at end to indicate group
#                 if full_path_g in self.ddef[ns]['structures']:
#                     pdef_ns = ns
#                 elif ns != default_ns and full_path_g in self.ddef[default_ns]['structures']:
#                     pdef_ns = default_ns
#                 if pdef_ns:
#                     # found definition in one of the name spaces
#                     pdef = self.ddef[pdef_ns]['structures'][full_path_g]
#                 else:
#                     pdef = None       
                # check for definition inside mstats
#                 mstats_df = None
                gid = id + "/"
                if gid in parent.mstats:
                    mstats_df = parent.mstats[gid]['df']
                    mstats_ns = parent.mstats[gid]['ns']
#                 if mstats_df and pdef:
#                     print "Conflicting definitions found for '%s'" % gid
#                     print "Defined in namespace '%s' path: '%s'" % (pdef_ns, full_path_g)
#                     print "and also in namespace '%s' as member of group '%s'" % (mstats_ns, parent.full_path)
#                     import pdb; pdb.set_trace()
#                     sys.exit(1)
#                 if pdef:
#                     sdef = {'id': gid, 'type': 'group', 'qid': None, 'ns':pdef_ns, 'df':pdef}
#                 elif mstats_df:
                    sdef = {'id': gid, 'type': 'group', 'qid': None, 'ns':mstats_ns, 'df':mstats_df}
                else:
                    # parent not defined.  Must be a custom location.
                    # make new node, saves it in node_tree.  'location':True indicates
                    # group created only to complete path to location of parent 
                    sdef = {'id': gid, 'type': 'group', 'qid': None, 'ns':None, 'df':{}, 'location':True}
                name = ""  # name always empty.  It's only used to specify name for variable named group
                if path == "":
                    path = "/"
                parent = Group(self, sdef, name, path, attrs, parent)
#                print "made parent group: path='%s', gid='%s'" % (path, gid)
            path = full_path
        return parent
        

       
    def initialize_node_tree(self):
        """ Create the initial root group in variable "node_tree".  This will
        contain all of the h5gate nodes (h5gate Group and Dataset objects)
        that correspond to the hdf5 nodes in the file.  See code for the Node
        object for contents of each entry"""
        # check for '/' id in default name space
        # TODO: Need to allow initializing using definition in non-default name space
        sdef = self.get_sdef("/", self.default_ns)
        if not sdef:
            sdef =  {'type': 'group', 'id':'/', 'qid':None, 'ns':None, 'df':{} }
        name = ''
        path = '/'
        attrs = {}
        parent = None
        root_group = Group(self, sdef, name, path, attrs, parent)
        # self.node_tree = root_group  # not needed, this done in save_node
        
    def create_scratch_group(self):
        """ scratch group is an h5gate group object that does not correspond
        to any group in the hdf5 file.  This is created to have a group object
        which can be used to call methods of the hdf5 group object when reading
        file to load the nodes in the file.  While doing this, it's necessary
        to expand structures in order to figure out which nodes in the file
        correspond to nodes in the specification language definition.  These
        methods are called from function get_expanded_def.
        id value '////scratch_group' is detected in node method "save_node"
        so that the node is not saved to the node_tree or in path2nodes.
        Attribute "scratch_group" is used to prevent saving subclass merges
        and subclass includes during calls to methods of the scratch_group.
        When calling this function, file.read_mode must be true so calls to
        save the node in a data file are not not performed."""
        name = ''
        path = '/'
        attrs = {}
        parent = None
        scratch_sdef = {'type': 'group', 'id':'////scratch_group', 'qid':None, 'ns':None, 'df':{} }
        self.scratch_group = Group(self, scratch_sdef, name, path, attrs, parent)
        self.scratch_group.scratch_group = True
          
        
    #####################################################        
    # Additions for loading data files
    
    def get_expanded_def(self, sdef, name, path):
        """ Get expanded definition of sdef.  This uses a special "group" object
        to allow calling methods of the group object"""
        grp = self.scratch_group
        # following is confusing.  name stored in group is sdef['id'] if not variable id
        # 'name' is used to specify name, only if it's a variable id, e.g. in angle brackets: <>
        id_noslash = sdef['id'].rstrip("/")  # remove trailing slash in case it's a group
        v_id = re.match( r'^<[^>]+>$', id_noslash) # True if variable_id (in < >)
        name = id_noslash if not v_id else name
        # testing for at root.  TODO: See if is principled way to avoid doing this
        if name == '' and path == '':
           # at root
           name = '/'   
        grp.sdef = sdef
        grp.name = name
        grp.path = path
        grp.full_path = self.make_full_path(path, name) if path is not None else None
        grp.attributes = {} # for attributes defined in specification language
        # grp.parent = parent
        grp.description = []
        # grp.parent_attributes = {}
        # print "in file.get_expanded_def; sdef['id']=%s, name='%s', path='%s', full_path='%s'" % (
        #     sdef['id'], name, path, grp.full_path)
        grp.get_expanded_def_and_includes()
        grp.get_member_stats()
        expanded_def = {'mstats': grp.mstats, 'attributes':grp.attributes,
            'description':grp.description, } # 'parent_attributes': grp.parent_attributes}
        return expanded_def

           
    

        
    def make_idsigs(self):
        """ Create an "idsig" (stands for "id signature") for each id in the structures
        part of the specification in each name space.  These are used to figure out
        what id corresponds to hdf5 nodes when reading the file.  (Reading is required for
        for validation or to modify the file).  The idsigs are constructed from the
        definition of the id.  Each idsig has the following format:
          { name: <>  -- name or None if no name, ie. is variable named id
            type: 'group' or 'dataset'
            link: True or False  (true if is a link)
            attrs: { 'key1': 'val1', ... }  -- for all attributes with values specified in definition
            msigs: [ <msig1>, <msig2>, ... ] } -- Signature of each member if id is a group
        where each <msig> has the format:
          { name: <>  -- name of member or None if no name, ie. is variable named id
            type: 'group' or 'dataset'
            link: True or False (true if is a link)
            attrs: { 'key1': 'val1', ... } }  -- for all attributes in member with value specified"""
        idsigs = {}
        for ns in self.ddef.keys():
            idsigs[ns] = self.mk_idsigs_ns(ns)
        return idsigs

    def mk_idsigs_ns(self, ns):
        """ Creates idsigs for structures in namespace ns, that are not an absolute path """
        idsigs_ns = {}
        for id in self.ddef[ns]['structures']:
            df = self.ddef[ns]['structures'][id]
            idsigs_ns[id] = self.mk_idsig(ns, id, df)
        self.filter_sigs(idsigs_ns)
        return idsigs_ns
        
        
        
    def filter_sigs(self, idsigs):
        """ Filter dictionary of idsigs (id signatures) by removing attributes 
        and members that do not help in the matching because they appear in
        more than one id.  This is done to prevent false matches.  It could lead
        to the removal of some attributes / members that could be useful for matching
        if a more sophisticated matching algorithm was used.  If this program is not
        able to match hdf5 nodes to nodes defined using the specification language, and
        if it's possible to identify them using attributes and members; then the
        problem might be fixed by making the filter (done here) less strict and making
        the matching algorithm (in function find_matching_id) made more sophisticated."""
        # Part 1. Remove top level sig attributes that have a value common to more than one sig
        # First, setup av (attr_values) to be:
        #  { "key1-type-name" : { val_1: [id1, id2...], val_2: [id3, ] },
        #    "key2-type-name" { .... } }
        # key is attribute name, type is type of id (group or dataset)
        # name if the fixed name, or empty string if no name
        # (name added for merge_subclass which results in more than one id with the
        # same name).
        av = {}
        for id in idsigs:
            sig = idsigs[id]
            sig_name = sig['name'] if sig['name'] else ''
#             if sig['name']:
#                 # fixed name, do not remove any attributes of this node
#                 continue
            type = sig['type']
            for key in sig['attrs']:
                kt = "%s-%s-%s" % (key, type, sig_name)
                value = sig['attrs'][key]['value']
                val_hash = hash(str(value))
                if kt not in av:
                    av[kt] = {val_hash: [id,]}
                elif val_hash not in av[kt]:
                    av[kt][val_hash] = [id, ]
                else:
                    av[kt][val_hash].append(id)
        # Now that have "av", remove attributes that have a value associated with multiple ids
        for kt in av:
            for val_hash in av[kt]:
                if len(av[kt][val_hash]) > 1:
                    # this key has same value in multiple id's.  Remove it
                    key = kt.split('-', 1)[0]
                    for id in av[kt][val_hash]:
                        del idsigs[id]['attrs'][key]
        # Part 2.  Remove any member nodes with fixed names
        # that are common to more than one id.  To find these, make mbs:
        # { "name-type": [id1, id2, ...], "name-type": [id3,], ... }
        mbs = {}
        for id in idsigs:
            sig = idsigs[id]
            if 'msigs' in sig:
                for msig in sig['msigs']:
                    if not msig['name']:
                        continue
                    # member has fixed name, i.e. not in <>
                    key = "%s-%s" % (msig['name'], msig['type'])
                    if key not in mbs:
                        mbs[key] = [id, ]
                    else:
                        mbs[key].append(id)
        # Now that have mbs structure, use it to remove members with the
        # same name and type that appear in multiple id's
        for kt in mbs:
            if len(mbs[kt]) > 1:
                # found member appearing in multiple ids
                name, type = kt.rsplit('-',1)
                for id in mbs[kt]:
                    sig = idsigs[id]
                    if 'msigs' in sig:
                        msigs = sig['msigs']
                        # update list of members to only include those with different name / type
                        # from: http://stackoverflow.com/questions/1207406/remove-items-from-a-list-while-iterating-in-python
                        msigs[:] = [m for m in msigs if m['name'] != name and m['type'] != type]
        # Part 3 (last part).  Remove attributes in members with no name if the values are
        # common to other attributes in members with no name with the same type.  For this, create av:
        #  { "key1-type" : { val_1: [id1-index, id2-index...], val_2: [id3-index, ] },
        #    "key2-type" { .... } }
        # key is attribute name, type is type of the member (group or dataset) and
        # "index" is the index of the msig entry (in msigs) that has that attribute
        av = {}
        for id in idsigs:
            sig = idsigs[id]
            if sig['name'] or 'msigs' not in sig:
                # fixed name or no members.  Do not remove any attributes of this nodes members
                continue
            i = -1  # index of member
            for msig in sig['msigs']:
                i = i + 1
                if msig['name']:
                    # member name is specified (not in <>).  Don't process
                    continue            
                ii = "%s-%s" % (id, i)  # id-index
                type = msig['type']
                # now check attributes in msig
                for key in msig['attrs']:
                    value = msig['attrs'][key]['value']
                    val_hash = hash(str(value))
                    kt = "%s-%s" % (key, type)
                    if kt not in av:
                        av[kt] = {val_hash: [ii,]}
                    elif val_hash not in av[kt]:
                        av[kt][val_hash] = [ii, ]
                    else:
                        av[kt][val_hash].append(ii)     
        # Now that av built, remove attributes that have a value associated with multiple members
        for kt in av:
            for val_hash in av[kt]:
                if len(av[kt][val_hash]) > 1:
                    # this key has same value in multiple msig's.  Remove it from those
                    for ii in av[kt][val_hash]:
                        id, i = ii.rsplit('-',1)
                        index = int(i)
                        key, type = kt.rsplit('-',1)
                        msig = idsigs[id]['msigs'][index]
                        del msig['attrs'][key]
 
#     def test_filter_sigs(self):
#         """ For testing filter_sigs method"""
#         print "Test 1: before filter, idsigs="
#         idsigs = {
#             '<i1>' : {'name': None, 'type': 'dataset', 'attrs': {'t': 'i1', 'count': 1}},
#             '<i2>' : {'name': None, 'type': 'dataset', 'attrs': {'t': 'i2', 'count': 1}},
#             '<i3>' : {'name': None, 'type': 'group', 'attrs': {'t': 'i1', 'count': 1}},
#             }
#         pp.pprint(idsigs)
#         self.filter_sigs(idsigs)
#         print "after filter, idsigs="
#         pp.pprint(idsigs)
#         print "count should be removed from <i1> and <i2> by not <i3>"
#         print "Test 2: before filter, idsigs="
#         idsigs = {
#             '<i1>' : {'name': None, 'type': 'group', 'attrs': {},
#                 'msigs': [
#                     {'name':'m1','type':'dataset', 'attrs':{}},
#                     {'name':'m2','type':'dataset', 'attrs':{}},
#                     ]},
#             '<i2>' : {'name': None, 'type': 'group', 'attrs': {},
#                 'msigs': [
#                     {'name':'m1','type':'dataset', 'attrs':{}},
#                     {'name':'m3','type':'dataset', 'attrs':{}},
#                     ]},
#             '<i3>' : {'name': None, 'type': 'group', 'attrs': {},
#                 'msigs': [
#                     {'name':'m1','type':'group', 'attrs':{}},
#                     {'name':'m2','type':'group', 'attrs':{}},
#                     ]},
#                 }
#         pp.pprint(idsigs)
#         self.filter_sigs(idsigs)
#         print "after filter, idsigs="
#         pp.pprint(idsigs)
#         print "m1 should be removed from <i1> and <i2>. <i3> should be unchanged."
#         print "Test 3: before filter, idsigs="
#         idsigs = {
#             '<i1>' : {'name': None, 'type': 'group', 'attrs': {},
#                 'msigs': [
#                     {'name':None,'type':'dataset', 'attrs':{'t': 'd1', 'count':1}},
#                     {'name':None,'type':'group', 'attrs':{'t':'g1', 'count':2}},
#                     ]},
#             '<i2>' : {'name': None, 'type': 'group', 'attrs': {},
#                 'msigs': [
#                     {'name':None,'type':'dataset', 'attrs':{'t':'d2', 'count':1}},
#                     {'name':None,'type':'group', 'attrs':{'t':'g2', 'count':3}},
#                     ]},
#             '<i3>' : {'name': None, 'type': 'group', 'attrs': {},
#                 'msigs': [
#                     {'name':None,'type':'group', 'attrs':{'t': 'd1', 'count':1}},
#                     {'name':'m2','type':'group', 'attrs':{'t': 'd1', 'count':1}},
#                     ]},
#                 }
#         pp.pprint(idsigs)
#         self.filter_sigs(idsigs)
#         print "after filter, idsigs="
#         pp.pprint(idsigs)
#         print "count should be removed from <i1> m1, and <i2>  <i3> should be unchanged."
 

       
    def mk_idsig(self, ns, id, df, node = None):
        """Make idsig for structure with id id in namespace ns and definition df.
        If id is from top-level structure, node == None.  If id is from
        an mstats in a group, then node is the group (h5gate.Group object) the
        id would be created in.
        """
        type = 'group' if id.endswith('/') else 'dataset'
        sig_name = self.get_sig_name(id)
        # make flag if name is fixed and unique.  Only reason might not be unique
        # is if there are subclass merges
        gsn = sig_name + "/" if sig_name and type == 'group' else sig_name
        name_unique = sig_name and ((node is None) or 
            not hasattr(node, 'subclass_merge_ids') or node.subclass_merge_ids[0] != gsn)
        is_link = 'link' in df
        if is_link:
            fixed_attrs = {}
            idsig = {'name': sig_name, 'type': type, 'attrs': fixed_attrs,
                'link': is_link, 'name_unique':name_unique}
            return idsig
        if type == 'dataset':
            fixed_attrs = self.get_sig_attrs(df)
            idsig = {'name': sig_name, 'type': type, 'attrs': fixed_attrs,
                'link':is_link, 'name_unique':name_unique}
            return idsig
        # type is group, need to get expanded def for attributes and also msigs
        # make sdef to use when calling get_expanded_def
        sdef = { 'type': type, 'id':id, 'ns':ns, 'df': df, }
        name = ""  # don't specify name.  Name only used if variable named id, and know actual replacement
        # path = full_path  # either None (if called for top level id, or full_path to node, if called for mstats)
        path = node.full_path if node else None
        expanded_def = self.get_expanded_def(sdef, name, path)
        # attrs = self.get_sig_attrs(df)   # probable bug, cause failure if no locations.  Fix below:
        attrs = self.get_sig_attrs(expanded_def)
        # Now have idsig for id, need to get idsigs for members
        v_id = re.match( r'^<[^>]+>/$', id) # True if variable_id (in < >)
        # path_id = id if not v_id else "__unknown__"
        # path = None if path is None else self.make_full_path(path, path_id)
        # don't use __unknown__ in path, instad make None if not known
        path = None if path is None or v_id else self.make_full_path(path, id)
        mstats = expanded_def['mstats']
        msigs = []
        for mid in mstats:
            mname = self.get_sig_name(mid)
            mdf = mstats[mid]['df']
            mtype = mstats[mid]['type']
            mlink = 'link' in mdf
            if mlink:
                # is a link
                mattrs = {}
            elif mtype == 'dataset':
                mattrs = self.get_sig_attrs(mdf)
            else:
                # is group
                mns = mstats[mid]['ns']
                msdef = { 'type': type, 'id':mid, 'ns':mns, 'df': mdf, }
                mex_def = self.get_expanded_def(msdef, name, path)  # leave name as blank
                mattrs = self.get_sig_attrs(mex_def)
            msig = {'name':mname, 'type':mtype, 'attrs': mattrs, 'link': mlink}
            msigs.append(msig)
        idsig = {'name': sig_name, 'type': type, 'attrs': attrs,
            'msigs': msigs, 'name_unique':name_unique}
        return idsig  

       
        
    def get_sig_name(self, id):
        """ idsig name is simply the id (without any trailing slash) if not a variable
        name, otherwise None"""
        id_noslash = id.rstrip('/')        # removing trailing slash in case it's a group
        if '-' in id_noslash:
            # dash in id signifies subclass
            # id is actually the part before it
            id_noslash = id_noslash.split('-')[0] 
        v_id = re.match( r'^<[^>]+>$', id_noslash) # True if variable_id (in < >)
        sig_name = None if v_id else id_noslash
        return sig_name
            
            
    def get_sig_attrs(self, df):
        """ Return dictionary of all attributes that have a value specified.  These
        are used in the matching of read hdf5 nodes to nodes defined in the structure.
        df is the structure definition."""
        sig_attrs = {}
        if 'attributes' in df:
            attrs = df['attributes']
            for key in attrs:
                avi = attrs[key]  # avi == attribute value info
                if 'value' in avi:
                    const = 'const' in avi and avi['const'] and avi['qty'] == '!'
                    # found an attribute with a specified value
                    sig_attrs[key] = {'value': avi['value'], 'const':const}
        return sig_attrs
        
    def make_ordered_name_spaces(self):
        """ Create list of name spaces with default namespace last, so when searching
        for structures that match a read hdf5 node, extensions (user defined name spaces)
        will take precedence"""
        self.name_spaces = self.ddef.keys()
        self.name_spaces.remove(self.default_ns)
        self.name_spaces.append(self.default_ns)
         
    def load_node_tree(self):
        """ Reads hdf5 file and figures out what nodes in file correspond to
        structures in specifications.  Stores nodes organized by structure in
        node_tree and id_lookups and dictionary from each path to node in path2nodes. """
        num_groups = self.links['count']['group']
        num_datasets = self.links['count']['dataset']
        if self.options['verbosity'] in ('all', ):
            print "Reading %i groups and %i datasets" % (num_groups, num_datasets)
        np = (self.file_pointer["/"], "/")  # np == 'node, path'
        groups_to_visit = [ np,]
        while groups_to_visit:
            np = groups_to_visit.pop(0)
            h5_group, path = np
            if 'spontaneous_stimulus/data' in h5_group.name:
            # if h5_group.name == '/stimulus/presentation/spontaneous_stimulus/data':
                import pdb; pdb.set_trace()
#             if h5_group.name == '/processing/brain_observatory_pipeline/MotionCorrection/2p_image_series/corrected':
#                 import pdb; pdb.set_trace()
            node = self.load_node(h5_group, path, 'group')
            if node.link_info:
                # this node was a link.  No further processing
                continue
            for mname in h5_group:
                mpath = self.make_full_path(path, mname)
                h5_node, ext_target = self.open_node_member(h5_group, mname)
                if not h5_node:
                    # unable to open the member
                    if ext_target:
                        # this is an external link that's not available.  Make a warning.
                        link_file, link_path = ext_target.split("\n")
                        msg = "%s: unable to open hdf5 external link, file='%s', path='%s'" % (
                            mpath, link_file, link_path)
                        self.warning.append(msg)
                    else:
                        msg = ("%s - unable to open node and not external link.  "
                            "Perhaps a dangling link?  Ignoring.") % mpath
                        self.error.append(msg)
                    # load node passing type "extlink" (deduce actual type i.e. group or dataset later)
                    self.load_node(h5_node, mpath, 'extlink')
                else:
                    # successfully loaded h5_node
                    if ext_target:
                        # found external link which exists
                        msg = ("%s: found external link.  Loading nodes from it, even though it's not "
                            "part of the original hdf5 file") % mpath
                        self.warning.append(msg)
                    if isinstance(h5_node, h5py.Dataset):
                        self.load_node(h5_node, mpath, 'dataset')
                    else:
                        np2 = (h5_node, mpath)
                        groups_to_visit.append(np2)
        # fill in any links that did not have target available when reading
        find_links.fill_missing_links(self)
        

    def open_node_member(self, h5group, mname):
        """ Attempts to open the member (group or dataset) with mname inside
        h5group.  Normally this should succeed.  But it may fail if the member
        is a hdf5 external link.  Return tuple: (member, ext_target).
        member is the opened node (if opened successfully) otherwise None.
        ext_target is the target for the external link (if this member is
        an hdf5 external link.  Otherwise None.
        """
        # first, get external link target if any
        path = self.make_full_path(h5group.name, mname)
        if path in self.links['path2lg']['ext']:
            ext_target = self.links['path2lg']['ext'][path]
        else:
            ext_target = None
        # now try to open member
        try:
            member = h5group[mname]
        except KeyError:
            if not ext_target:
                # unable to open and not an external link.  Not sure what's wrong
                msg = "%s: unable to read node.  Perhaps a dangling link?" % path
                self.warning.append(msg)
            member = None
        return (member, ext_target)
        
    
    def load_node(self, h5_node, full_path, type):
        """ save node corresponding to h5_node in node_tree, id_lookups
        and path2nodes.  type is 'group', 'dataset' or 'extlink'.  'extlink'
        indicates that node is an external link that is not available and actual
        type (group or dataset) is not known.  In that case, h5_node should be None."""
        # for debugging, h5_node.name == '...' cannot be used because it fails with external links
        # if full_path == '/stimulus/presentation/spontaneous_stimulus/data':
        #     import pdb; pdb.set_trace()
        assert (h5_node is None) == (type == 'extlink'), "h5_node and type don't match in load_node"
        parent_path, node_mname  = full_path.rsplit('/',1)
        if node_mname  == '':
            node_mname  = '/'  # at root node
            parent = None
        else:
            if parent_path == '':
                parent_path = '/' # at node just under root
            parent = self.path2node[parent_path]
#         if full_path == "/stimulus/presentation/rec_stim_1/data":
#             print "in load_node, found %s" % full_path
#             import pdb; pdb.set_trace()
        sdef = self.deduce_sdef(h5_node, full_path, type, parent)
        if type == 'extlink':
            # type was unknown because node was extlink.  Get type now from sdef
            type = sdef['type']
        # Uncomment the following to see found definitions while loading each node
        # print "Loading node: %s:" % h5_node.name
        # pp.pprint(sdef)
        v_id = re.match( r'^<[^>]+>/?$', sdef['id']) # True if variable_id (in < >)
        name = node_mname  if v_id else ''
        attrs = self.get_changed_attributes(h5_node, sdef, parent_path, node_mname ) if h5_node else {}
        # Get link information if this node is a link
        link_info = find_links.deduce_link_info(self, full_path, type, sdef)
        # finally, create the nodes so they are saved in the node tree
        if type == 'group':
            node = Group(self, sdef, name, parent_path, attrs, parent, link_info)
        else:
            value = self.make_value_info(h5_node) if h5_node else None
            dtype = None
            compress = False
            node = Dataset(self, sdef, name, parent_path, attrs, parent, value, dtype, compress, link_info)
        # Save hdf5 node attributes for later validation (checking for missing attributes)
        # only save if h5_node is not None.  It will be None if there is an external link
        if h5_node:
            for key in h5_node.attrs:
                value = h5_node.attrs[key]
                node.h5attrs[key] = value
        return node

    def save_counts(self, dict, key):
        """ save key and counts of key"""
        if key in dict:
            dict[key] += 1
        else:
            dict[key] = 1
  
    def make_value_info(self, h5_dataset):
        """ Make string describing type and shape of h5_dataset, so do not need to
        load in entire data array.  If shape is scalar, just return the value.
        Otherwise, return string describing value; looks like:
           value_info: type="float64", shape="[5]"     (1-d)
           value_info: type="int32", shape="[4 3]"   (2-dimensional)
        """
        shape = h5_dataset.shape
        if len(shape) == 0:
            # shape = 'scalar'
            # just use value of dataset
            value = h5_dataset.value
            return value
        # dtype = h5_dataset.dtype.type.__name__
        dtype = h5_dataset.dtype
        dt_name = dtype.type.__name__
        if dt_name == 'object_':
            # check for variable length string base type
            # this from: http://docs.h5py.org/en/latest/special.html
            base_type = h5py.check_dtype(vlen=dtype)
            matchObj = re.match(r"<(type|class) '([^']+)'>", str(base_type))
            if not matchObj:
                raise SystemError("** Error: Unable to find object base type in %s" % base_type)
            dt_name = matchObj.group(2)
            if dt_name == "str":
                dt_name = "text"
        elif dt_name == "string_": 
        # if dtype in ('object_', 'string_'):
        # if dtype in ('string_',):  # need to add unicode
            dt_name = 'text'
        pshape = re.sub('[,]', '', str(shape))[1:-1]  # slice removes ( )
        vi = 'value_info: type="%s", shape="[%s]"' % (dt_name, pshape)
        return vi
         
    def deduce_sdef(self, h5node, full_path, type, parent):
        """ Deduce the sdef (structure definition information) from the h5py node
        h5_node when reading a file.  
        * h5node is None if the node is an external link with a dangling target.  In that case
        type is 'extlink'.  
        * type is either 'group', 'dataset', or 'extlink'.
        * full_path is the path to the node using the parent group member name.  It is used
        to make node_mname, which is the name of the member in the parent hdf5 group that
        corresponds to this node.  It usually will match the last component of h5node.name,
        except if this node is an external link.  For example, if the
        parent group has a member named "data", and it is an external link to a node in an
        external file named "image_stack", node_mname  will be "data" but last component
        of h5node.name will be "image_stack".
        * parent is the parent h5gate group in the node_tree.
        The parent should always exist when this is called.  Fields in parent are:
            sdef - structure definition for parent.  See returned for fields.
            name - name of node if name not specified in sdef['id'] (because it's variable name)
            path  - path to parent of parent
            full_path  - path to parent
            mstats - dictionary mapping id of each member to information about the member
               self.parent.mstats[id] = { 'df': {}, 'type':type, 'ns': ns,
                    'created': [ self, ], 'qty':'?' }
            msigs - dictionary mapping id of each id in mstats that has a definition to
                the "idsig" for nodes of that type.  present if added (by a call from
                this function) in order to identify node
            parent - parent node of parent, or None if h5node is root
            Others ; (attrs, attributes) - not used here.
        Returned structure has keys:
            id - id in structures, (if is a top-level structure, or a member
                of a structure in a group).  Otherwise is the name of the hdf5 node
                with a trailing '/' if a group, otherwise no trailing '/'.
            qid - qualified id.  Can contain namespace:id.  Set to None here.
            ns - namespace associated with sdef (if found in structures).  Otherwise None.
            df - definition of structure (if found in structures top level or in member).
            location - set "True" if this is a group that is in a path in locations
                and if it does not match any structures.  Otherwise not present.
            top - set true if this node is in the top of the defined structures,
                not present otherwise."""
        parent_path, node_mname  = full_path.rsplit('/',1)
        if node_mname  == '':
            node_mname  = '/'  # at root node
        # import pdb; pdb.set_trace()
        assert (h5node is None) == (type == "extlink"), "h5node and extlink do not match in deduce_sdef"
        h5nsig = self.make_h5nsig(h5node, node_mname) if h5node else self.make_minimal_msig(node_mname)
        # if h5node and h5node.name == "/processing/brain_observatory_pipeline/MotionCorrection/2p_image_series/corrected":
        #     import pdb; pdb.set_trace()
        if not parent:
            # is root node.  See if there is a definition for root in structures
            match = self.find_matching_id_in_structures(h5nsig)
            if match:
                # creating top level structure by itself (not in another structure)
                id, ns = match
                sdef = self.get_sdef(id, ns, "referenced in deduce_sdef")
                return sdef
            # default sdef for root node
            sdef =  {'type': 'group', 'id':'/', 'qid':None, 'ns':None, 'df':{} }
            return sdef
        elif parent.sdef['df']:
            # This node is inside a structure.  Try to match node to one
            # of structures defined in mstats
            if not hasattr(parent, 'msigs'):
                # msigs dictionary not in parent.  Create it
                self.add_msigs(parent)
            id = self.find_matching_id(h5nsig, parent.msigs, 1)
            if id:
                # found match to id in parent definition.  Use this.  Following from get_sgd
                if type == "extlink":
                    # if extlink, don't know type, get it from parent definition in mstats
                    type = parent.mstats[id]['type']
                sgd = {'id': id, 'type': type, 'ns':parent.mstats[id]['ns'], 'df': parent.mstats[id]['df']}
                return sgd
            # Didn't find match to id in parent definition.            
            # see if creating a top-level structure (should not normally be done
            # inside a group, but if it is, it's good to detect it).
            # following derived from function get_custom_node_info
            match = self.find_matching_id_in_structures(h5nsig)
            if match:
                # creating top level structure inside another group structure
                id, ns = match
                sdef = self.get_sdef(id, ns, "referenced in deduce_sdef")
                sdef['custom'] = True   # flag custom node
                return sdef
            # did not match top level structure
            # must be a custom node in group
            gslash = '/' if type == 'group' else ''
            id = h5nsig['name']
            ns = parent.sdef['ns']
            sdef = { 'type': type, 'qid': None, 'id':id + gslash, 'ns':ns, 'df': {}, 'custom': True }
            if not ('custom' in parent.sdef and parent.sdef['custom']):
                # parent was not custom, but this is.  Save h5nsig in sdef for displaying
                # of information about why this is detected as custom
                sdef['h5nsig'] = h5nsig
            return sdef
        else:
            # This node is not inside a structure
            # Must be custom.  See if is top-level structure
            match = self.find_matching_id_in_structures(h5nsig)
            if match:
                # creating top level structure by itself (not in another structure)
                id, ns = match
                sdef = self.get_sdef(id, ns, "referenced in deduce_sdef")
                sdef['custom'] = True   # flag custom node
                sdef['top'] = True  # flag at the top level (same as in function 'get_custom_node_info')
                return sdef
            # Finally, must be a custom node.  Flag also at top level (not in structure).
            id = h5nsig['name']
            gslash = '/' if type == 'group' else ''
            sdef = { 'type': type, 'qid': None, 'id':id + gslash, 'ns':None, 'df': {}, 
                'custom': True, 'top': True }
            return sdef
            
    def add_msigs(self, node):
        """ Create 'msigs' entry in node (h5gate group object).  The msigs entry maps
        each id in mstats of node that has a definition to the signature for that id.
        It is used for searching for the ids that match an hdf5 node inside a group."""
        msigs = {}
#         if  node.full_path == u'/epochs/Trial_003':
#             import pdb; pdb.set_trace()
        # ns = node.sdef['ns']
        for id in node.mstats:
            info = node.mstats[id]
            if 'df' in info:
#                 if id == '<MyNewTimeSeries>/':
#                     import pdb; pdb.set_trace()
                ns = info['ns']
                # msigs[id] = self.mk_idsig(ns, id, info['df'], node.full_path)
                msigs[id] = self.mk_idsig(ns, id, info['df'], node)
            else:
                print "Did not find definition (df) in mstats entry: %s" % info
                # import pdb; pdb.set_trace()
                error_exit()
        self.filter_sigs(msigs)
        node.msigs = msigs
        
    def find_matching_id_in_structures(self, h5nsig):
        """ Find structure in any namespace matching h5nsig.  If found, return
        id, ns (id and namespace).  h5nsig is a signature of an h5node, created by
        make_h5nsig."""
        for ns in self.name_spaces:
            id = self.find_matching_id(h5nsig, self.idsigs[ns], 2)
            if id:
                return (id, ns)
                
                
    def find_matching_id(self, h5nsig, idsigs, level):
        """ Find node matching node signature.  Inputs are:
        h5nsig - signature of h5node
        idsigs - dictionary of signatures that the node may match. Build from definitions
        level - number of matches required to be a match.  A higher number is used
            to force more stringent matching (reduce false positives).
            So far, level == 1 or 2.  One if matching to a limited set of ids,
            (in a location or a group).  2 if matching to all top-level structures.
        Returns id of matching signature or None"""
        matches = []
        for id in idsigs:
            match_count = self.match_sigs(h5nsig, idsigs[id])
            if match_count == -1:
                # definitely not a match
                continue
            if match_count < level and 'msigs' in idsigs[id] and 'msigs' in h5nsig:
                # did not find required number matches yet.  Check members
                # hopefully there will not be many members.  A more efficient way
                # of doing this should be developed.
                for msig1 in h5nsig['msigs']:
                    for msig2 in idsigs[id]['msigs']:
                        if self.match_sigs(msig1, msig2) > 0:  
                            # count any match with member as one match, even if is 2
                            # There might be other methods, such as find num of maximal matches
                            # it's not clear those would be any better
                            match_count = match_count + 1
                            break
                    if match_count >= level:
                        # found all matches we need.  Terminate outer loop
                        break
            # if only one to match, and in group (i.e. level==1) be very forgiving
            if match_count >= level or (len(idsigs) == 1 and level==1):
                matches.append(id)
        if len(matches) > 1:
            print "Found more than one match to node. (%s)" % matches
            print "Perhaps specification is ambigious."
            import pdb; pdb.set_trace()
            error_exit()
        if len(matches) == 1:
            return matches[0]
        # did not find match
        return None
        
        
    def make_path_parts(self,path):
        """ Split path into components, including '/' as first part.  path
        is assumed to be an absolute path"""
        assert path[0]=='/', "Must be an absolute path"
        if path == '/':
            path_parts = ['/',]
        else:
            path_parts = path.split('/')
            assert path_parts[0] == '', "after split, first char is not empty"
            path_parts[0] = '/'
        return path_parts
                         
    
    def match_sigs(self, h5nsig, idsig):
        """ Determine match between signature for h5 node (h5nsig) and
        signature made from definitions (idsig).  Return either:
         -1 Definitely not a match.  Either types or fixed names do not match).
          0 Types match only (for non-named nodes)
          1 Either name or an attribute match
          2 Both name and an attribute match
        h5nsig['type'] will be None for external_link, otherwise 'group' or 'dataset'
        """  
        # check for definitely not a match
        if (h5nsig['type'] and idsig['type'] != h5nsig['type']) or (idsig['name'] and 
            idsig['name'] != h5nsig['name']):
            return -1
        match_count = 0
        if idsig['name'] and idsig['name'] == h5nsig['name']:
            # name is specified for idsig and matches name in h5 node
            # see if name is unique in idsig
            if 'name_unique' in idsig and idsig['name_unique']:
               # name matches and is unique, this must be a match
               return 5
            match_count = 1
        # Try to find an attribute that matches and check for const attributes that don't match
        # note that h5nsig attributes are like: {key1: value1, ... }
        # but idsig attributes are like: {key1: {'value: value1, 'const': True}}
        # ('const' may or may not be present)
        found_matching_attribute = 0
        for key in idsig['attrs']:
            const = 'const' in idsig['attrs'][key] and idsig['attrs'][key]['const']
            if key in h5nsig['attrs']:
                vals_match = find_links.values_match(idsig['attrs'][key]['value'],
                    h5nsig['attrs'][key])
                if vals_match:
                    found_matching_attribute = 1
                    continue
            if const and h5nsig['type']:
                # h5node exists (not external link) and either does not have the
                # const value, or the constant values don't match, so definitely not a match
                return -1
        match_count += found_matching_attribute
        return match_count  
              
            
    def make_h5nsig(self, h5node, node_mname):
        """ Make "signature" of h5node.  This used to search for match between
        h5node and nodes defined by structures in specification language. h5node is the
        hdf5 object, or None if not loaded (because it's a dangling external link).
          node_mname is the name of the node object in the
        members list of the parent group.  This may be different than the name 
        as given by the last component of the h5node.name if the node is a link.
        The signature
        has the following format:
          { name: name of node (not including path)
            type: 'group' or 'dataset'
            attrs: { 'key1': 'val1', ... }  -- for all attributes
            msigs: [ <memSig1>, <memSig2>, ... ] } -- Signature of each member if id is a group
        where <memSig> has the format:
          { name: <>  -- name of member
            type: 'group' or 'dataset'
            attrs: { 'key1': 'val1', ... } }  -- for all attributes in member """
        sig = self.make_h5nsig2(h5node, node_mname)
        if sig['type'] == 'group':
            msigs = []
            for mname in h5node:
                member, ext_target = self.open_node_member(h5node, mname)
                if not member:
                    # unable to open the member.  Perhaps due to it being an external link
                    # make a sig with just the name
                    msig = self.make_minimal_msig(mname)
                else:
                    msig = self.make_h5nsig2(h5node[mname], mname)
                msigs.append(msig)
            sig['msigs'] = msigs
        return sig
        
    def make_h5nsig2(self,h5node, node_mname):
        """Gets name, type and attributes from a h5node.  node_mname is the name
        of the node as given in the parent group"""
        # name = h5node.name.rsplit('/',1)[-1]
        name = node_mname
        if name == '':
            name = '/'
        type = 'dataset' if isinstance(h5node, h5py.Dataset) else 'group'
        attrs = self.fetch_attributes(h5node)
        return {'name': name, 'type': type, 'attrs':attrs}
       
       
    def make_minimal_msig(self, mname):
        """ Return msig with just the name.  This used when have hdf5 extlink because
        only the name is known.  Not the type or any attributes or members."""
        msig = {'name': mname, 'type': None, 'attrs':{}}
        return msig
        
                            
    def get_changed_attributes(self, h5_node, sdef, parent_path, node_name):
        """return dictionary of attributes that are set in h5_node and different
        from any default value specified in definition"""
        is_link = 'link' in sdef['df']
        if is_link:
            # if this node is defined as a link, don't return any changed attributes
            return {}
        if sdef['type'] == 'group':
            # only get expanded def for groups, not datasets
            edf = self.get_expanded_def(sdef, node_name, parent_path)
        else:
            edf = sdef['df']
        fixed_attrs = self.get_sig_attrs(edf)
        changed_attrs = {}
        for key in h5_node.attrs:
            value = h5_node.attrs[key]
            if (key not in fixed_attrs or not find_links.values_match(fixed_attrs[key], value)):
                changed_attrs[key] = value
        return changed_attrs
        
    def fetch_attributes(self, h5_node):
        """ Get attributes for hdf5 node as a dictionary"""
        attrs = {}
        for key in h5_node.attrs:
            value = h5_node.attrs[key]
            attrs[key] = value
        return attrs
        
            
    def get_dtype_and_shape(self, val):
        """ Return data type and shape of value val, as a tuple.  This
        called from Dataset object (when writing and reading a file)
        and also from File object when reading a file."""
        # get type of object as string
        val_type = str(type(val))
        matchObj = re.match(r"<(type|class) '([^']+)'>", val_type)
        if not matchObj:
            raise SystemError("** Error: Unable to find type in %s" % val_type)
        val_type = matchObj.group(2)
        # check for "value_info" passed in through calling script (e.g. Matlab)
        # if so, then type and shape is given in val (it does not contain the actual data
        # to store.  Also, shape can be passed as string when reading a file.
        if val_type == 'str' and (self.options['storage_method'] == 'commands' or
            self.reading_file):
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
        # TODO: make more general.
        if val_type in ('str', 'int', 'float', 'long', 'unicode', 'bool', 'int64'):
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
            if len(shape) == 0:
                shape = "scalar"
            dtype = str(val.dtype)
            if re.match(r'^\|V\d+$', dtype):
                # if found dtype like "|V537350" it's type "opaque".  This corresponds to binary
                # this put in for validating files that have binary data because this routine
                # called when reading the file (to simulate calls to write it)  Should probably change
                # so that the checks here are not called when reading a file since they will be done
                # at the end by function validate_file
                dtype = "binary"
            # print "found numpy or h5py dataset, dtype is %s", dtype

#         if isinstance(val, np.generic):
#             # obtain shape and type directly
#             shape = val.shape
#             if len(shape) == 0:
#                 shape = "scalar"
#             dtype = val.dtype.name  # will be like "int32".
#             return (dtype, shape)
            
        else:
            print "** Error, unable to determine shape of value assiged to dataset"
            print "value type is '%s'" % val_type
            error_exit()
        return (dtype, shape)
        
    # Following functions used with includes in class Group, but written as member 
    # of File object (rather than methods of class Group) so can call them from
    # doc_tools to process includes

    def save_include(self, includes, mid, id, ns, qty, source, loc, modifiers = None,
        base=None, source_id=None):
        """ Save information about an id being included.
        includes - dictionary used to store the include
        mid - member id to be stored in mstats (will be local id of item within group)
        id - full id used to lookup definition in structures
        ns - namespace for item
        qty - quantity flag, '!', '*', '?', '^', '+'
        source - source of item.  One of:
            - explicit (mid explicitly specified in include)
            - implicit (include added because id has absolute path matches path for this node
            - subclass (mid added because it's a subclass of include specified with
                'subclasses': True)
        loc - string specifying location, displayed if error message
        modifiers - if present, is a dictionary that should be merged into the included
            definition.  This allows modifying the definition (subclassing) the item included.
        base - base class of member if source is 'subclass'.  e.g. in the specification:
            "include": {"<TimeSeries>/*":{"_options": {"subclasses": True}} },
            base will be "<TimeSeries>/" and (mid will be a subclass of <TimeSeries>/).
        source_id - ns:id of structure specifying this include.  Currently not used.
        """
        if mid in includes:
            # this was already included.  Don't include it again, don't flag an error, just ignore it
            # print "Found id '%s' in includes.  ns='%s', source=%s, loc=%s, includes=" % (
            #    mid, ns, source, loc)
            # print "ignoring this for now."
            return
#         assert mid not in includes, "%s: attempting to add include %s more than once" %(
#             loc, mid)
        assert id in self.ddef[ns]['structures'], ("%s: attempting to add include %s:%s "
            "but definition not found") % (loc, ns, id)
        assert source in ('explicit','implicit','subclass'), ("Invalid source (%s) in "
            "save_include" % source)
        assert qty in ('!', '*', '?', '^', '+'), "invalid qty '%s' in save_include" % qty
        includes[mid] = {'id':id, 'ns':ns, 'qty':qty, 'source':source, 
            'modifiers':modifiers, 'base':base, 'source_id': source_id}
    
    def save_includes(self, ns, includes, include_spec, loc):
        """ Process includes specified in format specification.  Expand each and
        save it in dict includes"""
        for qid in include_spec:
            # qid, qty = self.parse_qty(qidq, "*")
            ins, mid = self.parse_qid(qid, ns)
            extra = include_spec[qid]
            qty = extra.pop('_qty') if '_qty' in extra else '*'
            # remove '_source' from includes extra.  This currently not used.
            source_id = extra.pop('_source') if '_source' in extra else None
            if ("_options" in extra and "subclasses" in extra["_options"]
                and extra["_options"]["subclasses"]):
                # if subclasses, don't save any modifiers (other contents of extra)
                self.save_subclass_includes(includes, mid, ins, qty, loc)
            else:
                # this include is not specifying subclasses
                id = mid  # since id is not a path, the id is same as the member id
                source = 'explicit'
                self.save_include(includes, mid, id, ins, qty, source, loc, extra, 
                    source_id=source_id)
    

    def save_subclass_includes(self, includes, mid, ns, qty, loc):
        """ Add list of subclasses of mid to self.includes
        """
        qmid = "%s:%s" % (ns, mid)
        # if no subclasses, just use class by itself as list of subclasses
        subclasses = self.subclasses[qmid] if qmid in self.subclasses else [qmid,]
        for sid in subclasses:
            sns, smid = self.parse_qid(sid, ns)
            self.save_include(includes, smid, smid, sns, qty, 'subclass', loc, base=mid)
            

    # following moved from member of group to member of file so can call from doc_tools

    def merge_attribute_defs(self, dest, source):
        """ Merge attribute definitions.  This used for merges,
        and includes where attributes are specified.  It converts sources specified
        as a string using key '_source' to an array with key 'source' and values the
        ancestors of the sources.  This used if there is a superclass overriding
        attributes in a subclass.  It may also be used for extensions.
        The order in the array is that the latest in the list is
        the most recent source, earlier in list are from structures that are extended
        (e.g. base classes).
        """
        for aid in source.keys():
            if aid not in dest.keys():
                dest[aid] = copy.deepcopy(source[aid])
                if 'qty' not in dest[aid]:
                    # if present, rename key from '_qty' to 'qty' to be consistent with mstats key
                    dest[aid]['qty'] = dest[aid].pop('_qty') if '_qty' in dest[aid] else "!"  # default is required
                if '_source' in dest[aid]:
                    # rename key from '_source' to 'source' to be consistent with mstats key
                    assert 'source' not in dest[aid], "attribute '%s', has 'source' in def: %s" % (
                       aid, dest[aid])
                    a_source = dest[aid].pop('_source')
                    dest[aid]['source'] = [a_source]
                continue
            # attribute already is in dest, append any specified '_source' to 'source' list
            a_source = source[aid]['_source'] if '_source' in source[aid] else None
            # replace qty specified in superclass with qty for subclass
            source_qty = (source[aid]['qty'] if 'qty' in source[aid] else
                source[aid]['_qty'] if '_qty' in source[aid] else "!")  # default is required
            dest[aid]['qty'] = source_qty
            if a_source:
                if 'source' in dest[aid]:
                    dest[aid]['source'].append(a_source)
                else:
                    dest[aid]['source'] = [a_source]
                # also, replace any description by the superclass description, or if there
                # is no superclass description, remove description from the definition.
                # This done so any value specified will be be displayed in generated
                # documentation rather than the description of the subclass
                if 'description' in source[aid]:
                    dest[aid]['description'] = source[aid]['description']
                else:
                    if 'description' in dest[aid]:
                        dest[aid].pop('description')               
            if 'value' not in dest[aid]:
                if 'value' in source[aid]:
                    val = source[aid]['value']
                    # this used for appending, no longer done
                    # if type(val) is str and val[0] == '+':
                    #    val = val.lstrip('+')
                    if 'dimensions' in dest[aid]:
                        # todo: check if this is used.  Might be only for old-style append
                        # destination is an array.  This is the first element
                        dest[aid]['value'] = [val,]
                    else:
                        # just regular assignment
                        dest[aid]['value'] = val
                    # TODO: check if data type specified in destination matches value       
                else:
                    print ("** Error, merging attribute '%s' but value not specified in source"
                        " or destination") % aid
#                     import pdb; pdb.set_trace()
                    error_exit()
            else:
                if 'value' in source[aid]:                       
                    # value given in both source and destination
                    self.append_or_replace(dest[aid], source[aid], 'value', "attribute %s" % aid)
                else:
                    # value specified in dest but not source.  Just leave value in dest
                    pass
            # copy const if present
            if 'const' in source[aid]:
                dest[aid]['const'] = source[aid]['const']
            
                     
#   


    def append_or_replace(self, dest, source, key, ident):
        """ dest and source are both dictionaries with common key 'key'.  If both
        values of key are type str, and source[key] starts with "+", append the value
        to dest[key], otherwise replace dest[key].  This is to implement appends
        or replacing in 'include' directives.  ident is descriptive identifier
        used for warning or error message. """
        prev_val = dest[key] 
        new_val = source[key]
        # check for appending new_value to previous value
        if (type(new_val) is str and new_val[0] == '+'):
            # need to append string to prev_val
            new_val = new_val.lstrip('+')
            # Either append to array or to comma separated string
            if type(prev_val) is str:
                # appending to string
                if prev_val != '':
                    dest[key] = prev_val + "," + new_val
                else:
                    dest[key] = new_val
            elif isinstance(prev_val, list):
                # appending to list
                dest[key] = dest[key] + [new_val]
            else:
                msg = "Attempting to append '%s' to type '%s'.  Must by list or string" % (
                    new_val, type(prev_val))
                error_exit(msg)
            return
        # Not appending.
#         if (type(prev_val) is str and type(new_val) is str and new_val[0] == '+'):
#             # need to append to string
#             new_val = new_val.lstrip('+')
#             if prev_val != '':
#                 dest[key] = prev_val + "," + new_val
#                 return
        # replace previous value by new value
        # first do some validation
        if type(prev_val) != type(new_val):
            print ("** Error, type mismatch when setting %s, previous_type=%s,"
                " new type=%s; previous value=") %(ident, type(prev_val), type(new_val))
            pp.pprint(prev_val)
            print "New value="
            pp.pprint(new_val)
            error_exit()
# Disable type checking for testing ancestry attribute as array
#         if not(type(new_val) is str or type(new_val) is int or type(new_val) is float
#             or type(new_val) is long):
#             print "** Error, invalid type (%s) assignd to %s" % (type(new_val), ident)
#             print "Should be string, int or float.  Value is:"
#             pp.pprint(new_val)
#             traceback.print_stack()
#             sys.exit(1)
        # TODO: check for data_type matching value type
        dest[key] = new_val
 
    def merge_def(self, expanded_def, sdef, to_include, id_sources, loc, descriptions=[]):
        """ Merge structure defined by sdef into expanded_def.
        Also sets to_include to set of structures to include. loc is a location
        string (or id) displayed in an error message if there is an error.
        expanded_def is the destination for the merge.
        sdef is the structure definition to merge into expanded_def.
        to_include is a list set to id's referenced in a include statement in sdef['df'].            
            id_sources is set to a dictionary mapping each id (stored as key in mstats)
        to a list of sources for that key (series of subclasses or extensions
        overwriting the previous versions).  Each element of the list is a
        'qualified sdef id' (qsid).  Value is: (ns:id) ns == sdef['ns'],
        id == sdef['id']).  Last element gives the final source which includes
        the namespace associated with the id for displaying in documentation.
        Also allows displaying when this was formed by overriding a previous value.
        """
        # setup 'qsid' (qualified sdef id) to store in description
        qsid = "%s:%s" % (sdef['ns'], sdef['id'])
        for id in sdef['df'].keys():
            if (((id == 'description' and type(sdef['df'][id]) is str)
                and '_description' not in sdef['df'].keys()) or id == '_description'):
                # add this description to list of descriptions
                descriptions.append((qsid, sdef['df'][id]))
                # append this description to any other descriptions specified by previous merge
                # description = "%s:%s- %s" % (sdef['ns'], sdef['id'], sdef['df'][id])
                # self.description.append(description)
                continue
            if id in ('merge', '_qty', '_source', '_source_id'):
                continue
            if id == 'attributes':
                if 'attributes' not in expanded_def:
                    expanded_def[id] = {}
                self.merge_attribute_defs(expanded_def[id], sdef['df'][id])
                continue
            if id == 'include':
                # save includes for processing later
                include_spec = copy.deepcopy(sdef['df'][id])  # make copy since will be changed
                # Caution: do not confused self.sdef with sdef (being merged in).
                self.save_includes(sdef['ns'], to_include, include_spec, loc)
                continue
            if id in expanded_def.keys():
                # if value for both are dictionaries, try recursive merge
                if isinstance(expanded_def[id], dict) and isinstance(sdef['df'][id], dict):
                    # print "conflicting key (%s) in merge" % id
                    # print "attempting to recursively merge expanded_def['%s]:" % id
                    # pp.pprint(expanded_def[id])
                    # print "with sdef['df']['%s']:" % id
                    # pp.pprint(sdef['df'][id])
                    self.merge(expanded_def[id], sdef['df'][id])
                else:
#                     if (id in ("_description", "description") and
#                          isinstance(expanded_def[id], str) and isinstance(sdef['df'][id], str)):
#                          # replace earlier definition with latest one
#                          expanded_def[id] = sdef['df'][id]
#                          continue
                    print "** Error"
                    print "Conflicting key (%s) when merging '%s'" % (id, sdef['id'])
                    # print "make_group(%s, %s, path=%s)" % (self.sdef['id'], self.name, self.path)
                    print "expanded_def is:"
                    pp.pprint(expanded_def)
                    print "sdef is:"
                    pp.pprint(sdef)
                    # import pdb; pdb.set_trace()
                    error_exit()
            else:
                # no conflict, just copy (or merge) definition for id
                # deep copy so future merges do not change original
                df_copy = copy.deepcopy(sdef['df'][id])
                if isinstance(sdef['df'][id], dict):
                    # merge so convert source for id_attributes from '_source' (str) to 'source' (array)
                    expanded_def[id] = {}
                    self.merge(expanded_def[id], df_copy)
                else:
                    expanded_def[id] = df_copy
                # df_copy = copy.deepcopy(sdef['df'][id])
#                 if isinstance(df_copy, dict):
#                     # use merge function to merge so any attributes will include source
#                     expanded_def[id] = {}
#                     self.merge(expanded_def[id], df_copy, qsid)
#                 else:
#                     expanded_def[id] = df_copy
            # OLD: save namespace associated with this id
            # ns_sources[id] = sdef['ns']
            # NEW: append qid of this source to id_sources
            if "_source" in expanded_def[id]:
                source = expanded_def[id].pop("_source")
                if id in id_sources:
                    id_sources[id].append(source)
                else:
                    id_sources[id] = [source]
#             print "set id_sources['%s'] to: %s" %(id, qsid)
            

    def merge(self, a, b, path=None):
        """merges b into a
        from: http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
        """
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    if key == 'attributes':
                        # self.merge_attribute_defs(b, a)
                        self.merge_attribute_defs(a[key], b[key])
                    else:
                        self.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
                    self.append_or_replace(a,b,key, '/'.join(path + [str(key)]));
            else:
                if key == 'attributes' and isinstance(b[key], dict):
                    # if attributes, always call merge attribute defs to setup source key to
                    # be array.  This might be appended to later if subclassing
                    a[key] = {}
                    self.merge_attribute_defs(a[key], b[key])
                else:
                    a[key] = b[key]
        return a


    def find_overlapping_structures(self, sdef, full_path):
        """ Find structures (group definitions) that should be merged into the definition
        of group with structure definition sdef; full_path
        is the path to the group, or None if the group is an Id that does not
        have a path.
        This merging implements extensions.  Structures are located using
        three methods: 1. having the same identifier (id), e.g. "<electricalSeries>/" and be
        located in a different namespace (ns), 2. having an identifier that is is equal
        to the absolute location (full path) of this node, or 3. If the id for this node is
        a variable id (i.e. in <angle brackets>/) and the id of a structure is the same as
        the parent full path appended to the id if this node.  i.e.:
        "/stimulus/presentation/<VoltageClampStimulusSeries>/
         """
        to_merge = []
        tns = sdef['ns']  # this namespace (namespace for this group)
#         if self.full_path=='/general':
#             import pdb; pdb.set_trace()
        id = sdef['id']
        source_id = sdef['df']['_source_id'] if '_source_id' in sdef['df'] else id
        if full_path is not None:
            if full_path[0] != '/':
                full_path = "/" + full_path
            full_path_g = full_path if full_path.endswith('/') else full_path + "/"
        for ns in self.ddef:
            structures = self.ddef[ns]['structures']
            if id in structures and ns != tns:
                # import pdb; pdb.set_trace()
                # found to merge using criteria 1
                qid = "%s:%s" % (ns, id)
                to_merge.append(qid)
            if full_path is None:
                # full path is unknown.  Don't check for absolute paths to merge
                continue
            if full_path_g in structures and (ns != tns or full_path_g != source_id):  # don't merge in self
                # found to merge using criteria 2
                qid = "%s:%s" % (ns, full_path_g)
                to_merge.append(qid)
            v_id = re.match( r'^<[^>]+>/$', id) # True if variable_id (in < >)
            if v_id:
                parent_path, name = self.get_name_from_full_path(full_path)
                full_path_vid = self.make_full_path(parent_path, id)
                if full_path_vid in structures:
                # found to merge using criteria 3
                    qid = "%s:%s" % (ns, full_path_vid)
                    to_merge.append(qid)
#         if to_merge:
#             print "find_overlapping_structures, tns=%s, id=%s, full_path=%s; returning %s" % (tns,
#                 id, full_path, to_merge)
#         if 'core:acquisition/' in to_merge:
#             import pdb; pdb.set_trace()
        return to_merge
 
    def find_all_merge(self, initial_to_merge, initial_ns):
        """ Builds list of all structures to be merged.
            Includes merges containing a merge.  initial_ns is the namespace initially
            assumed (if no other name space specified).  """
        to_check = copy.copy(initial_to_merge)
        checked = []
#         if self.full_path == "/stimulus/presentation/Sweep_45":
#             import pdb; pdb.set_trace()
        # order is import.  id's to be merged last are first in to_merged
        # they will be first in checked.  When processing return values, process them in reverse order
        while len(to_check) > 0:
            qid = to_check.pop(0)
            if qid in checked:
                continue
            sdef = self.get_sdef(qid, initial_ns, "Referenced in merge")
            if 'merge' in sdef['df'].keys():
                # get new namespace if specified
                (ns, id) = self.parse_qid(qid, initial_ns)
                for mqid in sdef['df']['merge']:
                    # make name space explicit to match any specified in qid
                    (mns, mid) = self.parse_qid(mqid, ns)
                    emqid = "%s:%s" % (mns, mid)
                    to_check.append(emqid)
                    # to_check.extend(sdef['df']['merge'])
            checked.append(qid)
        return checked
       
    def process_merge(self, expanded_def, all_to_merge, to_include, id_sources,
        initial_ns, loc, descriptions=[]):
#         all_to_merge = self.file.find_all_merge(initial_to_merge, self.sdef['ns'])
#         self.merged = all_to_merge  # save for use in validating links
        # print "In process merge, all_to_merge = %s" % all_to_merge
        for qid in reversed(all_to_merge):
            # print "-- calling merge_def with qud=", qid
            sdef = self.get_sdef(qid, initial_ns, "Referenced in merge")
            self.merge_def(expanded_def, sdef, to_include, id_sources, loc, descriptions)


class SchemaIdError(Exception):
    # SchemaIdError is raised when attempting to create a group or dataset that
    # does not have an identifier in the schema.  e.g. make_group("invalid_id")
    pass


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
            and value is a tuple: (file, path) - file name and path within file.
        """
        self.file = file
        self.sdef = sdef
        id_noslash = sdef['id'].rstrip("/")  # remove trailing slash in case it's a group
        v_id = re.match( r'^<[^>]+>$', id_noslash) # True if variable_id (in < >)
        if type(name) is Group:
            # linking to a group
#             self.link_node = name  # link_node is no longer used
            # if variable id, use name of target group, otherwise keep name the same
            name = name.name if v_id else id_noslash
        else:
#             self.link_node = None
            if v_id:
                if name == '':
                    msg = "** Error: name for %s '%s' must be specified" % (sdef['type'], id_noslash)
                    error_exit(msg)
            else:
                if name != '':
                    msg = ("** Error: %s name '%s' is fixed.  Cannot create (or link)"
                        " with name '%s'") % (sdef['type'], id_noslash, name)
                    error_exit(msg)
                else:
                    name = id_noslash
        # testing for at root.  TODO: See if is principled way to avoid doing this
        if name == '' and path == '':
           # at root
           name = '/'              
        self.name = name
        self.path = path
        self.full_path = self.file.make_full_path(path, name)
        self.attrs = self.file.cast_to_dict(attrs)
        self.attributes = {} # for attributes defined in specification language
        self.h5attrs = {}  # attributes that mirrors what is in hdf5 file
        self.add_node_identifier()
        self.parent = parent
        self.link_info = link_info
        self.create_link()
        self.check_for_link_expected()
        self.save_node()
        
    # following allows using "sorted" on list of nodes, sorting by full_path
    def __cmp__(self, other):
        return cmp(self.full_path, other.full_path)
        
  
    def create_link(self):
        """ If node is being linked to another node, create the link in the hdf5 file"""
        if self.link_info:
            link_type = self.file.options['link_type']
            if 'node' in self.link_info:
                target_node = self.link_info['node']
                if target_node:
                    # if have target node always validate link even if reading file
                    find_links.validate_link(self.file, self, target_node)
                    if self.file.reading_file:
                        # reading file.  Don't save link information because all links loaded in advance
                        return
                    # not reading, save the link information for later use in autogen
                    # find_links.save_info(objtype, objno, path, target, links):
                    find_links.save_info("link", None, self.full_path, target_node.full_path, self.file.links)
                elif self.file.reading_file:
                    # reading file; and don't have target node (it was not created yet.  Do nothing.
                    return
                # above elif not necessary because if reading the file code below will not create links
                # because and create_dataset and create_softlink do not operate if reading
                target_path = self.link_info['node'].full_path
                if link_type == 'string':
                    # create string dataset containing link path
                    #- self.file.file_pointer.create_dataset(self.full_path, data="h5link:/" + target_path)
                    self.file.create_dataset(self.full_path, data="h5link:/" + target_path)
                elif link_type == 'soft':
                    # create link to target using h5py Softlink.
                    #- self.file.file_pointer[self.full_path] = h5py.SoftLink(target_path)
                    self.file.create_softlink(self.full_path, target_path)
                else:               
                    raise Exception('Invalid option value for link_type (%s)' % link_type)
            elif 'extlink' in self.link_info:
                file, path = self.link_info['extlink']
                if not self.file.reading_file:
                    # save link to external file if reading file, for possible use in finding
                    # common targets (used to generate 'data_link' and 'timestamp_link" in nwb
                    target= "%s\n%s" % (file, path)
                    find_links.save_info('ext_link', None, self.full_path, target, self.file.links)
                # link to external file
                if link_type == 'string':
                    # create string dataset containing link path
                    target_path = "%s,%s" % (file, path)
                    #- self.file.file_pointer.create_dataset(self.full_path, data="h5extlink:/" + target_path)
                    self.file.create_dataset(self.full_path, data="h5extlink:/" + target_path)
                elif link_type == 'soft':
                    # create link to external file
                    #- self.file.file_pointer[self.full_path] =  h5py.ExternalLink(file,path)
                    self.file.create_external_link(self.full_path, file, path)               
                else:
                    raise Exception('Invalid option value for link_type (%s)' % link_type)
            else:
                raise SystemError("** Error: invalid key in link_info %s" % self.link_info)
    
    def check_for_link_expected(self):
        """ Check for link specified in definition of node (i.e. this node should be a
        link) but it's not a link.  If this happens, need to generate a warning (or
        error) and substitute the definition of the item linked-to, for the link
        definition"""
        if 'link' not in self.sdef['df'] or self.link_info is not None:
            return
        inc_path = self.get_include_path()
        msg = "%s:\n(Id path='%s') expecting link but found %s" % (self.full_path, inc_path, self.sdef['type'])
        self.file.error.append(msg)
        self.link_info = {"node": None, "error": "Expected link not present"}
        return
        # import pdb; pdb.set_trace()
        
    
    def save_node(self):
        """ Save newly created node in id_lookups (if node is defined structure created
        at top level) and in "node_tree".  Nodes stored in both of these are later used
        for validating that required nodes are present.
        Also save in 'path2node' - that's used for file object get_node method"""
        if self.sdef['id'] == '////scratch_group':
            # do not save scratch group.  That used for reading
            return
        # save node in path2node
        if self.full_path in self.file.path2node:
            print "** Error, created node with path twice:\n'%s'" % self.full_path
            # import pdb; pdb.set_trace()
            error_exit()
        self.file.path2node[self.full_path] = self            
        # save node in id_lookups
        id = self.sdef['id']
        ns = self.sdef['ns']
        type = self.sdef['type']
        custom = 'custom' in self.sdef and self.sdef['custom']
        location = 'location' in self.sdef and self.sdef['location']
        top = 'top' in self.sdef and self.sdef['top']
        if top and self.sdef['df'] and not custom:
            # structure (not custom) created at top level, save in id_lookups
            if id not in self.file.id_lookups[ns]:
                msg = "** Error: Unable to find id '%s' in id_lookups when saving node" % id
                error_exit(msg)
            if self.path not in self.file.id_lookups[ns][id]:
                print ("** Error: Unable to find path '%s' in id_lookups when"
                    " saving node %s") % (self.path, id)
                print "self.sdef['df'] is:"
                pp.pprint (self.sdef['df'])
                error_exit()
            self.file.id_lookups[ns][id][self.path]['created'].append(self)
        # save node in node_tree, either directly (if root node) or inside
        # mstats structure of parent node
        if self.parent is None:
            # this is the root node, save it directly
            self.file.node_tree = self
        else:
            if id not in self.parent.mstats:
                self.parent.mstats[id] = { 'df': {}, 'type':type, 'ns': ns,
                    'created': [ self, ], 'qty':'?' }
#                 if custom or location:
#                     # custom or location node created, add id to mstats of parent
#                     self.parent.mstats[id] = { 'df': {}, 'type':type, 'ns': ns,
#                         'created': [ self, ], 'qty':'?' }
#                 else:
#                     print "** Error: Unable to find key '%s' in parent mstats" % id
#                     print "self.parent.mstats is"
#                     pp.pprint (self.parent.mstats)
#                     print "node info is"
#                     pp.pprint(vars(self))
#                     print "top is", top
#                     traceback.print_stack()
#                     sys.exit(1)
            else:          
                # append node to parent created mstats                   
                self.parent.mstats[id]['created'].append(self)
                
    def add_node_identifier(self):
        """ If requested in options, add an attribute indicating if this node is custom, defined
        in an extension, or specifying a schema id (namespace:id)"""
        # attribute id to set.  Assume not setting anything
        aid = None
        if self.sdef['df']:
            # this node has a definition (not custom)
            ns = self.sdef['ns']
            id = self.sdef['id']
            qid = "%s:%s" % (ns, id)
            if ns == self.file.default_ns:
                # is defined in the default_ns.  If requested save the schema_id
                if self.file.options['identify_normal_nodes']:
                    aid = self.file.options['normal_node_identifier']
                    a_value = qid
            else:
                # is defined in an extension (not the default namespace)
                if self.file.options['identify_extension_nodes']:
                    aid = self.file.options['extension_node_identifier']
                    a_value = qid
        else:
            # this node is custom (has no definition)
            if self.file.options['identify_custom_nodes']:
                cni = self.file.options['custom_node_identifier']
                assert (isinstance(cni, (list, tuple)) and len(cni) == 2 
                    and isinstance(cni[0], str) and isinstance(cni[1], str)), ("Invalid value "
                    "for option 'custom_node_identifer', must be [attribute_id, value], is: %s") % cni
                aid, a_value = cni
        if aid:
            # found node that needs to be identified, identify it
            self.attributes[aid] = {'value': a_value, 'data_type': 'text', 'qty': '!', 'const': True} 

        
    def get_attributes_ddt(self):
        """ Get the "decoded data type" (ddt) for the nodes attributes (stored
        in self.attributes.  Self.attributes is used to store the attributes
        for the node.  It is set initially by the attributes in the node
        definition (sdef['df']['attributes'] merged with any attributes from
        groups merged with this one.  After that, routine merge_attrs merges
        attributes that are passed in using the call to set_dataset or make_group."""
        ats = self.attributes  # convenient shorthand
        for aid in ats:
            if 'autogen' in ats[aid]:
                # 'data_type' not required in autogen
                continue
            if 'data_type' not in ats[aid]:
                print "%s: data type not specified for attribute '%s'" % (self.full_path,
                    aid)
                # import pdb; pdb.set_trace()
                error_exit()
            if 'const' in ats[aid] and 'value' not in ats[aid]:
                msg = "%s: value not provided for const attribute '%s'" % (self.full_path,
                    aid)
                error_exit(msg)
            ats[aid]['ddt'] = decode_data_type(ats[aid]['data_type'], self.full_path)
            
    def update_attribute_value(self, aid, nv):
        """ Update attribute with new value (nv).  Checks to be sure not
        attempting to change a 'const' attribute and also checks for data type"""
        ats = self.attributes   # convenient shorthand
        if aid not in ats:
            # setting custom attribute
            self.attributes[aid] = {'qty': 'custom'}
        if 'ddt' not in ats[aid]:
            if 'autogen' not in ats[aid]:
                # setting custom attribute, perhaps again.  autogen is not custom        
                self.remember_custom_attribute(self.full_path, aid, nv)
        else:
            # check for 'const' (variables that cannot be changed)
            if 'const' in ats[aid] and ats[aid]['const']:
                if self.file.reading_file:
                    # reading file (either for validation or to append).  Don't change
                    # const attribute value.  If value in file does not match, validation
                    # check run at end will generate error
                    return
                val = ats[aid]['value']
                print "%s: attempting to change 'const' attribute '%s' value from '%s' to '%s'" % (
                    self.full_path, aid, val, nv)
                # import pdb; pdb.set_trace()
                error_exit()
            # check data type
            ddt = ats[aid]['ddt']
            dtype, shape = self.file.get_dtype_and_shape(nv)
            if not valid_dtype(ddt, dtype):
                msg = ("'%s': expecting type '%s' assigned to attribute [%s], but value being stored"
                    " is type '%s'") % (self.full_path, ddt['orig'], aid, dtype)
                self.file.error.append(msg)
            if not shape == "scalar":
                if not "dimensions" in ats[aid]:
                    msg = ("%s: array (shape %s) being stored in attribute '%s', but"
                        " no dimensions specified; new value=%s") % (self.full_path, shape, aid, nv)
                    # import pdb; pdb.set_trace()
                    self.file.error.append(msg)
                else:
                    dimo = self.find_matching_dimension(ats[aid]["dimensions"], shape, dtype, nv, aid)
                    if dimo:
                        # save found dimension for future use in references (not implemented)
                        pass
        self.attributes[aid]['nv'] = nv
        return

    def merge_attrs(self):
        """ Merge attributes specified by 'attrs=' option when creating node into
        attributes defined in specification language.  Save values using key 'nv'
        (stands for 'new_value')"""
        # before merging get decoded data type
        self.get_attributes_ddt()
        # now merge, doing type checking
        for aid in self.attrs:         
            nv = self.attrs[aid]
            self.update_attribute_value(aid, nv)
            
         
    def set_attr_values(self):
        """ set attribute values of hdf5 node.  Values to set are stored in
        self.attributes, either in the values key (for values specified in
        the specification language or in the 'nv' key (for values specified
        via the API
        """
        if self.file.reading_file or self.file.options['mode'] == 'no_file':
            # don't set attributes in hdf5 file if reading
            return
        ats = self.attributes  # convenient short name
        for aid in ats:
            value = ats[aid]['nv'] if 'nv' in ats[aid] else (
                ats[aid]['value'] if 'value' in ats[aid] else None)
            if value is None:
                continue
            if (isinstance(value, (str, unicode))):
                # convert string value to numpy string, so string in hdf5 file will be fixed length
                # see: http://docs.h5py.org/en/latest/strings.html
                value = np.string_(value)
            # save attribute value for later validation
            self.h5attrs[aid] = value
#                 self.h5node.attrs[aid] = value
            #- self.file.file_pointer[self.full_path].attrs[aid] = value
            self.file.set_attribute(self.full_path, aid, value)
            #- self.file.h5save_attribute(self.full_path, aid, value)
            #- self.file.h5commands.append("set attribute(%s:%s)-%s" % (self.full_path,
            #-     aid, value))
                
    def set_attr(self, aid, value, custom=False):
        """ This is one of the functions for the API.
        Set attribute with key aid to value 'value'.  If custom True
        could inhibit warning messages if setting custom attribute.
        Right now no warning is generated anyway. """
        self.update_attribute_value(aid, value)
#         if aid not in self.attributes and not custom:
#             # print "** Warning: non-declaired attribute %s['%s'] set to:\n'%s'" % (
#             #    self.name, aid, value)
        if (isinstance(value, (str, unicode))):
            # convert string value to numpy string, so string in hdf5 file will be fixed length
            # see: http://docs.h5py.org/en/latest/strings.html
            value = np.string_(value)
        self.file.set_attribute(self.full_path, aid, value)
        # save value for validation
        self.h5attrs[aid] = value
        
    def remember_custom_attribute(self, node_path, aid, value):
        """ save custom attribute for later reporting """
        msg = "'%s' [%s]:'%s'" % (node_path, aid, value)
        self.file.custom_attributes.append(msg)
            
       
    def check_attributes_for_autogen(self):
        """ Check attributes for any "autogen" specifications.  If any are found
        save them for later processing."""
        for aid in self.attributes:
            dict = self.attributes[aid]
            find_links.check_for_autogen(dict, aid, self.full_path, self.sdef['type'], self.file)
            
     

    def find_matching_dimension(self, dims, shape, dtype, val, aid=None):
        """ Find dimension option in 'dims' that matches shape of data.
        -dims is either a list of dimension names, e.g. ["a", "b", ...], 
        or a list of lists, e.g.: [ ["a", "b"], ["a", "b", "c"] ].  The second
        form is used if the data stored can have more than one shape
        (for example, if both a grayscale and color image could be stored, might
        require option of a 2-d and 3-d array, e.g. [ ["x", "y"], ["x","y","rgb"]].
        "dtype" is the type of data being stored.
        "aid" is an attribute id, if the dimensions were specified in an
        attribute.  Otherwise None. 
        val - is value being stored.  Is displayed if error.
           This routine returns the matching dimension or None if not found.
        """
        # for any error messages, include attribute name if inside an attribute
        atname = " (attribute %s)" % aid if aid else ""
        # if dims is list of strings, make it list of lists
        if isinstance(dims[0], str):
            dims = [dims, ]
        else:
            assert isinstance(dims[0], list), ("%s%s Invalid dimensions specified, "
                "must be list of strings, or list of list of stings: %s" % (
                self.full_path, atname, dims))
        if shape == 'scalar':
            inc_path = self.get_include_path()
            value_summary = self.make_value_summary(val)
            vs = "; value='%s'" % value_summary if value_summary else ""
            msg = ("%s%s: Expecting array because dimensions%s %s"
                " but value assigned is scalar with type '%s'%s") % (
                self.full_path, atname, inc_path, dims, dtype, vs)
#             msg = "%s%s: No dimensions%s %s match shape %s %s being stored%s" % (
#                   self.full_path, atname, inc_path, dims, shape, dtype, vs)
            self.file.error.append(msg)
            return None
        # try to find dimension option that matches shape
        found_match = False
        for dimo in dims:   # dimension option
            if len(dimo) == len(shape):
                found_match = True
                break
        if not found_match:
            inc_path = self.get_include_path()
            value_summary = self.make_value_summary(val)
            vs = "; value='%s'" % value_summary if value_summary else ""
            msg = "%s%s: No dimensions%s %s match value shape %s %s%s" % (
                  self.full_path, atname, inc_path, dims, shape, dtype, vs)
            self.file.error.append(msg)
            return None
        return dimo
        
    def get_include_path(self):
        """ Returns path of Ids from most recent ancestor include to this node.  e.g.
        "<ImageSeries>/external_file" if called from node "external_file".  Or return
        empty string if no recent include.  This path is included in error and warning messages
        to help the user identify the type of node the message applies to"""
        inc_path = []
        node = self
        inc_ns = None
        while node.parent and not inc_ns:
            id = node.sdef['id']
            inc_path.append(id)
            parent = node.parent
            pms = parent.mstats[id]
            if 'include_info' in pms:
                # found include_info, this is where structure was included (start of include path)
                # save ns both to stop loop and also in case not default_ns
                inc_ns = pms['include_info']['ns']
            else:
                # did not find include in this parent, try parent parent
                node = node.parent
        if inc_ns:
            nss = "%s:" % inc_ns if inc_ns != self.file.default_ns else ""
            inc_path = nss + "".join(reversed(inc_path))
            return " in " + inc_path
        else:
            return ""
            
    def make_value_summary(self, val):
        # make summary for a single value.  val either contains the value, or starts with
        # the string 'value_info: type="'
        if isinstance(val, str) and val.startswith('value_info: type="'):
            # value not available.  This called when reading a file and value in file not loaded
            return None
        val_str = str(val)
        if len(val_str) > 40:
            val_str = val_str[0:40]+"..."
        return val_str

  
             
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
        # change made in version for reading.  Now do nothing if this node is a link
        if self.link_info:
            # this dataset set to link to another.  Already done in Node.  Nothing to do here
            return
        # print "Creating Dataset, sdef="
        # pp.pprint(sdef)
        if 'attributes' in self.sdef['df']:
            # self.attributes = copy.deepcopy(self.sdef['df']['attributes'])
            # merge attributes into empty self.attributes so have source saved
            # print "calling merge_attribute_defs for dataset id %s, ns %s" % (self.sdef['id'], self.sdef['ns'])
            self.file.merge_attribute_defs(self.attributes, self.sdef['df']['attributes'])
            # del self.sdef['df']['attributes']  # if do this, no need to check for attributes in mk_dsinfo
        # check for autogen in attributes
        self.check_attributes_for_autogen()
        # check for autogen in dataset definition
#        a = find_links.check_for_autogen(self.sdef['df'], None, self, self.file)
#         if a:
#             # found autogen in dataset definition
#             # do not save dataset now.  Will create dataset when computing autogen
#             # flag autogen so function validate_dataset dataset will ignore
#             self.dsinfo = {"autogen": True}
#             return
        self.dsinfo = self.mk_dsinfo(value)
        # atags not used anymore
        # self.file.merge_attribute_defs(self.attributes, self.dsinfo['atags'])
        # else:
            # definition empty, must be custom dataset
        #    self.dsinfo = {}
        self.merge_attrs()
        if self.link_info:
            # this dataset set to link to another.  Already done in Node.  Nothing to do here
            pass
        else:
#             if self.full_path == "/processing/ROIs/DfOverF/fov_16002/roi_names":
#                 import pdb; pdb.set_trace()
            # creating new dataset (normally done)
            if (not dtype and self.dsinfo['ddt'] and self.dsinfo['ddt']['type'] == 'binary'
                and isinstance(value, (str, unicode))):
                # set dtype to binary to flag, save string value using h5py np.void(),
                # as described at: http://docs.h5py.org/en/latest/strings.html
                dtype = 'binary'
            elif (isinstance(value, (str, unicode))):
                # convert string value to numpy string, so string in hdf5 file will be fixed length
                # see: http://docs.h5py.org/en/latest/strings.html
                # before converting encode using utf-8 to prevent 
                # UnicodeEncodeError: 'ascii' codec can't encode characters 
                # value = np.string_(value.encode('utf-8'))
                value = np.string_(value)
            elif (isinstance(value, (np.ndarray)) and str(value.shape) == "(1,)"
                    and str(value.dtype) == 'object'):
                # this added because sometimes strings are np.ndarray, (example,
                # virus_text from Svboda lab ssc-1).  Try to convert to np.string_
                value = np.string_(value)
            elif not dtype and self.file.options['use_default_size']:
                dtype = self.get_default_dtype()
            # use automatic compression if specified and either np_string or not scalar
            if (not compress and self.file.options['auto_compress'] and
                (self.dsinfo['shape'] != "scalar") and
                not isinstance(value, np.string_)):
                compress = True
            maxshape=self.get_maxshape()
            # compress = "gzip" if compress else None
            # self.h5node = self.h5parent.create_dataset(self.name, data=value,
            #    dtype=dtype, compression=compress)
            #- self.file.file_pointer.create_dataset(self.full_path, data=value,
            #-     dtype=dtype, compression=compress)
            self.file.create_dataset(self.full_path, data=value, dtype=dtype,
                compress=compress, maxshape=maxshape)
            # self.file.h5commands.append("create_dataset(%s, %s)" % (self.full_path, value))
            # if dtype:
            #    self.h5node = self.h5parent.create_dataset(self.name, data=value, dtype=dtype)
            # else:  # should find out what default value for dtype used in h5py and use that, combine these
            #    self.h5node = self.h5parent.create_dataset(self.name, data=value)
        self.set_attr_values()
        
    def get_maxshape(self):
        """Check if this dataset has any dimensions named "*unlimited*".  If so,
        return shape of data, with unlimited dimension set to None, as would be used
        to set maxshape in call to h5py."""
        dims = self.dsinfo['dimensions']
        if '*unlimited*' not in dims:
            return None
        shape = self.dsinfo['shape']
        if not isinstance(shape, (list, tuple)):
            error_exit("Found '*unlimited*' dimension, but data shape (%s) is not a list" % shape)
        maxshape = []
        for i in range(len(shape)):
            msv = shape[i] if dims[i] != '*unlimited*' else None
            maxshape.append(msv)
        return maxshape
            
    def append(self, value):
        """append a value to an expandable dataset.  This method is only valid for
        datasets defined with a dimension set to "*unlimited*".  It resizes the dataset
        then appends the value"""
        dims = self.dsinfo['dimensions']
        if '*unlimited*' not in dims:
            msg = "append called on dataset '%s', but no dimension set to '*unlimited*'" % (
                self.full_path)
            error_exit(msg)
        if len(dims) > 1:
            msg = "%s: append currently allowed for 1-D datasets.  Dims is:" % (
                self.full_path, dims)
            error_exit(msg)  
        # dataset being appended
        dset = self.file.file_pointer[self.full_path]
        shape = dset.shape
        # make new shape one larger in '*unlimited*' dimension
        new_shape = []
        for i in range(len(shape)):
            nsv = shape[i]+1 if dims[i] == '*unlimited*' else shape[i]
            new_shape.append(nsv)
        dset.resize(new_shape)
        new_length = new_shape[0]
        dset[new_length - 1] = value


    def get_default_dtype(self):
        """ Get default data type from specification to use when creating dataset.
        Also checks for expandable array of text and if found creates h5py special_dtype
        """
        if not self.dsinfo['ddt'] or self.dsinfo['ddt']['type'] in ("number", "any"):
            # no information specified about data type
            # if int64, default to int32, if float64, default to float32
            # TODO: This should be made an option
            val_type = self.dsinfo['dtype']
            if val_type == "int64":
                dtype = "int32"
            elif val_type == "float64": 
                dtype = "float32"
            else:
                dtype = None
            return dtype
        ddt = self.dsinfo['ddt']
        if not ddt['default_size']:
            # no default size
            # check for unlimited (expandable) dimension and type text
            if ddt['type'] == 'text':
                dims = self.dsinfo['dimensions']
                if '*unlimited*' in dims:
                    # return special dtype for variable length strings
                    dtype = h5py.special_dtype(vlen=bytes)
                    # print "get_default_dtype returning h5py.special_dtype(vlen=bytes)"
                    return dtype
            # not special case of text and unlimited dimensions
            # this should perhaps be enhanced to allow variable length arrays of other types
            return None
        # TODO: set default to int32, float32 if default_size not specified.  Also, make this an option
        default_size = ddt['default_size']
        if ddt['type'] in ('int', 'uint'):
            dtype = ddt['type'] + str(default_size)
            return dtype
        if ddt['type'] == 'float':
            dtype = "f" + str(default_size / 8)
            return dtype
        if ddt['type'] == 'text':
            # this should never be called because strings converted to np.string_ without
            # calling this function
            sys.error("attempting to specify width of string.  Not allowed.")
            # dtype = 'S' + str(default_size)
            # return dtype
        # if not int, float or text, don't return default dtype
        return None


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
            dimensions - list of dimensions. The list is an outer list with
                one or more inner lists; each inner list is one of the possible
                dimension options.  This allows specifying, for example, that the
                there can be either a 2-d or 3-d array.
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
        dsinfo['dimensions'] = []
        dsinfo['dimdef'] = {}
        # dsinfo['ref'] = ''
        dsinfo['dtype'] = ''     # type actually present in val, e.g. 'int32'
        # dsinfo['data_type'] = '' # type specified in definition, e.g. int, float, number, text
        # decoded data type.  Values are decoded from data_type string. 
        dsinfo['ddt'] = None  # decoded data type (from specification)
        dsinfo['shape'] = ''     # shape of array or string 'scalar'
        # dsinfo['unit'] = ''
        # dsinfo['semantic_type'] = '' 
        dsinfo['atags'] = {}
        df = self.sdef['df']
        # save all referenced atags
        for tag in atags:
            # don't save descriptions or semantic_type by default
            # SKIP atags.  No longer used.  (Hence if False below).
            if False and tag in df and tag not in ('description', 'semantic_type'):
                dsinfo['atags'][atags[tag]['atname']] = {
                    'data_type': atags[tag]['data_type'],
                    'description': atags[tag]['description'],
                    'value': df[tag],}      
        if self.link_info:
            # setting this dataset to another dataset by a link
            # get previously saved info about dataset linking to
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
            dsinfo['dtype'], dsinfo['shape'] = self.file.get_dtype_and_shape(val)
        if 'dimensions' in df:
            dimo = self.find_matching_dimension(df['dimensions'], dsinfo['shape'], dsinfo['dtype'], val)
            if dimo:
                # found matching dimension option           
                # check for any dimensions defined in dataset.  If found save them
                dsinfo['dimensions'] = dimo
                i = 0
                for dim in dimo:
                    if dim.endswith('^'):
                        scope = 'global'
                    else:
                        scope = 'local'
                    dsinfo['dimdef'][dim] = {'scope':scope, 'len': dsinfo['shape'][i]}
                    if dim in df.keys():
                        dsinfo['dimdef'][dim].update(df[dim])
                    i = i + 1
#                 if not isinstance(df['dimensions'][0], str):
#                     print "%s: Found matching dimensions: %s, dimdef= %s" %(
#                         self.full_path, dimo, dsinfo['dimdef'])
        if 'attributes' in df.keys():
            pass  # do nothing here, attributes moved to self.attributes     
        if 'data_type' in df.keys():
            # dsinfo['data_type'] = df['data_type']
            dsinfo['ddt'] = decode_data_type(df['data_type'], self.full_path)
        else:
            if not df:
                # nothing specified for dataset definition.  Must be custom dataset
                # (being created by "set_custom_dataset").  Do no validation
                return dsinfo
            print "** Error: 'data_type' not specified in dataset definition"
            print "definition is:"
            pp.pprint(df)
            error_exit()
        # Now, some simple validation
        if dsinfo['dtype'] and not valid_dtype(dsinfo['ddt'], dsinfo['dtype']):
            msg = ("'%s': default dataset type is '%s', but value passed"
                " is '%s'") % (self.full_path, dsinfo['ddt']['orig'], dsinfo['dtype'])
            self.file.warning.append(msg)  
        # make sure everything defined in dataset definition is valid
        for key in df.keys():
            if (key in ('dimensions', 'data_type', 'attributes', 'autogen',
                '_source_id', '_qty') or
                key in atags or key in dsinfo['dimensions']):
                continue
            print "** Error, invalid key (%s) in dataset definition" % key
            print "dataset definition is:"
            pp.pprint(df)
            error_exit()
        return dsinfo                                 
        


def decode_data_type(dt_spec, path):
    """ Decode data_type specification to produce: dinfo['ddt'] - (decoded data type).
    dt_spec has form: <type>default_size!?]
    <type> == uint|int|float|text| others...;  everything above in [] is optional.  Trailing "!" indicates
    that the size is a required minimum size.  returns fields:
    {  'orig': <original dt_spec>,
       'type': <int|float|text...>,
       'default_size': number of bits or None,
       'minimum_size': number of bits or None,
       'unsigned': False or True}
    """
    pattern = "(bool|byte|text|number|int|uint|float|binary|any)(?:(\d+)(!?))?"
    match = re.match(pattern, dt_spec)
    if match:
        type = match.group(1)
        # unsigned = match.group(2)
        size = match.group(2)
        size = int(size) if size else None
        is_min = match.group(3)
    else:
        print "%s: Invalid specification for data type: '%s'" % (path, dt_spec)
        print "should be like: 'int', 'int32', 'int32!', 'uint8', 'float64!'"
        print "Number if specified is default size. '!' means is minimum size"
        error_exit()
    if size and size % 8 != 0 and type not in ('text', 'binary'):
        raise ValueError('Size specified for datatype must be multiple of 8: "%s"' % dt_spec)
    ddt = {
        'orig': dt_spec,
        'type': type, 
        'default_size': size,
        # 'unsigned': True if unsigned == 'u' else False,
        'minimum_size': size if is_min == '!' else None}
    return ddt


def valid_dtype(ddt, found):
    """ Return True if found data type is consistent with expected data type.  Inputs are:
    ddt - decoded data type from "data_type" property (the expected value).  Has fields:
       orig, type, default_size, unsigned, minimum_size.  See function decode_data_type
    for meanings.
    found - data type generated by python dtype converted to a string."""
    etype = ddt['type']
    # Check for ddt type matches passed in value
    if etype not in ('bool', 'byte', 'text', 'number', 'int', 'uint', 'float', 'binary', 'any'):
       raise SystemError(("** Error: invalid value (%s) in definition "
          "for expected data type") % ddt['orig'])
    if etype == 'any':
        return True
    if found == 'binary':
        dtype = 'binary'
    elif found in ('str', 'unicode', 'text') or re.match( r'^\|S\d+$', found) or 'byte' in found:
        # print "found dtype '%s', interpreting as string" % dtype
        dtype = 'text'
#         # if expected type if binary, pretend found type is binary.  Otherwise text
#         dtype = 'binary' if etype == 'binary' else 'text'
    elif 'bool' in found:
        dtype = 'bool'
    elif 'uint' in found:
        dtype = 'uint'
    elif 'int' in found or 'long' in found:
        dtype = 'int'
    elif 'float' in found or 'double' in found:
        dtype = 'float'
    else:
        # raise ValueError(("** Error: unable to recognize data type (%s) for validation."
        #     "expecting compatible with '%s'") % (found, etype))
        # don't abort here.  Return not valid.  This happens with type 'object'
        return False
    valid_type = (dtype == etype 
        or (dtype in ('int', 'float', 'uint', 'bool', ) and etype == 'number')
        or (dtype in ('int', 'uint') and etype == 'int')
        # binary can be int, text (string), or binary
        or (dtype in ('int', 'uint', 'text', 'binary') and etype == 'binary'))
    # possible TODO:  might be good to check for size here, but it's difficult to determine size
    # of data passed in because there are many different types.  Instead, check sizes using value
    # stored in hdf5 file at the end.  That is needed for validation anyway.
    return valid_type


def patch_json_vals(json, replace):
    # Replace old_values with new_values in json
    # json is a dict (basically JSON format)
    # replace is a dict mapping old_values to new_values
    # This used to replace string "float('NaN')" with float('NaN') i.e. and actual NaN.
    for key in json.keys():
        if type(json[key]) is dict:
            patch_json_vals(json[key], replace)
        elif type(json[key]) is str and json[key] in replace:
            json[key] = replace[json[key]]
  
  
def error_exit(msg = None):
    if msg:
        print("** Error: " + msg)
    print("Stack trace follows")
    print("-------------------")
    traceback.print_stack()
    sys.exit(1)

  
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
        # if this id was part of a subclass_merge, prune the others and possibly change id
        sdef['id'] = self.prune_subclass_merges(parent, sdef['id'])
        super(Group, self).__init__(file, sdef, name, path, attrs, parent, link_info)
        # change for reading file.  Now if link_info, do nothing.
        # All information is in target link
        if self.link_info:
            return
        self.description = []
        # self.parent_attributes = {}
        self.get_expanded_def_and_includes()
        self.check_attributes_for_autogen()
        # print "after get_expanded_def_and_includes, includes="
        # pp.pprint(self.includes)
        self.get_member_stats()
        self.check_mstats_for_autogen()
        # self.add_parent_attributes()
        self.merge_attrs()
        if self.link_info:
            # this group is linking to another.  Already done in Node class.  Nothing to do here
            pass
        else:
#             self.h5node = self.h5parent.create_group(self.name)
            #- self.file.file_pointer.create_group(self.full_path)
            #- self.file.h5commands.append("create_group(%s)" % self.full_path)
            if self.full_path != "/":  # root group already exists.  Cannot create it.
                self.file.create_group(self.full_path)
        # add attribute values to node
        self.set_attr_values()


    def check_mstats_for_autogen(self):
        """ Check for any members (groups or datasets) within this group that are 
        created by autogen.  If found, save the information necessary to create them
        automatically (using autogen) when the file is closed if they have not been 
        created already.  To find the datasets in this group that have autogen, the 
        "mstats" (member stats" dictionary is searched. """
        for id in self.mstats:
            minfo = self.mstats[id]
            if 'autogen' in minfo['df']:
                # found autogen.  Make sure member does not have a variable name
                v_id = re.match( r'^<[^>]+>/?$', id)   # True if variable_id (in < >)
                if v_id:
                    print ("%s: %s  - Cannot use autogen to fill value of variable named "
                        "(i.e. name in <>) node because autogen has no way of knowing what "
                        "the name should be.") % (self.full_path, id)
                    error_exit()
                # has a fixed name.  Save it for later processing
                # make full path to future
                mtype = minfo['type']
                mpath = self.file.make_full_path(self.full_path, id)
                find_links.check_for_autogen(minfo['df'], None, mpath, mtype, self.file)


    def find_implicit_includes(self):
        """ Find definitions that should be included implicitly into the definition
        for this node.  These are definitions with an absolute path as the id and the
        node located in this group (path to group containing node is the same as the
        path to this group).
        To do this, makes "implicit_includes" structure, which has:
          { mid1: [(ns, id, qty), (ns, id, qty), ...], mid2: [ ... ], }
        each 'mid' is the member id to be stored in mstats, id is the full source id.
        Implicit includes are only added if one does not already exist with the same
        mid in self.includes.
        """
        full_path = self.full_path
        if full_path is None:
            # no full path (perhaps called by make_id_sigs), can't find implicit includes
            return
        implicit_includes = {}
        tns = self.sdef['ns']  # this namespace (namespace for this group)
        if full_path[0] != '/':
            full_path = "/" + full_path
        full_path_g = full_path if full_path.endswith('/') else full_path + "/"
        for ns in self.file.ddef:
            structures = self.file.ddef[ns]['structures']
            for id in structures:
                if id[0] != '/' or id == "/":
                    # not absolute path, or is root (root can never be included in any group)
                    continue
                parent_path, basename = self.file.get_name_from_full_path(id)
                parent_path_g = parent_path + '/' if not parent_path.endswith('/') else parent_path
                if parent_path_g.startswith(full_path_g):
                    # found id to include
                    # '_qty' key may have been added by function File.reformat_structures
                    qty = structures[id]['_qty'] if '_qty' in structures[id] else '!'
                    # mid = basename
                    mid = self.get_path_part(full_path_g, id)
#                     print "get_path_part, prefix='%s', full_path='%s', returned='%s'" % (
#                         full_path_g, id, mid)                    
                    inc_info = (ns, id, qty)
                    if mid in implicit_includes:
                        implicit_includes[mid].append(inc_info)
                    else:
                        implicit_includes[mid] = [ inc_info, ]
        # explicit_includes = self.expand_explicit_includes()
#         print "implicit_includes="
#         pp.pprint(implicit_includes)
        source = "implicit"
        for mid in implicit_includes:
            if mid not in self.includes:
                mid_info = implicit_includes[mid]
                if len(mid_info) > 1:
                    # find implicit include with shortest path to be sure to get the definition
                    # of it in function get_member_stats.  (If the path was longer than necessary
                    # get_member_stats might create an empty definition, rather than using the
                    # real one).
                    min_path_length = None
                    for i in range(len(mid_info)):
                        (i_ns, i_id, i_qty) = mid_info[i]
                        i_path_length = len(i_id)
                        if min_path_length is None or i_path_length < min_path_length:
                            min_path_length = i_path_length
                            wanted_index = i
#                     print "%s: implicitly including more than one id with same member id: %s" % (
#                         self.full_path, mid)
#                     print "Id's are:"
#                     pp.pprint(mid_info)
#                     print "selected index %i: %s" % (wanted_index, mid_info[wanted_index])
                else:
                    wanted_index = 0
                ns, id, qty = mid_info[wanted_index]
            self.file.save_include(self.includes, mid, id, ns, qty, source, self.sdef['id'])
#                 qidq = "%s:%s%s" % (ns, id, qty)
#             self.includes[qidq] = {}
   
    
    def get_path_part(self, prefix, full_path):
        """ Get part of path after prefix.  prefix must end with slash.
        If full_path starts with prefix, return component of full path
        immediately after prefix.  Example:
        given full_path == "/for/bar/bax/sou"
        prefix == "/foo/bar/" return "bax/"
        prefix == "/foo/bar/bax" returns "sou"
        If full_path does not start with prefix, return None
        """
        assert prefix.endswith('/'), "%s: prefix must end with '/'" % prefix
        if not full_path.startswith(prefix):
            return None
        start = len(prefix)
        end = full_path.find("/", start)
        end = end+1 if end != -1 else len(full_path)
        path_part = full_path[start:end]
        return path_part
                       
    def get_expanded_def_and_includes(self):
        """ Process any 'merge', 'parent_attribute' or 'description' entities.
            Save copy of definition with merges done in self.expanded_def
            Save all includes in self.includes"""
        self.expanded_def = {}
        self.includes = {}
        # save name spaces of id's merged for use in creating mstats
        self.id_sources = {}
#        if self.full_path == "/processing/Units":
#             import pdb; pdb.set_trace()
        to_merge = []
#         if self.sdef['id'] == '<TimeSeries>/':
#             import pdb; pdb.set_trace()
        # order is import.  Put id's to be merged last, first in to_merged
        if 'merge' in self.sdef['df'].keys():
            to_merge.extend(self.sdef['df']['merge'])
        to_merge.extend(self.file.find_overlapping_structures(self.sdef, self.full_path))
        all_to_merge = self.file.find_all_merge(to_merge, self.sdef['ns'])
        # self.merged = all_to_merge  # save for use in validating links (in file find_links)
        # make merges qualified by namespace in front for use in matching links in find_links
        qualified_merged = self.file.make_qualified_ids(all_to_merge, self.sdef['ns'])
        self.merged = qualified_merged
        if all_to_merge:
            self.file.process_merge(self.expanded_def, all_to_merge, self.includes,
                self.id_sources, self.sdef['ns'], self.sdef['id'])
        # if 'merge' in self.sdef['df'].keys():
        #    self.process_merge(self.expanded_def, self.sdef['df']['merge'], self.includes, self.ns_sources)
        # print "-- calling merge_def for id %s, ns %s" % (self.sdef['id'], self.sdef['ns'])
        # pp.pprint(self.sdef)
        self.file.merge_def(self.expanded_def, self.sdef, self.includes, self.id_sources, self.sdef['id'])
        if 'attributes' in self.expanded_def:
            # merge any attributes to self.attributes for later processing
            for aid in self.expanded_def['attributes']:
                if aid in self.attributes:
                    # found conflicting attribute.  If attribute is the schema_id_attr, ignore
                    # it because this may be due to an extension that is subclassing a group
                    # defined in the default_ns.  For NWB this occurs when an extension defines
                    # a new timeseries.  The base class timeseries has neurodata_type "timeseries"
                    # but the extension has a different neurodata_type (e.g. "ns:MyNewTimeseries")
                    # created by function add_node_identifier.  Let the value generated by
                    # add_node_identifier take precedence since that flags the group as being
                    # defined in an extension.  (Also, routine validate_file will be expecting that
                    # value). 
                    # NO LONGER, now using separate identifiers for extensions (extension_node_identifier)             
                    # if aid == self.file.options['schema_id_attr']:
                    #    continue
                    print 'conflicting attribute found when merging into self.attributes: %s' % aid
#                     import pdb; pdb.set_trace()
                    error_exit()
                self.attributes[aid] = self.expanded_def['attributes'][aid]
            # print "calling merge_attribute_defs for id %s, ns %s" % (self.sdef['id'], self.sdef['ns'])
            # self.attributes.update(self.expanded_def['attributes']) # instead of this, make call below so qty processed
            # self.file.merge_attribute_defs(self.attributes, self.expanded_def['attributes'])
            del self.expanded_def['attributes']
        self.generate_subclass_merges()
              
    def generate_subclass_merges(self):
        """Check for any member group having a "subclass merge" (e.g. "merge+").  If so
        replace the group definition with a series of group definitions, one for each
        subclass.  The extra definitions are removed when a particular subclass is
        chosen."""
        # string used in specification language to indicate subclass_merge
        msc = "merge+"
        df = self.expanded_def
        for key in df.keys():
            if key.endswith('/') and isinstance(df[key], dict) and msc in df[key]:
                assert len(df[key][msc]) == 1, ("%s: must be only one element in list when"
                    " using \"%s\": %s") % (self.full_path, msc, df[key][msc])
                orig_df = df[key]
                assert 'merge' not in orig_df, ('%s: cannot have "merge" and "%s" ' %
                    'at same time: %s') % (self.full_path, msc, orig_df)
                base_class = orig_df[msc][0]
                q_base_class = self.file.make_qid(base_class, self.sdef['ns'])
                assert q_base_class in self.file.subclasses, ("%s: %s base class (%s) "
                    "qualified (%s) has no subclasses") % (
                    self.full_path, msc, base_class, q_base_class)
                subclasses = self.file.subclasses[q_base_class]
                # Generate new group definitions by replacing merge+ with merge of
                # all subclasses
                id_base = key.rstrip('/')
                sources = self.id_sources[key]
                subclass_ids = [key,]
                for subclass in subclasses:
                    [ns, ssc] = subclass.split(':')
                    if ssc == base_class:
                        # don't add new entry for base class, modify orig_df
                        continue
                    new_df = copy.deepcopy(orig_df)
                    del new_df[msc]
                    new_df['merge'] = [subclass,]
                    new_id = "%s-%s" % (id_base, ssc)
                    self.expanded_def[new_id] = new_df
                    subclass_ids.append(new_id)
                    # add entry to id_sources
                    self.id_sources[new_id] = sources
                # modify original def, replacing msc with normal merge
                orig_df['merge'] = orig_df[msc]
                del orig_df[msc]
                # save list of subclass_id in node
                self.subclass_merge_ids = subclass_ids
                # scratch_group only used for preparation.  So if scratch_group don't save
                if not hasattr(self,'scratch_group'):
                    # save node for possible
                    # cleanup in function file.prune_unused_subclasses
                    # print "saving subclass-merge: %s" % self.full_path
                    self.file.subclassed_nodes['merge'].append(self)
        return
        
    def prune_subclass_merges(self, parent, id):
        """ Check if id is for an mstats entry generated because of a subclass merge.
        If so, delete all entries not being used, and if necessary, rename the entry that
        is used to the original name.  Return the id name (same as entry if no change,
        or the new name if changed). """
        if not hasattr(parent, 'subclass_merge_ids') or id not in parent.subclass_merge_ids:
            # this id was not used in a subclass_merge
            return id
        id_base = parent.subclass_merge_ids[0]
        # delete subclasses that are not used from mstats and expanded_ids
        for subclass_id in parent.subclass_merge_ids:
            if subclass_id != id:
                del parent.mstats[subclass_id]
                del parent.expanded_def[subclass_id]
        # if needed, rename subclass that is used to id_base
        if id != id_base:
            parent.mstats[id_base] = parent.mstats[id]
            del parent.mstats[id]
            parent.expanded_def[id_base] = parent.expanded_def[id]
            del parent.expanded_def[id]
            id = id_base
        # remove attribute for subclass_merge_ids
        del parent.subclass_merge_ids
        # add attribute to flag that this node was created using a subclass_merge
        # this is used by doc_tools "add_group_doc" function to add the text
        # "(or subclass)" when generating documentation about this node
        self.subclass_merge_base = id_base
        return id
        
        

    def get_member_stats(self):
        """Build dictionary mapping key for each group member to information about the member.
           Also processes includes.  Save in self.mstats """
        self.mstats = {}
        # add in members from expanded_def (which includes any merges)
        for id in self.expanded_def.keys():
            if id == 'merge_into':
                # merge_into was processed in function 'process_merge_into'
                # ignore it here
                continue
            if id == "_properties":
                # _properties currently used only for documentation (to flag group is abstract)
                # not needed here
                continue
#             if id in ("description", "_description"):
#                 # testing not including description
#                 continue
            if id == "_required":
                # don't save _required specification in mstats, save it with object
                self.required = self.expanded_def[id]
                continue
            if id == "_exclude_in":
                # don't save _exclude_in specification in mstats, save it with object
                self.exclude_in = self.expanded_def[id]
                continue
            if id in ('_source_id', '_qty'):
                # _source_id and _qty are not real members.  Ignore.
                # (_source_id is used in function "find_overlapping_structures"
                # to prevent merging absolute path id with itself; _qty is
                # is the quantity specified at end of absolute path_id, moved
                # to _qty by function "File.reformat_structures"
                continue
            # check for trailing quantity specifier (!, *, +, ?).  Not for name space.
            # ! - required (default), * - 0 or more, + - 1 or more, ? - 0 or 1
            # id, qty = self.file.parse_qty(qid, "!")
            qty = self.file.retrieve_qty(self.expanded_def[id], "!")
            if id in self.mstats.keys():
                error_exit("duplicate (%s) id in group" % id)
            type = 'group' if id.endswith('/') else 'dataset'
            if type == 'dataset':
                # check for this being a dimension and not really a dataset
                if 'data_type' in self.expanded_def[id]:
                    # is dataset
                    pass
                elif 'type' in self.expanded_def[id]:
                    # is dimension
                    continue
                else:
                    print ("Unable to determine if member (id='%s') is dataset, "
                        "group or dimension.  expanded_def=:") % id
                    pp.pprint(self.expanded_def)
#                     import pdb; pdb.set_trace()
                    error_exit()
            if id not in self.id_sources:
                print "id %s not found in id_sources:" % id
                pp.pprint(self.id_sources)
                import pdb; pdb.set_trace()
            assert id in self.id_sources, ("%s: id '%s' not found it id_sources when "
                "makeing mstats") % (self.sdef['id'], id)
            id_source = self.id_sources[id]
            # get ns from last element, all elements have format: "ns:id"
            ns = id_source[-1].rpartition(':')[0]
#             print "for id '%s' set mstats ns='%s', id_source='%s'" % (id, ns, id_source)
#             ns = self.ns_sources[id] if id in self.ns_sources else self.sdef['ns']
            # quid = "%s:%s" % (ns, id) if ns != self.file.default_ns else id
            self.mstats[id] = { 'ns': ns, 'qty': qty, 'df': self.expanded_def[id],
                'created': [], 'type': type, 'source': id_source }
        # add in members from any includes
        # first find any id's that are included explicitly (by absolute path)
        self.find_implicit_includes()
        self.add_includes_to_mstats()
        return
 

    def add_includes_to_mstats(self):
        """ Add self.includes to member stats"""
        subclass_include_count = 0
        for mid in self.includes:
            inc_info = self.includes[mid]
            iid = inc_info['id']
            ins = inc_info['ns']
            qty = inc_info['qty']
            if inc_info['source'] == "subclass":
                # keep track of number of subclass includes
                subclass_include_count += 1
            sdef = self.file.get_sdef(iid, ins, "Referenced in include")
            ns = sdef['ns']
            assert ns == ins, "add_includes_to_mstats, ns (%s) != ins (%s)" % (ns, ins)
            df = copy.deepcopy(sdef['df'])
            # retrieve _source set by function reformat_structures
            source = df.pop('_source')
            # source from includes info, should match that from _source
            ii_source = "%s:%s" % (ns, iid)
            assert source == ii_source, "add_includes_to_mstats - source (%s) != ii_source '%s'" % (
                source, ii_source)
            modifiers = inc_info['modifiers']
            if modifiers and len(modifiers) > 0:
                # merge in modifications.  This currently is not used.
                # need to incorporate modifications to definition of included child members
                # df = copy.deepcopy(sdef['df'])
                # self.modify(df, modifiers)
                # this feature currently not used, disable for now.
                print "Includes with modifiers not implemented: %s" % modifiers
                pp.pprint(df)
                # import pdb; pdb.set_trace()
                # self.file.merge(df, modifiers)  # merges modifiers into definition
                # print "df after merging modifiers:"
                error_exit()
            id = sdef['id']
            type = sdef['type']
            # check for id with absolute path.  If so, replace id by path part corresponding
            # to member for this group
            if id[0] == "/" and id != "/":
#                 if id == "/now/for/something/newds":
#                     import pdb; pdb.set_trace()
                # is absolute path, set id to part of path that would be created in this node
                source_id = id
                prefix = self.full_path
                prefix_g = prefix if prefix.endswith('/') else prefix + '/'
                path_part = self.get_path_part(prefix_g, source_id)
                if path_part == source_id[len(prefix_g):]:
                    # this path_part is at end of absolute path, keep definition found in sdef
                    # save original id in _source_id
                    df['_source_id'] = source_id
#                     print "setting source_id, df="
#                     pp.pprint(df)
                else:
                    # this path_part is is not at end of absolute id.
                    # Definition in sdef does not yet apply.  Make empty definition for mstats
                    # qty = '!' if '_qty' not in df else df['_qty']
                    df = {'_source_id': source_id,}
                    type = 'group'
                    # set qty to '?' (optional) so validate_file will not check it
                    # (validate_file checks all ids with absolute path directly).
                    qty = '?'
                id = path_part
                assert id == mid, "add_includes_to_mstats - id (%s) and mid (%s) should match" % (
                    id, mid)
                # ignore if this id overlaps some other since it's a path.  Other parts merged later
                # this testing for aibs_ct extension
                if id in self.mstats.keys():
                    continue
#                 parent_path, basename = self.file.get_name_from_full_path(id)
#                 id = basename
            # quid = "%s:%s" % (ns, id) if ns != self.file.default_ns else id
            # pp.pprint(df)
            # qty = '!'  # assume includes are required
            if id in self.mstats.keys():
                print "%s: Duplicate id (%s) in group, referenced by include" % (self.full_path, id)
#                 import pdb; pdb.set_trace()
                error_exit()
            alt_id = id.rstrip('/') if id.endswith('/') else id+'/'
            if alt_id in self.mstats.keys():
                print "%s: Group and dataset have same name (%s), referenced by include" %(
                    self.full_path, id)
#                 import pdb; pdb.set_trace()
                error_exit()
            # save include information along with other keys in mstats entry
            # these are setup in function "save_include"
            # iinfo = { 'base': inc_info['base'], 'itype': inc_info['source'] }
            self.mstats[id] = { 'ns': ns, 'qty': qty,
                'df': df, 'created': [], 'type': type,
                'source': [source], 'include_info': inc_info } # was shorter: iinfo }
        if subclass_include_count > 1 and not hasattr(self,'scratch_group'):
            # more than one subclass include member in this node, save node for possible
            # cleanup in function file.prune_unused_subclasses
            self.file.subclassed_nodes["include"].append(self)
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
#         print "parent_attributes="
#         pp.pprint (self.parent_attributes)
        print "attributes="
        pp.pprint (self.attributes)
        print "mstats="
        pp.pprint (self.mstats)


    def make_group(self, id, name='', attrs={}, link='', abort=True, attrs_shape=None):
        """ Create a new group inside the current group.
        id - identifier of group
        name - name of group in case name is not specified by id (id is in <angle brackets>)
            *OR* Group node linking to
            *OR* pattern specifying a link: link:path or extlink:file,path
        attrs - attribute values for group that are specified in API call
        link - specified link, of form link:path or extlink:file,path.  Only needed
            if name must be used to specify local name of group
        abort - If group already exists, abort if abort is True, otherwise return previously
            existing group.
        attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
            only used for matlab bridge.
        """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.file.deflatten_attrs(attrs, attrs_shape)         
        gid = id + "/"
        # if this id was part of a subclass_merge, prune the others and possibly change id
        # gid = self.prune_subclass_merges(gid)
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

    def make_custom_group(self, qid, name='', path='', attrs={}, attrs_shape=None):
        """ Creates custom group.
            qid - qualified id of structure or name of group if no matching structure.
                qid is id with optional namespace (e.g. core:<...>).  Path can
                also be specified in id (path and name are combined to produce full path)
            name - name of group in case id specified is in <angle brackets>
            path - specified path of where group should be created.  If not given
                or if relative path.  Only needed if location ambiguous
            attrs - attribute values for group that are specified in API call.
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
        """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.file.deflatten_attrs(attrs, attrs_shape) 
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
            sgd = {'id': id, 'type': type, 'ns':self.mstats[id]['ns'], 'df': self.mstats[id]['df'],}
            # print "found definition for %s in mstats, mstats=" % id
            # pp.pprint(self.mstats)
            return sgd
        msg = []
        msg.append("Attempting to create '%s' (name='%s') inside group:" % (id, name))
        msg.append(self.full_path)
        msg.append("But '%s' is not a member of the structure for the group" % id)
        msg.append("Valid options are: %s" % self.mstats.keys())
        # print "Extra information (for debugging):  Unable to find definition for node %s" % id
        # print "mstats="
        # pp.pprint(self.mstats)
        msg = "\n".join(msg)
        raise SchemaIdError(msg)
        # error_exit()

        
    def set_dataset(self, id, value, name='', attrs={}, dtype=None, compress=False,
        shape=None, attrs_shape=None):
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
            shape - only used when called from matlab.  Specifies shape that 1-d value
                should be converted ot.  (matlab can only pass in 1-d arrays).
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
        """
#         print "called group.set_datset, id=%s" % id
#         print "value=", value
#         print "attrs=", attrs
#         print "dtype=", dtype
#         print "attrs_shape=", attrs_shape
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.file.deflatten_attrs(attrs, attrs_shape)
        if isinstance(value, (array.array, tuple)):
            value = self.file.deflatten(value, shape)
        sgd = self.get_sgd(id, name)
        link_info = self.file.extract_link_info(value, None, Dataset)
        path = self.full_path
        ds = Dataset(self.file, sgd, name, path, attrs, self, value, dtype, compress, link_info)
        # self.mstats[id]['created'].append(ds) 
        return ds 

       
    def set_custom_dataset(self, qid, value, name='', path='', attrs={}, dtype=None, 
        compress=False, shape=None, attrs_shape=None):
        """ Creates custom dataset that is inside the current group.
            qid - qualified id of structure.  id, with optional namespace (e.g. core:<...>).
            name - name of dataset in case name is unspecified (id is in <angle brackets>)
            path - specified path of where dataset should be created if not specified in qid
            attrs - attributes (dictionary of key-values) to assign to dataset
            dtype - if provided, included in call to h5py.create_dataset
            compress - if True, compression provided in call to create_dataset
            shape - only used when called from matlab.  Specifies shape that 1-d value
                should be converted ot.  (matlab can only pass in 1-d arrays).
            attrs_shape - specifies shapes of 1-d attrs values passed in from matlab.  This
                only used for matlab bridge.
            """
        if attrs_shape:
            # convert attribute values passed in by matlab from 1-d to original shape
            self.file.deflatten_attrs(attrs, attrs_shape)
        if isinstance(value, (array.array, tuple)):
            value = self.file.deflatten(value, shape)
        gslash = ""
        parent = self
        sdef, name, path = self.file.get_custom_node_info(qid, gslash, name, path, parent)   
        ds = Dataset(self.file, sdef, name, path, attrs, parent, value, dtype, compress)
        return ds    
