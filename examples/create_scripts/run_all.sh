#!/bin/bash

# This script will run all the example create scripts.
#
# It is run by entering the script name, optionally followed by character "s" or "f".
# "s" specifies text output should be displayed on the screen, "f" indicates the
# text output should be sent to a file, in directory "../text_output_files/create".
# Writing to a file is useful for comparing the text output of each
# create script to the output of validating the created nwb file.
# (The output from both should be mostly the same) and to the output generated
# in other runs.  The output is used by the scripts in the "test_all" directory
# at the top level.
# The 'validate_all.py' script (in directory '../utility_scripts') can be used
# to validate all the NWB files created by these scripts.

txt_output_dir="../text_output_files/create"
nwb_output_dir="../created_nwb_files"

output_mode=$1
if [[ "$output_mode" == "" ]] ; then
    output_mode="f"
fi

if [[ ! "$output_mode" =~ [fs]$ ]] ; then
    echo "format is:"
    echo "$0 <output_mode>"
    echo "where, <output_mode> is one of:"
    echo " f - output to file in $txt_output_dir"
    echo " s - output to screen."
    echo " default is 'f'"
    exit 1
fi
if [[ "$output_mode" == 's' ]] ; then
    dest="screen"
else
    dest="directory $txt_output_dir"
fi

source_data_dir="source_data_2"
source_data_test_file="../$source_data_dir/crcns_alm-1/data_collection.txt"

if [[ -f "$source_data_test_file" ]] ; then
    have_source_data="1"
    source_data_msg="Have ../$source_data_dir directory contents, running scripts that use it."
else
    have_source_data="0"
    source_data_msg="Did not find ./$source_data_dir directory contents.  Skipping scripts that use it."
fi

echo "sending output to $dest"
echo "$source_data_msg"


if [[ "$output_mode" == 'f' ]] ; then
    # make sure text output directory exists and is empty
    if [[ ! -d "$txt_output_dir" ]]; then
        mkdir $txt_output_dir
        echo "created $txt_output_dir"
    else
        rm -f $txt_output_dir/*.txt
        echo "cleared $txt_output_dir"
    fi
fi



function run_script {
   script=$1
   if [[ "$output_mode" == "f" ]] ; then
      stem=${script%.*}
      output_file="$stem.txt"
      echo "doing 'python $script > $txt_output_dir/$output_file'"
      python $script > $txt_output_dir/$output_file
   else
      echo "doing 'python $script'"
      python $script
   fi
}

# these scripts take longer to run and require source data.  Run last.
slow_scripts="crcns_hc-3.py crcns_ret-1.py crcns_ssc-1.py crcns_alm-1.py"
all_scripts=`ls *.py`

# first, run all scripts that do not take a long time
for script in $all_scripts ; do
if [[ $slow_scripts != *"$script"* ]]
then
   run_script $script
fi
done


# check if have source data (for scripts that take longer)

if [[ "$have_source_data" == "0" ]] ; then
    echo $source_data_msg
    exit 0
fi

echo ""
echo "Now running scripts that take longer..."

for script in $slow_scripts ; do
    if [[ "$prompt_for_slow" == "y" ]] ; then
        yes_no "Run $script ?"
        if [[ "$yesno" == "y" ]] ; then
            run_script $script
        fi
    else
        run_script $script
    fi
done

echo "All done."


exit 0
