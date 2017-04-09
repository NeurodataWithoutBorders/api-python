# script to create output of tests run on current setup.
# output is stored in directory "curr"


cwd=`pwd`

# clear previous curr directory
rm -rf curr
mkdir -p curr/unittest

# send any error output to crash_log.txt
logFile="curr/log.txt"

# Directory for nwb test files (optional).  If present, and if there are nwb files
# inside, they are used for additional consistency tests (validation and signatures).
# Otherwise this is ignored.
nwb_test_files_dir="nwb_test_files"
 

# delete all files in a directory except 0_README.txt
# this written as function because simple "rm" will remove 0_README.txt
# and the following commands gave an error message when run in the script:
# rm `find $target -type f ! -name "0_README.txt"`
# find $examples_created_dir -type f ! -name "0_README.txt" -delete
# find $examples_created_dir -type d -delete
# direct use of find (two above) gave message:
# find: -delete: ../examples/created_nwb_files: relative path potentially not safe
#
function clear_dir () {
    target_dir=$1
    echo "target_dir is $target_dir"
    files=`find $target_dir -type f ! -name "0_README.txt"`
    for fname in $files
    do
        if [[ "$fname" !=  "0_README.txt" ]] ; then
            rm $fname
        fi
    done
    dirnames=`find $target_dir -d -mindepth 1 -type d`
    for dname in $dirnames
    do
        rmdir $dname
    done
}

# examples_created_dir="../examples/created_nwb_files"
# 
# 
# 
# echo "before"
# ls $examples_created_dir
# clear_dir $examples_created_dir
# 
# echo "after"
# ls $examples_created_dir
# 
# exit 0


# Following opening brace used to redirect standard output and standard error of all enclosed
# commands into $logFile as well as display on screen
# From:
#  http://unix.stackexchange.com/questions/61931/redirect-all-subsequent-commands-stderr-using-exec
# #!/bin/bash
# {
#     somecommand 
#     somecommand2
#     somecommand3
# } 2>&1 | tee -a $DEBUGLOG

# ----- Opening brace used to redirect standard output and standard error to screen and file
{

echo "Python version is:"
python -V


# to speed up testing for development -------------------------
# if [[ "1" == "1" ]] ; then


# matlab_bridge

# following loads assignment of matlab variable, should be set to location of matlab
. test_all.cfg

# echo "matlab is $matlab"
if [[ -z "$matlab" ]] ; then
    echo "matlab path not specified in test_all.cfg file."
    test_matlab=0
elif [[ ! -f "$matlab" ]] ; then
    echo "matlab executable not found at location specified in test_all.cfg file: $matlab"
    test_matlab=0
else
    # see if nwb installed in matlab
    echo "Checking for matlab with NWB installed in matlab pyversion Python..."
    result=`$matlab -nodisplay -nosplash -nodesktop -r "try, [T] = evalc('py.nwb.display_versions.matlab();'), catch me, fprintf('%s / %s\n',me.identifier,me.message), end, exit"`
    present="Python executable:"
    absent="MATLAB:undefinedVarOrClass"
    if [[ "$result" =~ "$present" ]] ; then
        echo "Matlab found with NWB installed in pyversion python."
        test_matlab=1
    elif [[ "$result" =~ "$absent" ]] ; then
        echo "Matlab found.  But NWB is not installed in pyversion python."
        echo "To test matlab, setup matlab according to instructions in matlab_bridge directory"
        test_matlab=0
    else
        echo "unexpected return from testing for matlab pyversion python:"
        echo $result
        exit 1
    fi
fi
if [[ "$test_matlab" == "0" ]] ; then
    echo "Not testing matlab_bridge"
else
    echo "Testing matlab_bridge"
    echo "Running matlab unittests"
    utd="../matlab_bridge/matlab_unittest"
    cd $utd
    # clear old nwb files from matlab_unittest directory
    rm *.nwb
    $matlab -nodisplay -nosplash -nodesktop -r "try, run('run_all_tests.m'), catch me, fprintf('%s / %s\n',me.identifier,me.message), end, exit"
    cd $cwd

    echo "run matlab examples"
    # clear output directories for matlab example create scripts
    ml_examples_nwb_dir="../matlab_bridge/matlab_examples/created_nwb_files"
    clear_dir $ml_examples_nwb_dir
    exd="../matlab_bridge/matlab_examples/create_scripts"
    cd $exd
    $matlab -nodisplay -nosplash -nodesktop -r "try, run('run_all_examples.m'), catch me, fprintf('%s / %s\n',me.identifier,me.message), end, exit"
    cd $cwd
    
    echo "copying unittest results file"
    curr_ml_dir="curr/matlab_bridge"
    curr_ml_unittest_dir="$curr_ml_dir/unittest"
    mkdir -p $curr_ml_unittest_dir
    cp ../matlab_bridge/matlab_examples/text_output_files/unittest_results.txt $curr_ml_unittest_dir
    
    echo "Generating h5diffsig output for matlab unittest nwb files"
    curr_ml_unittest_sig_dir="$curr_ml_unittest_dir/h5sig"
    mkdir -p $curr_ml_unittest_sig_dir
    ml_unittest_dir="../matlab_bridge/matlab_unittest"
    python ../examples/utility_scripts/make_h5sig.py $ml_unittest_dir $curr_ml_unittest_sig_dir

    echo "copying example create results files"
    curr_ml_examples_dir="$curr_ml_dir/examples"
    curr_ml_examples_create_dir="$curr_ml_dir/examples/create"
    mkdir -p $curr_ml_examples_create_dir
    ml_examples_create="../matlab_bridge/matlab_examples/text_output_files/create"
    cp $ml_examples_create/*.txt $curr_ml_examples_create_dir
    
    echo "making signature files for matlab examples"
    curr_ml_examples_sig_dir="$curr_ml_examples_dir/h5sig"
    mkdir -p $curr_ml_examples_sig_dir
    python ../examples/utility_scripts/make_h5sig.py $ml_examples_nwb_dir $curr_ml_examples_sig_dir


fi

echo "done processing matlab"
# exit 0


# Python unittests

echo "Running python unittests..."
unittest_nwb_dir="../unittest"
cd $unittest_nwb_dir
rm *.nwb
./run_tests.sh 2>&1 | tee ../test_all/curr/unittest/run_tests.txt
cd $cwd

# run validator on unittests
echo "validating unittest nwb files"
validate_unittest_dir="curr/unittest/validate"
mkdir -p $validate_unittest_dir
../examples/utility_scripts/validate_others.sh $unittest_nwb_dir $validate_unittest_dir


# Generate h5diffsig output for unittest nwb files
h5sig_unittest_dir="curr/unittest/h5sig"
mkdir -p $h5sig_unittest_dir
python ../examples/utility_scripts/make_h5sig.py $unittest_nwb_dir $h5sig_unittest_dir


# echo "done unittests"


examples_created_dir="../examples/created_nwb_files"
examples_create_text_dir="../examples/text_output_files/create"
if [[ ! -d "$examples_created_dir" ]] ; then
    echo "Directory $examples_created_dir not found.  Aborting"
    exit 1
fi
if [[ ! -d "$examples_create_text_dir" ]] ; then
    echo "Directory $examples_create_text_dir not found.  Creating it."
    mkdir -p $examples_create_text_dir
fi


# clear output directories for example create scripts
# echo "clearing directories $examples_created_dir and examples_create_text_dir"
clear_dir $examples_created_dir
clear_dir $examples_create_text_dir

# rm `find $examples_created_dir -type f ! -name "0_README.txt"`
# rm `find $examples_created_dir -type d`
# 
# # rm -rf $examples_create_text_dir/*
# echo "doing rm find $examples_create_text_dir -type f ! -name 0_README.txt"
# # find $examples_create_text_dir -type f ! -name "0_README.txt" -delete
# rm `find $examples_create_text_dir -type f ! -name "0_README.txt"`

# read -n1 -r -p "Press space to continue..." key


echo "Running examples/create_scripts"
cd ../examples/create_scripts
./run_all.sh f
cd $cwd

examples_curr_create="curr/examples/create"
echo "Copying $examples_create_text_dir/*.txt to $examples_curr_create"
mkdir -p $examples_curr_create
# use cp `find ...` to copy all except 0_README.txt
# cp $examples_create_text_dir/*.txt $examples_curr_create
cp `find $examples_create_text_dir -type f -name "*.txt" ! -name "README.txt"` $examples_curr_create

echo "Running validation script on example created nwb files..."
validate_output_dir="../examples/text_output_files/validate"

if [[ ! -d "$validate_output_dir" ]] ; then
    echo "Directory $validate_output_dir not found.  Creating it."
    mkdir -p $validate_output_dir
fi
echo "clearing $validate_output_dir"
# rm -f $validate_output_dir/*.txt
# use find so to not delete 0_README.txt
# find  $validate_output_dir ! -name "0_README.txt" -delete
# rm `find  $validate_output_dir ! -name "0_README.txt"`
clear_dir $validate_output_dir

cd ../examples/utility_scripts
python validate_all.py f
cd $cwd

echo "Copying output of validation of examples script to curr"
examples_curr_validate="curr/examples/validate"
mkdir -p $examples_curr_validate
# cp $validate_output_dir/*.txt $examples_curr_validate
cp `find $validate_output_dir -type f -name "*.txt" ! -name "README.txt"` $examples_curr_validate

echo "Generating h5sig files for examples"
examples_h5sig_dir="curr/examples/h5sig"
mkdir -p $examples_h5sig_dir
python ../examples/utility_scripts/make_h5sig.py $examples_created_dir $examples_h5sig_dir

# Validate schema examples
echo "validating schema files"
schema_check_file="curr/check_schemas.txt"
cd ../examples/utility_scripts/
./check_schemas.sh > ../../test_all/$schema_check_file
cd $cwd

# generate documentation
echo "Generating documentation"
doc_dir=../examples/text_output_files/doc
if [[ ! -d "$doc_dir" ]] ; then
    mkdir -p $doc_dir
    echo "created $doc_dir"
else
    rm -f $doc_dir/*.html
    echo "cleared $doc_dir"
fi
cd ../examples/utility_scripts/
python make_docs.py
cd $cwd
doc_dir2="curr/doc"
mkdir -p $doc_dir2
cp $doc_dir/*.html $doc_dir2


# test nwb_sample files if present
if [[ ! -d "$nwb_test_files_dir" ]] ; then
    echo "Skipping nwb_samples because directory '$nwb_test_files_dir' not found"
else
    nwb_tf_dir="nwb_test_files"
    dest="curr/$nwb_tf_dir/h5sig"
    mkdir -p $dest
    echo "Generating $dest"
    python ../examples/utility_scripts/make_h5sig.py $nwb_test_files_dir $dest

    dest="curr/$nwb_tf_dir/validate"
    mkdir -p $dest
    echo "Generating $dest"
    ../examples/utility_scripts/validate_others.sh $nwb_test_files_dir $dest
fi

# finally, build signature file
python make_dirsig.py curr


# close if for development --------------------
# fi


echo "Done building ./curr"

# ----- Closing brace used to redirect standard output and standard error to screen and file
} 2>&1 | tee -a $logFile


exit 0


