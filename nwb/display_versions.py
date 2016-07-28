import sys
import os

# Function to display Python and hdf5 version from both Python
# and Python called from matlab

# To run by calling Python directly, enter the following command into the
# operating system shell:
# python -m nwb.display_versions

# To run from Matlab enter the following command into the Matlab command window:
# py.nwb.display_versions.matlab()

# The versions displayed by the above two calls should be the same.
# If the output is different, you need to specify the
# correct version of Python to Matlab as described in the
# matlab_bridge 0_INSTALL.txt file.

    

def display_versions():
    print "** environment variables:"
    for key in sorted(os.environ.keys()):
        print key, os.environ[key]
    print "** Versions:"
    print "Python:", sys.version
    print "Python executable:", sys.executable
    try:
        import h5py
    except:
        e = sys.exc_info()[0]
        print "unable to import hd5f:", e
    else:
        print "HDF5 API:", h5py.version.api_version
        print "HDF5:", h5py.version.hdf5_version
    
def matlab():
    print "\n**** called from MatLab"
    display_versions()
    

if __name__ == "__main__":
    print "\n**** called directly from Python"
    display_versions()
