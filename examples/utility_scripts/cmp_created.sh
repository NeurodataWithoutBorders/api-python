#!/bin/bash

# This script compares nwb files in two directories, saving the result
# (showing differences) in a third directory.


nwb1=$1
nwb2=$2
dest=$3
if [ ! -d "$nwb1" ]; then
  nwb1="../created_nwb_files_py2"
fi
if [ ! -d "$nwb2" ]; then
  nwb2="../created_nwb_files_py3"
fi
if [ ! -d "$dest" ]; then
  dest="../text_output_files/diff/created_nwb23"
fi
if [ ! -d "$nwb1" ]; then
  echo "Directory nwb1, '$nwb1' does not exist"
  exit 1
fi
if [ ! -d "$nwb2" ]; then
  echo "Directory nwb2, '$nwb2' does not exist"
  exit 1
fi
if [ ! -d "$dest" ]; then
  echo "Directory dest, '$dest' does not exist"
  exit 1
fi

echo "comparing $nwb1/*.nwb to $nwb2/*.nwb, saving differences in $dest"
# FILES=`find $nwb1 -name "*.nwb" -exec basename {} \;`
FILES=`find -H $nwb1 -name "*.nwb"`
for f in $FILES
	do
                bn=`basename $f`
                # Substring Removal
                path=${f#$nwb1}
		f_name=${bn%.*}
                file2="$nwb2$path"
		if [ ! -f "$file2" ]; then
			echo "Not found: $file2"
			continue
		fi
                echo "doing python -m nwb.h5diffsig $f $file2 > $dest/$f_name.txt"
                python -m nwb.h5diffsig $f $file2 > $dest/$f_name.txt
	done

