# Script to validate nwb_core specification and all example extensions.
# Uses the nwb.check_schema utility (which in turn, uses the json-schema
# specification in file meta_schema.py).

# nwb.check_schema requires having jsonschema installed.
# available at: https://github.com/Julian/jsonschema

# to run, type ./check_all_schema.sh

# check core schema
python -m nwb.check_schema -
# echo "result is $result"

# get list of extensions to check
extensions=`ls ../create_scripts/extensions/e-*.py`

# check schema for each extension
for fn in $extensions
do
  python -m nwb.check_schema $fn
done

echo "All done"

