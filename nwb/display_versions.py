import h5py
import sys

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
    python_version = sys.version
    python_executable = sys.executable
    hdf5_api_version = h5py.version.api_version
    hdf5_version = h5py.version.hdf5_version

    print "Versions are:"
    print "Python:", python_version
    print "Python executable:", python_executable
    print "HDF5 API:", hdf5_api_version
    print "HDF5:", hdf5_version
    
def matlab():
    print "\n**** called from MatLab"
    display_versions()
    

if __name__ == "__main__":
    print "\n**** called directly from Python"
    display_versions()
