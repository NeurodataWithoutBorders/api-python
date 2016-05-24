0_README.txt for NWB examples


Directories are:

create_scripts   - scripts used to create sample NWB files

created_nwb_files  - location of where example NWB files will be created

utility_scripts  - scripts demonstrating validating files and
    generating documentation.
    
text_output_files - text files created when running create scripts or
    utility scripts.
    

source_data  - This is initially empty.  To run the scripts that require
    source data files, download file "source_data.tar.gz" from:
    https://portal.nersc.gov/project/crcns/download/nwb-1
    then upack it, and either put the contents into the "source_data"
    directory, or create a symbolic link from the downloaded
    source_data directory to examples/source_data (first remove the
    currently existing directory).  When finished, the "source_data"
    directory should have subdirectories:
    crcns_alm-1  crcns_hc-3  crcns_ret-1  crcns_ssc-1

To run the create_scripts, or the utility_scripts, cd into the corresponding
directory and follow the instructions in the readme file in that directory.

