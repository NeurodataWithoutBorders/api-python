# Script to perform all tests

# Requires existing "orig" directory containing signature file
# ("dirsig.txt").  Builds "curr" directory containing results of
# all scripts and signature file for results.  Compares
# curr/dirsig.txt to orig/dirsig.txt
# If these match, all tests pass.

cwd=`pwd`

orig_sig="orig/dirsig.txt"
source_data_dir="../examples/source_data_2"

if [[ ! -e "$orig_sig" ]] ; then
    echo "File '$orig/dirsig.txt' does not exist.  Cannot run tests."
    exit 1
fi


if [[ ! -e "$source_data_dir" ]] ; then
    echo ""
    echo "*** Source data directory is not installed.  Do you wish to install it?"
    echo "Directory '$source_data_dir' must be installed before running test."
    echo "Do you wish to install $source_data_dir (about 1.2GB; 580MB download)?"
    echo "Type 1 if Yes.  2 if no."
    select yn in "Yes" "No"; do
        if [[ "$yn" == "Yes" ]] ; then
             cd ../examples/utility_scripts
             python install_source_data.py
             status=$?
             cd $cwd
             if [[ "$status" -ne "0" ]] ; then
                 echo "Tests aborted because $source_data_dir not installed."
                 exit 1
             fi
             break ;
        else
             echo "Tests aborted because $source_data_dir not installed."
             exit 1
        fi
    done
fi


./make_curr.sh

curr_sig="curr/dirsig.txt"
if [[ ! -e "$curr_sig" ]] ; then
    echo "File '$curr_sig' does not exist.  Cannot complete tests."
    exit 1
fi

python show_diff.py

status=$?

echo
if [[ "$status" -eq "0" ]] ; then
    echo "** ALL TESTS PASS **"
else
    echo "** ONE OR MORE TESTS FAILED. **"
fi 


