0_README.txt for NWB examples


Directories are:

create_scripts   - scripts used to create sample NWB files

created_nwb_files  - location of where example NWB files will be created

utility_scripts  - scripts demonstrating validating files and
    generating documentation.

text_output_files - text files created when running create scripts or
    utility scripts.

source_data_2  - This is initially absent.  When added, it contains
    source data that is needed to run scripts that have prefix "crcns_".
    The "sourc_data_2" directory can be installed by
    running "get_source_data.py" in the utility_scripts directory.
    To install manually, download file "source_data_2.tar.gz" from:
    https://portal.nersc.gov/project/crcns/download/nwb-1
    then upack it, and put it in this directory.
    After adding it, the "source_data_2" directory should have subdirectories:
    crcns_alm-1  crcns_hc-3  crcns_ret-1  crcns_ssc-1

To run the create_scripts, or the utility_scripts, cd into the corresponding
directory and follow the instructions in the readme file in that directory.

