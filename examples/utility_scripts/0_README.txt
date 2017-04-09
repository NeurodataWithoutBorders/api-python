Directory examples/utility_scripts

Contains:

h5diffci.sh  - Demonstrates using h5diffci.py utility which displays difference between HDF5 files.

make_cv_diff.sh - Makes diff of output of create and validate scripts.  
                  Useful to make sure they mostly match.  If not there might be an error in software.

make_docs.sh   - Demonstrate making documentation.  (Old version, does not generate docs
                 for all extension examples).

make_docs.py   - Demonstrate making documentation.  (New version).  To run: python make_docs.py

validate_all.py  -  Validates all NWB files created by create scripts.  To run: python validate_all.py

validate_internal.sh  - Demo of validating file using internally stored format specifications.

check_schemas.sh  - Validate schema files (nwb_core.py and example extensions).

cmp_created.sh  - compare (diff) nwb files with the same names in two different directories, save
                  output in third directory.

install_source_data.py  - download and install example/source_data_2 directory (which is needed
                 to run some of the ../create_scripts

make_h5sig.py  - generate 'h5sig' (hdf5 signature) of nwb files that are in a directory, storing the
                generated signatures in an output directory.

validate_others.sh - validates all nwb files in a directory, saving validation outout in an output
                     directory.

