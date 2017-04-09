# script to validate all NWB files stored in a directory, sending
# output to another directory.
# Validation is done using the external "nwb_core.py" definition and
# not using any schema's included in the file.  So it will not if
# the nwb files were created using extensions.  To validate files
# that use extensions, eiter the extensions need to be specified in
# the command line or using the specifications stored in the file
# need to be specified.  Examples of validations using these methods
# are respectively in the scripts "validate_all.py" and
# "validate_internal.sh"

if [[ ! "$#" -eq 2 ]] ; then
    echo "Format is:"
    echo "$0 <nwb_dir> <output_dir>"
    echo "where:"
    echo "<nwb_dir> - directory containing nwb files"
    echo "<output_dir> - directory for validation output"
    exit 1
fi

nwb_dir=$1
out_dir=$2

if [[ ! -d "$nwb_dir" ]] ; then
    echo "<nwb_dir> does not exist: $nwb_dir"
    exit 1
fi


if [[ ! -d "$out_dir" ]] ; then
    echo "<out_dir> does not exist: $out_dir"
    exit 1
fi

# get list of nwb files
files=`ls $nwb_dir/*.nwb`

if [[ "$files" == "" ]] ; then
    echo "No files with extension '.nwb' found in <nwb_dir>: $nwb_dir"
    exit 1
fi

# validate each file
for nwb_file in $files
do
    fname_and_extension=${nwb_file##*/}
    fn=${fname_and_extension%.nwb}
    # fn="${nwb_file%.*}"
    echo "doing: python -m nwb.validate $nwb_dir/$fn.nwb > $out_dir/$fn.txt"
    python -m nwb.validate $nwb_dir/$fn.nwb > $out_dir/$fn.txt
#     if [ $? -ne 0 ]; then
#         echo "python -m nwb.validate $nwb_dir/$fn.nwb FAILED"
#         exit 1
#     fi
done

# echo "All done"

