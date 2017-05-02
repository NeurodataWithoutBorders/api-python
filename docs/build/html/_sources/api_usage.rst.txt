Python (and Matlab) API for Neurodata Without Borders (NWB) format
==================================================================

:Revision: 0.8.2
:Date: May 1, 2017 [1]_


Overview
--------

The Python API for the NWB format is a write API that can be used to
create NWB files (it does not provide functionality for reading).
The API provides a small set of generic functions for storing data in the file
(that is, creating HDF5 groups and datasets).    It is
implemented using a software that is domain-independent.
The specialization of the API to
create NWB files is achieved by having the format defined
using a :ref:`specification language <h5gate_format_specification_language>`.
The system provides the following features:

* Write API for both Python and Matlab.

* The format is extensible in a formal way that enables validation and sharing
  extensions.
  
* Documentation for the format and extensions can be automatically generated.

More details of these features are given in the
:ref:`specification language documentation <h5gate_format_specification_language>`.


.. [1] The reversion number is for this document and is independent of
   the version number for the NWB format. The date is the last
   modification date of this document.
   
Installation
------------

Installing using system Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The API works with both Python 2 and Python 3.


To get the source code for installation, do::

    git clone https://github.com/NeurodataWithoutBorders/api-python nwb_api-python


The last parameter is optional.  Providing it, will cause the software to be stored in a
directory named "nwb_api-python" rather than 'api-python'.


After you get the latest software, install it using::

    python setup.py install
    

Then, in the future, (to incorporate any further updates), issue the command::

    git pull origin

then re-run ``python setup.py install`` to install the updates.

Note: If there is a previous version installed, to ensure that the new version is used,
remove the previous version.  This can be done by finding the location the previous
version was installed in, then removing it.  The location the previous version was
installed in can be found by printing nwb.__path__ from inside a python shell that is
started in a directory other than that containing the NWB API source code.  The commands
look like the following:

.. code-block:: python

    >>> import nwb
    >>> print(nwb.__path__)
    ['/Path/to/site-packages/nwb']
    >>> quit()
    rm -rf /Path/to/site-packages/nwb*
    

After installing, try running the ``test_all.sh`` script in the ``test_all`` directory to
test the installation.  See file ``0_README.txt`` in that directory for instructions.


Installing using conda
^^^^^^^^^^^^^^^^^^^^^^

The NWB API depends on HDF5 (accessed via the h5py library) and with the
default install will use whatever version is installed on your system.
You can install it within a [conda] environment to keep it isolated from
other software, for instance if you wish to use a different version of HDF5,
or not have h5py installed globally.

Once you have [installed conda], you can use the following commands to set
up an environment for NWB::

    conda create -n nwb python=3.6 h5py  # or python=2.7
    # Activate the conda environment with one of the following two lines
    source activate nwb # Linux, Mac OS
    activate nwb        # Windows
    # Build & install the API within the environment
    cd nwb_api-python
    pip install -e .


With this approach (in particular the ``-e`` flag) updates to the API obtained
with ``git pull`` will automatically be reflected in the version installed in
the environment.  Information is at:

:[conda]: http://conda.pydata.org/docs/get-started.html
:[installed conda]: http://conda.pydata.org/docs/install/quick.html



API usage overview
------------------

The API for both Python and Matlab provides two main
functions: "make_group" and "set_dataset."  These 
are respectively used to create a HDF5 group and dataset.  Both functions
allow specifying attribute key-value pairs which are stored in the created
group or dataset.  The process of creating an NWB file using the API is
to sequentially make the calls to these functions in order to hierarchically
create the file.

While conceptually very simple, there are variants of the "make_group"
and "set_dataset" functions that have slightly different parameters
depending on whether the group or dataset is created at the top-level
of the HDF5 file, and whether the group or dataset are "custom,"
that is, not part of the core format or an extension defined by the
specification language.  These variants and also other functions that are
part of the API are described after the "Examples and utilities" section below.


Examples and utilities
----------------------


Example scripts for creating NWB files and running utilities are in the
following directories::

    examples/create_scripts       # Python example create scripts in Python
    unittest                      # Python unittests
    matlab_bridge/matlab_examples # Matlab example create scripts
    matlab_bridge/matlab_unittest # Matlab unittests
    examples/utility_scripts      # Examples for running various NWB utilities
    
The utilities included with the software (and usage) are shown below.


Validate an NWB file
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  python -m nwb.validate filename.nwb

See the ``validate_all.sh`` script in ``examples/utility_scripts`` for specific examples.


Generate documentation for the NWB format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # for the core NWB format
    python -m nwb.make_doc > doc.html
    
    # for the core NWB format and an extension
    python -m nwb.make_doc extension.py > doc.html
    
    # from an NWB file (uses specifications stored in the file)
    python -m nwb.make_doc filename.nwb > doc.html
    

See ``make_docs.py`` in ``examples/utility_scrips`` for specific examples.


Compare two HDF5 files displaying differences in detail
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  # find all differences
  python -m nwb.h5diffsig file1.nwb file2.nwb > diff.txt
  
  # find all differences except those that normally change between NWB files
  python -m nwb.h5diffsig file1.nwb file2.nwb -Na > diff.txt

The "N" option filters out components in the
file that could change (such as dataset ``file_create_date``) even if
the NWB file contents are the same.  The "a" option sorts the contents
by location (path) rather than by size.  Documentation of the
options are displayed by running the script with no parameters.


Generate a 'signature file' for a HDF5 file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # generate full signature
    python -m nwb.h5diffsig filename.nwb > filename_sig.txt
    
    # generate signature, filtering out parts that normally change
    python -m nwb.h5diffsig filename.nwb -Na > > filename_sig.txt
  
A 'signature file' is a text file that can be used for comparison
to check if two files match.  (The .nwb extension is used for NWB files,
which are in hdf5 format.)  The "N" and "a" options are as described
previously.

.. _initializing_the_api:

Initializing the API
--------------------

To create an NWB file using the API, the following imports are required:

.. code-block:: python

    from nwb import nwb_file
    from nwb import nwb_utils as utils


Function ``nwb_file.open`` is used to create or open an NWB file.  It has the
following signature:

.. code-block:: python

    def open(file_name, start_time=None, mode="w-", identifier=None,
        description=None, core_spec="nwb_core.py", extensions=[],
        default_ns="core", keep_original=False, auto_compress=True):
        
Parameters are:

        **file_name** - Name of file to create or open.  Text. Required.

        **start_time** - Starting time for the experiment.  Is used only if writing
        a file (mode=``w``).  If not specified, the current time is used.

        **mode** - Mode of file access.  One of:
            :``r``:  Readonly, file must exist.  (currently only used for validation).
            :``r+``: Read/write, file must exist.
            :``w``:  Create file, replacing if exists. (Default)
            :``w-``: Create file, fail if exists.
            :``a``:  Read/write if exists, create otherwise.

        **identifier** - Unique identifier for the file.  Required if ``w`` mode.  Not
        used otherwise.

        **description** - A one or two sentence description of the experiment and what
        the data inside represents.  Required if ``w`` mode.  Not used otherwise.

        **core_spec** - Name of file containing core specification of NWB format.
        If a dash (``-``), load specification from NWB file (used when opening an existing
        file).

        **extensions** - List of files containing extensions to the format that may
        be used.  Empty list if no extensions or if extension specifications should be
        loaded from NWB file.

        **default_ns** - Namespace (also called **Schema-Id**) of specification to use
        as default if no namespace specified when creating groups or datasets.  Normally,
        the default value ("core") should be used, since that is the namespace used in
        the default core_spec (file ``nwb_core.py``)

        **keep_original** - If True and mode is ``w`` or ``r+`` or ``a`` (modes that can change
        and exiting file), a backup copy of any original file will be saved with the name
        "<filename>.prev".

        **auto_compress** - If True, data is compressed automatically through the API.
        Otherwise, the data is not automatically compressed.

An example of calling nwb_file.open is given below:

.. code-block:: python

    from nwb import nwb_file
    from nwb import nwb_utils as utils

    settings = {}
    settings["file_name"] = "filename.nwb"
    settings["identifier"] = utils.create_identifier("some string; will be added to unique identifier")
    settings["mode"] = "w"
    settings["start_time"] = "2016-04-07T03:16:03.604121Z"
    settings["description"] = "Description of the file"

    # specify an extension (Could be more than one).
    settings['extensions'] = ["extension_foo.py"]
    f = nwb_file.open(**settings)


The call to function ``nwb_file.open`` returns a “h5gate File” object.  This is a Python object
that controls the creation of an hdf5 file using the format specified by the specification
language files (for the core nwb format and any extensions).  The "extensions" parameter
allows specifying extensions to the core format specification.  The use of extensions is
described in Section :numref:`using_extensions`.


Referencing groups and datasets
-------------------------------

The NWB Python API works by allowing the user to sequentially create hdf5 groups and
datasets that conform to the specification of the format.  To reference a group or dataset
in a call to the API, the name of the group or dataset as given in the file format
specification is used.  Some groups and datasets have a name which is variable, that is,
which is specified in the call to the API rather than in the format specification. 
(For example, group “electrode_X” in the general/intracellular_ephys group.)  In the
API calls, groups or datasets that have a variable name are referenced by enclosing the
identifier associated with them in angle brackets, e.g. ``<electrode_X>``.  Another
example are NWB “Modules” which are stored in hdf5 groups.  To create a module, a call 
to make_group is used, e.g. ``f.make_group("<module>", "shank-1")``.

h5gate File and Group objects
-----------------------------

The call to function nwb_file.nwb_file returns a “h5gate File” object (stored in variable
“f” in the above example).  Methods of this object are used to create groups and datasets
in the HDF5 file that are, figuratively speaking, at the “top-level” of the file format 
specification, that is, not located inside groups that are defined in the specification 
language.  Calls to the API functions which creates groups, return an “h5gate Group” object.
This object has methods that are used to create groups and datasets within the associated
HDF5 group.  There is also a method (``set_attrs``) which can be used set attributes associated
with groups or datasets.

The methods of the h5gate File and Group objects and the ``set_attrs`` function are described
in the following sections.


h5gate File object methods
--------------------------

The h5gate File object has the following methods (functions):
    1. make_group
    2. make_custom_group
    3. set_dataset
    4. set_custom_dataset
    5. get_node
    6. close

h5gate File make_group
^^^^^^^^^^^^^^^^^^^^^^

Method ``make_group`` of object h5gate File creates a group in the hdf5 file.  It has the
following signature::

    g = f.make_group(qid, name, path, attrs, link, abort)

``f`` signifies an h5gate File object.  The returned object, stored in variable ‘g’ in
the above, is a “h5gate Group” object—which is described in the Section
:numref:`h5gate_group_object`.  In the make_group function, only the first argument (qid)
is always required.  The second two arguments (name and path) are sometimes required.
All arguments are described below:
 
``qid`` is the “qualified id” for the group.  The qualified id is the name used to
reference the group (with surrounding angle brackets if the name is variable).  The
id may optionally prefixed with a Schema-Id or "namespace."  The Schema-Id provides a
way to associate extensions to the format with an identifier, in a manner similar to
how namespaces are used in XML.  This is described in Section :numref:`using_extensions`).

``name`` is only used if the group name is variable (referenced using <angle brackets>).
It contains the name to be used when creating the group.

``path`` specifies the path to the parent group within the HDF5 file.  It is only needed
if the location of the group within the file is ambiguous.  For many groups, the location
is not ambiguous and for those groups, the location is automatically determined by the API,
without requiring a specification by argument “path”.

``attrs`` is a Python dictionary containing hdf5 attributes keys and values to assign to
the created group.  It is optional.

``link`` is used to create a hdf5 link to an existing group.  If present it contains
either a previously created h5gate Group object, or a string of the form
“link:/path/to/group” or a string of the form: “extlink:path/to/file, path/to/group”.
The first two are used to make a HDF5 link to a group within the current file.  The third
method specifies a link to a group in an external HDF5 file.

``abort`` is a logical variable, default is True.  It controls the program behavior if
the group being created already exists.  If ``abort`` is True the program will abort.
If False, the function will return the previously existing group (h5gate Group object).

h5gate File make_custom_group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Method ``make_custom_group`` of object h5gate File creates a custom group in the hdf5 file
(that is, a group that is not part of the core format specification or an extension).  This
method is provided because method “make_group” can only be used to create groups that are
specified in the file format or an extension.  The function signature for
``make_custom_group`` is::

    g = f.make_custom_group(qid, name, path, attrs)

Return type and parameters are the same as for h5gate File method ``make_group``.  If
parameter ``path`` is not specified or is a relative path, then the custom group will be
created in the default custom location, which is inside group ``/general``.


h5gate File set_dataset
^^^^^^^^^^^^^^^^^^^^^^^

Method “set_dataset” of object h5gate File is used to create and store data in an HDF5
dataset.  It has the following signature::

    d = f.set_dataset(qid, value, name, path, attrs, dtype, compress)

The return value is an object of type h5gate Dataset.  The arguments are described below:

``qid`` - the “qualified id” for the dataset.  The qualified id is the name used to
reference the dataset (with surrounding angle brackets if the name is variable)
optionally prefixed with a “namespace” as described in the qid parameter for method make_group.

``value`` - value to store in the dataset.  To store numeric or string values in the dataset
(what is normally done) the value can be a scalar, Python list or tuple, or a Numpy array.
To have the created dataset be a link to another Dataset, the value is set to an h5gate
Dataset object or a string matching the pattern: "link:/path/to/dataset" (to link to a
dataset within the file) or “extlink:path/to/file, /path/to/dataset” to link to a dataset
in an external file.

``name`` - name of the dataset in case the name is unspecified (qid is in <angle brackets>).

``path`` - specified path of where to create the dataset (path to parent group).  Only
needed if the location of where to create the dataset is ambiguous in the format
specification.

``attrs`` - a dictionary containing hdf5 attributes keys and values to assign to the
created group.  It is optional.

``dtype`` type of data.  If provided, this is included in the call to the library routine
which creates the dataset (h5py.create_dataset).

``compress`` - if True, compression is specified in the call to the library routine which
creates the dataset (h5py.create_dataset).  The default value is False.  It is recommended
that this be set True when saving large datasets in order to reduce the size of the
generated file.
  
h5gate File set_custom_dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Method “set_custom_dataset” of object h5gate File creates a custom dataset in the hdf5 file
(that is, a dataset that is not part of the format specification).  The function signature
is:

.. code-block:: python

    d = f.set_custom_dataset(qid, value, name, path, attrs, dtype, compress)

Return type and parameters are the same as for method ``set_dataset``.

  
h5gate File get_node
^^^^^^^^^^^^^^^^^^^^

Method ``get_node`` returns the h5gate Group or Dataset object located at the specified
location (full path in the hdf5 file).  It has the following signature:

.. code-block:: python

    n = f.get_node(full_path, abort)

Arguments are:

**full_path** – absolute path to group or dataset.

**abort** – A logical value that specifies what to do if there is no node (group or
dataset) at the specified path.  Default is True, which causes the program to abort.
A value of False, causes the function to return None.


h5gate File close
^^^^^^^^^^^^^^^^^

Method ``close`` of object h5gate File is used to close the created file.  It must be
called to complete the creation of the file.  Function signature is:

.. code-block:: python

    f.close()

There are no arguments.

.. _h5gate_group_object:

h5gate Group object
--------------------

An h5gate Group object is returned by h5gate File methods ``make_group`` and
``make_custom_group``.  It is associated with a HDF5 group created in the NWB file.
The h5gate Group object has the following methods:

    1. make_group
    2. make_custom_group
    3. set_dataset
    4. set_custom_dataset
    5. set_attr
    6. get_node

The name of the first four of these methods are the same as the name of methods of
the h5gate File object. The difference between the File and Group object methods is that
the h5gate File methods are used to create groups and datasets that are not inside groups
that are defined as part of the format specification whereas the Group methods are used
to create groups and datasets inside the current group, that is, inside the Group object
used to call the methods.  The h5gate Group methods are described below:

h5gate Group make_group
^^^^^^^^^^^^^^^^^^^^^^^

Method ``make_group`` of object h5gate Group creates a group inside the current group.
It has the following signature:

.. code-block:: python

    g = pg.make_group(qid, name, attrs, link, abort)

In the above line, ``pg`` signifies a parent group, (object of type h5gate Group).
The returned object, stored in variable ``g`` in the above, is also an “h5gate Group” object.
Parameters in the function have the same meaning as those in function h5gate
File make_group.  There is no “path” parameter (which was in the File object make_group)
because the location of the created group is always known.  (The created group will be
located inside the parent group used to invoke the method).

h5gate Group make_custom_group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Method ``make_custom_group`` of object h5gate Group creates a custom group, usually within
the parent group.  The function signature for ``make_custom_group`` is:

.. code-block:: python

    g = pg.make_custom_group(qid, name, path, attrs)

Return type and parameters are the same as for h5gate Group method ``make_group``.  If path
is not specified or is a relative path, the group will be created inside the parent group.
If path is an absolute path, the group will be created at the specified location which
can be anywhere in the hdf5 file.

h5gate Group set_dataset
^^^^^^^^^^^^^^^^^^^^^^^^

Method ``set_dataset`` of object h5gate Group is used to create a dataset within the parent
group.  It has the following signature:

.. code-block:: python

    d = pg.set_dataset(qid, value, name, attrs, dtype, compress)


The return value is an object of type h5gate Dataset.  The parameters have the same
meaning as those in function h5gate File set_dataset.  There is no “path” parameter because
the created dataset is always located inside the parent group used to invoke the method.


h5gate Group set_custom_dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Method set_custom_dataset of object h5gate Group is used to create a custom dataset,
usually within the parent group.  It has the following signature:

.. code-block:: python

    d = pg.set_custom_dataset(qid, value, name, path, attrs, dtype, compress)


The return value is an object of type h5gate Dataset.  The parameters have the same
meaning as those in function h5gate Group set_dataset.  If path is not specified or is
a relative path, the group will be created inside the parent group.  If path is an
absolute path, the group will be created at the specified location.


set_attr method
^^^^^^^^^^^^^^^

Both the h5gate Group and h5gate Dataset objects have a method ``set_attr`` which is used
to set the value of an hdf5 attribute of the group or dataset.  It has the following
signature:

.. code-block:: python

   n.set_attr(aid, value, custom)

In the above, “n” is an h5gate Node object (which is a h5gate Group or Dataset).

Parameters are:

    **aid**    – attribute id (name of the attribute).
    
    **value**  – value to store in the attribute.

    **custom** – a logical value (default False) which indicates whether or not the
                 attribute is a custom attribute (that is, not part of the file format
                 specification).  Setting a value of “True” when setting a custom attribute
                 prevents a warning message from being displayed for the attribute when
                 closing the file.


h5gate Group get_node method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a shorthand wrapper for the ``File.get_node`` method for accessing Groups or Datasets
within the current Group.  It has the following signature:

.. code-block:: python

   n = g.get_node(path, abort)

In the above ``g`` is an h5gate Group object.  Parameters are as for ``File.get_node`` except
that the `path` may be a relative path, in which case it is resolved relative to ``g``.


nwb_utils.py functions
----------------------

File nwb_utils.py provides the following utility functions that are useful when using
the API.  The function signatures and doc strings are given below.

.. code-block:: python

    def load_file(filename):
        """ Load content of a file.  Useful for setting metadata to 
        content of a text file"""

    def add_epoch_ts(e, start_time, stop_time, name, ts):
        """ Add timeseries_X group to nwb epoch.
            e - h5gate.Group containing epoch
        start_time - start time of epoch
        stop_time - stop time of epoch
        name - name of <timeseries> group to be added to epoch
        ts - timeseries to be added, either h5gate.Group object or
           path to timeseries """


    def add_roi_mask_pixels(seg_iface, image_plane, name, desc, pixel_list, weights, width, height, start_time=0):
        """ Adds an ROI to the module, with the ROI defined using a list of pixels.
            Args:
                *image_plane* (text) name of imaging plane
                *name* (text) name of ROI
                *desc* (text) description of RO
                *pixel_list* (2D int array) array of [x,y] pixel values
                *weights* (float array) array of pixel weights
                *width* (int) width of reference image, in pixels
                *height* (int) height of reference image, in pixels
                *start_time* (double) <ignore for now>
            Returns:
                *nothing*
        """

    def add_roi_mask_img(seg_iface, image_plane, name, desc, img, start_time=0):
        """ Adds an ROI to the module, with the ROI defined within a 2D image.
            Args:
                *seg_iface* (h5gate Group object) ImageSegmentation folder
                *image_plane* (text) name of imaging plane
                *name* (text) name of ROI
                *desc* (text) description of ROI
                *img* (2D float array) description of ROI in a pixel map (float[y][x])
                *start_time* <ignore for now>
            Returns:
                *nothing*
        """

    def add_reference_image(seg_iface, plane, name, img):
        """ Add a reference image to the segmentation interface
            Args: 
                *seg_iface*  Group folder having the segmentation interface
                *plane* (text) name of imaging plane
                *name* (text) name of reference image
                *img* (byte array) raw pixel map of image, 8-bit grayscale
            Returns:
                *nothing*
        """

Example API calls
-----------------

To create an NWB file using the Python API, each component in the file (hdf5 group or
dataset) must be created using a call to either ``make_group`` or ``set_dataset``.
For a given API call, the main decisions to be made are:

    1. Whether or not to use the h5gate File object methods (e.g. “f.make_group”,
       “f.set_dataset”) or the methods associated with a previously created group
       (e.g. “g.make_group” or “g.set_dataset”).
       
    2. What name to specify if the group or dataset has a variable name.
    
    3. Whether or not a path must be specified for the parent group or dataset.
    
    4. The group or dataset to create based on the NWB File format specification and
       the data to be stored in the file.

Some examples of calls made for the different types of data stored in NWB files are given
below (for the Python API).  For most complete and recent examples, see the scripts in
``examples/create_scripts``.  Matlab examples are in ``matlab_bridge/matlab_unittest`` and
``matlab_bridge/matlab_examples``.


Setting metadata in the top-level general group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For metadata that is in the top level of group ``/general``, a call to the h5gate File object
is used.  Examples are:

.. code-block:: python

    f.set_dataset("lab", "content to be stored...")
    f.set_dataset("surgery", "content to be stored...")

For metadata that is in inside a subgroup of general, first a call to the h5gate File
object is used to create the subgroup, then calls are made using the subgroup to create
and store the data inside it.  Examples are:

**Subject metadata** – (inside group ``/general/subject``)

.. code-block:: python

    g = f.make_group("subject")
    g.set_dataset("subject_id", "content to be stored...")
    g.set_dataset("species", "content to be stored...")

**Extracellular ephys metadata** – (inside group ``/general/extracellular_ephys``)

.. code-block:: python

    g = f.make_group("extracellular_ephys")
    g.set_dataset("electrode_group", "content to be stored...")

**Extracellular ephys electrode group metadata**

.. code-block:: python

    # create subgroup using the group “g” made by the previous call
    g2 = g.make_group("<electrode_group_N>", "name of electrode group...")

    # set dataset inside subgropu
    g2.set_dataset("description", "content to be stored...")

Creating Modules and interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NWB “Modules” (which are stored as hdf5 groups inside the ``/processing`` group) are
created using the following call:

.. code-block:: python

    gm = f.make_group("<module>", "name of module.")

Once a module is created, NWB interfaces (which are groups inside a module) are created
by calling “make_group” using the group associated with the module.  Examples:

.. code-block:: python

    gi = gm.make_group("Clustering")

In the above call, the ``Clustering`` interface is created inside of the module created in
the previous call.  Storing data inside the interface is done by calling the methods of
the group associated with the interface.  For example, the Clustering interface contains
a dataset named ``times``.  Data would be saved to it using:

.. code-block:: python

    gi.set_dataset("times", data_to_be_stored)

In the above call, ``data_to_be_stored`` would be a list, tuple, or numpy array
containing the data to be stored.


Storing TimeSeries data
^^^^^^^^^^^^^^^^^^^^^^^

NWB time series are stored by first creating a group that specifies the type of
TimeSeries being stored than using methods of that group to store the associated data.
All time series groups have a variable name (that is, the name is specified by in the API
call).  If the TimeSeries being created is not inside a previously created h5gate Group,
then the h5gate File object must be used to create the TimeSeries.  Otherwise, the parent
h5gate Group object is used.  Some examples are below.

**Storing TimeSeries** (in ``/acquisition/timeseries``)

.. code-block:: python

    ts = f.make_group("<TimeSeries>", "name of TimeSeries group",
       path="/acquisition/timeseries", attrs= {"source": "..."})
    ts.set_dataset("data", data_to_be_stored,
       attrs={"unit": "unit used"}, compress=True )
    ts.set_dataset("timestamps", times, compress=True)
    ts.set_dataset("num_samples", len(times))

In the above, times is a list, tuple or numpy array having the data to be stored in the
timestamps array.  Argument ``compress`` is set to true to save space.

**Storing TimeSeries type ImageSeries** (in ``/stimulus/timeseries``)

.. code-block:: python

    ts = f.make_group("<ImageSeries>", "name of group",
       path="/stimulus/timeseries", attrs= {"source": "..."})
    # calls below are the same as in the previous example
    ts.set_dataset("data", data_to_be_stored,
       attrs={"unit": "unit used"}, compress=True )
    ts.set_dataset("timestamps", times, compress=True)
    ts.set_dataset("num_samples", len(times))

**Storing a TimeSeries type in an Interface**

Many interfaces include as a member one or more TimeSeries types.  Modules and interfaces
are stored using the following hierarchical layout::

    /processing/<module>/interface/interface-contents

To store a TimeSeries inside an interface,the group associated with the interface is used
to create the TimeSeries group.  An example:

.. code-block:: python

    # create the module
    gm = f.make_group("<module>", "name of module.")

    # create the interface
    gi = gm.make_group("DfOverF")

    # create the TimeSeries group using the interface group
    ts = gi.make_group("<RoiResponseSeries>", "name of TimeSeries group")

    # set the TimeSeries datasets using the time series group
    ts.set_dataset("data", data_to_be_stored,
       attrs={"unit": "unit used"}, compress=True )
    ts.set_dataset("timestamps", times, compress=True)
    ts.set_dataset("num_samples", len(times))


Storing epochs
^^^^^^^^^^^^^^

To store epochs, first create the top-level epoch group:

.. code-block:: python

    fe = f.make_group("epochs")

Then create each epoch inside the top-level epoch group:

.. code-block:: python

    e = fe.make_group("<epoch_X>", epoch_name)
    e.set_dataset('description', description)
    e.set_dataset('start_time', start_time)
    e.set_dataset('stop_time', stop_time)
    e.set_dataset('tags', tags)

To add time (“timeseries_X”) to the epoch, use the nwb_utility routine “add_epoch_ts”:

.. code-block:: python

    ut.add_epoch_ts(e, start_time, stop_time, "pole_in", tsg)

In the above “tsg” specifies a previously created time series to add to the epoch.  It can
either be an h5gate Group object, or a string specifying the hdf5 path to a previously
created time series.


.. _using_extensions:

Using extensions
----------------

Overview of extensions
^^^^^^^^^^^^^^^^^^^^^^

This API for the NWB format is implemented using software that is domain-independent,
that is, the API software does not encode any part of the NWB format.  Instead,
as described previously, the API implements general functions (``make_group``, ``set_dataset``)
which can be used to create files of multiple formats.

Thus, the API is like a tabula rasa, independent of any particular data format.  The
specialization of the API to create files of a particular format, such as NWB, is
achieved by providing the API with a specification of the format, written in the
:ref:`specification language <h5gate_format_specification_language>`.  For the NWB format,
this specification is in file ``nwb_core.py``.  It defines the "core" NWB format.

Because of the wide variety of requirements for storing Neuroscience data and metadata,
there will often be instances in which data and metadata that are not described by the
core format will need to be stored in NWB files.  To enable this, *extensions* to
the core format can be created.

Extensions are specifications for data that are written in the same language used to
define the core format but which specify the format for data not described
by the core format.  Extensions are "merged" into the specification of the core format
when the API is initialized.  (This is described in Section :numref:`extensions`).

Once the API is initialized with extensions, the data structures defined by the extensions
can be used in the same manner as the structures defined by the core format.  Both the
core format and extensions are written in a JSON-like syntax (Python dictionary).
Extensions are human- and machine-readable, can be easily shared, and, in addition to
being used by the API to create files, they can also be used to validate files and
generate documentation.

Probably, the best way to learn about extensions (after reading the information here)
is to read through the documentation about the
:ref:`specification language <h5gate_format_specification_language>`) and
look at the example scripts that use extensions (files that end with ``-e.py`` in
directory ``examples/create_scripts``) and the extensions (files that start with
``e-``, in directory ``examples/create_scripts/extensions``).


Creating extensions
^^^^^^^^^^^^^^^^^^^

Extensions are Python files that contain a Python dictionary of a particular form.
They can created using any text editor.  An example is below (from file
``e-analysis.py`` in ``examples/create_scripts\extensions``):


.. code-block:: json

 {"fs": {"aibs_ct_an": {


 "info": {
    "name": "AIBS cell types - analysis",
    "version": "0.9.2",
    "date": "May 6, 2016",
    "author": "Jeff Teeters, based on Allen Institute cell types DB",
    "contact": "jteeters@berkeley.edu",
    "description": "NWB extension for AIBS cell types database NWB."
 },

 "schema": {
    "/analysis/": {
        "aibs_spike_times/": {
        "description": "Group for storing AIBS specific spike times",
            "attributes": {
                "comments": {
                    "data_type": "text",
                    "value": "Spike times are relative to sweep start"}
            },
            "<aibs_sweep>": {
                "attributes": {
                    "comments": {
                        "data_type": "text",
                        "value": "Spike times are relative to sweep start"}
                },
                "description": "Times associated with a single sweep",
                "dimensions": ["numSamples"],
                "data_type": "float64!"
            }
        }
    }
 }

 }}}

The first line, ``{"fs": {"aibs_ct_an": {`` specifies the "namespace" or "Schema-Id" for
the extension.  It's an identifier which is associated with the extension.

The ``info`` section provides information about the extension.

The ``schema`` section specifies the schema for the extension, that is the groups.
datasets and attributes that make up the extension.  This is the main part of the extension.
It is written in the :ref:`specification language <h5gate_format_specification_language>`).
(See documentation in that section).

Initializing the API with extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use extensions to create an NWB file, the path to the extension file(s) must be passed
into the call to ``nwb_file.open`` using the **extensions** parameter described in
Section :numref:`initializing_the_api`.  An example call (from file
``examples/create_scripts/analysis-e.py`` is given below for the above
extension, which is in file ``extensions/e-analysis.py``.

.. code-block:: python

    # create a new NWB file
    settings = {}
    settings["file_name"] = OUTPUT_DIR + file_name
    settings["identifier"] = ut.create_identifier("example /analysis group using extension.")
    settings["mode"] = "w"
    settings["start_time"] = "Sat Jul 04 2015 3:14:16"
    settings["description"] = ("Test file demonstrating storing data in the /analysis group "
        "that is defined by an extension.")

    # specify the extension (Could be more than one.  Only one used now).
    settings['extensions'] = ["extensions/e-analysis.py"]

    # create the NWB file object. this manages the file
    print("Creating " + settings["file_name"])
    f = nwb_file.open(**settings)

Referencing extensions
^^^^^^^^^^^^^^^^^^^^^^

Once extensions the API has been initialized with one or more extensions, the
structures defined in the extension can be referenced in the same manner as those
defined in the core format.  In the calls to ``make_group`` or ``set_dataset``
the Id associated with structures (in the core format or an extension) may be
prefixed with the Schema-Id (or namespace) within which the structure was specified.
This may be useful to better document in the code that an Id is associated with an
extension and not the core format.

Examples of referencing structures defined in an extension is given below (from file
``examples/create_scripts/analysis-e.py``).  It creates creates a group and
datasets that are defined by the extension given above.

.. code-block:: python
    
    # This example, stores spike times for multiple sweeps
    # Create the group for the spike times
    # The group ("aibs_spike_times") is defined in the extension
    # f is the h5gate File object returned by nwb_file.open
    ast = f.make_group("aibs_spike_times")

    # above could also have been:
    # ast = f.make_group("aibs_ct_an:aibs_spike_times")
    

    # some sample data
    times = [1.1, 1.2, 1.3, 1.4, 1.5]

    # create some sample sweeps
    for i in range(5):
        sweep_name = "sweep_%03i" % (i+1)
        ast.set_dataset("<aibs_sweep>", times, name=sweep_name)
    

    # all done; close the file
    f.close()


Using the Matlab API
--------------------

The Matlab API is implemented using Matlab functions which allow calling the
Python API from Matlab.  These functions are included in directory
``matlab_bridge/matlab_bridge_api``.  The functions are direct replacements for
all of the Python API functions described in the sections above.  The only difference
is that when calling the Matlab versions, Matlab-style function calls must be
made.  That is, instead of using named parameters in which parameter name = value
(which is done in Python calls), calls with named parameters use a Matlab
Cell Array, with the parameter names alternating with the value for the
parameter.  Example Matlab calls corresponding to the Python code given in the
two sections above is below.  Note, the extension files do not change regardless
of whether the Python or Matlab API is used.  This is because the Python API also
handles the calls made from Matlab.


Matlab code (from file ``matlab_bridge/create_scripts/analysis_e.m``):

.. code-block:: matlab

    % create a new NWB file
    settings = { ...
        'file_name', nwb_file_path, ...
        'identifier', ...
            char(py.nwb.nwb_utils.create_identifier('abstract-feature example')), ...
        'mode', 'w', ...
        'start_time', 'Sat Jul 04 2015 3:14:16', ...
        'description',['Test file demonstrating storing data in the /analysis' ...
            ' group that is defined by an extension.'] ...
        'extensions', {'../../../examples/create_scripts/extensions/e-analysis.py'} ...
        };

    f = nwb_file(settings{:});

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % This example, stores spike times for multiple sweeps
    % create the group for the spike times
    % The group ("aibs_spike_times") is defined in the extension

    ast = f.make_group('aibs_spike_times');

    % some sample data
    times = [1.1, 1.2, 1.3, 1.4, 1.5];

    % create some sample sweeps
    for i = 1:5
        sweep_name = sprintf('sweep_%03i', i);
        ast.set_dataset('<aibs_sweep>', times, 'name', sweep_name);
    end

