edho
echo "This script demonstrates validating an NWB file using the format"
echo "specifications stored within the file."

if [[ ! -e "../created_nwb_files/annotations.nwb" ]] ; then
   echo "This script requires file ../created_nwb_files/annotations.nwb"
   echo "do: python ../create_scripts/annotations.py to create that file"
   echo "before runnign this script"
   exit 1
fi

   # Note the two dashes after the file name.  First dash is for
   # extensions, second is for the core specification (nwb_core.py).

   python -m nwb.nwb_validate ../created_nwb_files/annotations.nwb - -





