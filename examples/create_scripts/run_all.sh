#!/bin/bash

txt_output_dir="../text_output_files/create"
echo
echo "         ** Run all create scripts **"
echo
echo "This script will run all the example create scripts."
echo
echo "The text output of running the each script can either be displayed on the screen"
echo "or written to a file (in directory '$txt_output_dir')."
echo "Writing to a file is useful for comparing the text output of each"
echo "create script to the output of validating the created nwb file."
echo "(The output from both should be mostly the same).  Script 'validate_all.py'"
echo "(in directory '../utility_scripts') can be used to validate all the"
echo "NWB files created by these scripts."
echo

function yes_no {
   prompt=$1
   read -p "$prompt"
   while [[ ! "$REPLY" =~ [YyNn]$ ]] ; do
      read -p "please enter 'y' or 'n': "
   done
   if [[ "$REPLY" =~ [Yy]$ ]] ; then
      yesno="y"
   else
      yesno="n"
   fi
}


# echo "txt_output_dir='$txt_output_dir'"
yes_no "Write text output to files (y/n)?: "
write_files=$yesno
# echo "write_files is '$write_files'"

echo
echo "Some scripts take a long time (5+ minutes to run)"
echo "Do you wanted to be prompted before running each of these?"
yes_no "(Enter 'y' to be prompted, 'n' to run them all without prompting): "
prompt_for_slow=$yesno


function run_script {
   script=$1
   echo 
   echo
   echo "running $script"
   if [[ "$write_files" == "y" ]] ; then
      stem=${script%.*}
      output_file="$stem.txt"
      echo "doing 'python $script > $txt_output_dir/$output_file'"
      python $script > $txt_output_dir/$output_file
   else
      echo "doing 'python $script'"
      python $script
   fi
}

# these scripts take longer to run, prompt before running each
slow_scripts="crcns_hc-3.py crcns_ret-1.py crcns_ssc-1.py crcns_alm-1.py"
all_scripts=`ls *.py`

# first, run all scripts that do not take a long time
for script in $all_scripts ; do
if [[ $slow_scripts != *"$script"* ]]
then
   run_script $script
fi
done

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
