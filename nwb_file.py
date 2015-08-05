import time
import h5gate as g
import nwb_init as ni

def nwb_file(fname, start_time="", ddef={}, dimp=[], default_ns='core', options={}):
	""" Create NWB file.  Returns h5gate File object.
	fname  - name of nwb (hdf5) file to create.
	start_time - session starting time.  If not specified, current time is used.  
	ddef - supplied file format specification
	dimp - Array of data definition files to import.  Can be used to import the
		core definitions and/or extensions.  Has dictionaries of form:
		{'file': <file_name>, 'var': <variable_name> }
		where <file_name> is name of .py file defining the structures and locations,
		and <variable_name> is the variable having the definitions in that file.
	default_ns - default name space for referencing data definition structures
	options - specified options.  See 'validate_options' in h5gate.py
	"""
	if 'schema_id_attr' not in options:
		options['schema_id_attr'] = 'nwb_sid'
	if not ddef and not dimp:
		# no definitions specified, Use nwb_core.py as default
		dimp = ['"nwb_core.py":"nwb"', ]
	# create nwb file
	f = g.File(fname, ddef, dimp, default_ns, options)
	# set initial metadata
	ni.nwb_init(f, fname, start_time)
	return f
