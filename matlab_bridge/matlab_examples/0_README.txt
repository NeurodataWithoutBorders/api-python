0_README.txt for NWB MatLab examples

Directories are:

create_scripts   - scripts used to create sample NWB files

created_nwb_files  - location of where example NWB files will be created

source_data  - This is initially empty.  To run the script that require
    source data files (crcns_alm_1.m), download file
    "matlab_source_data.tar.gz" from:
    https://portal.nersc.gov/project/crcns/download/nwb-1/example_script_data
    (You can either login with a crcns.org account, or click the checkbox
    and login anonymously to download the file).
    After downloading the file, upack it, and either put the contents into
    the "source_data" directory, or create a symbolic link from the downloaded
    source_data directory to examples/source_data (first remove the
    currently existing directory).  When finished, the "source_data"
    directory should have subdirectory crcns_alm-1

To run the create_scripts, go into the directory (in Matlab) and run
the script by typing the name into the command line.

*** These require that the matlab NWB bridge is setup.  See the instructions
in the 0_INSTALL.txt file in the directory above this one.

