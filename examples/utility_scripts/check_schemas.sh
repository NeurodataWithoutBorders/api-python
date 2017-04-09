# Script to validate nwb_core specification and all example extensions.
# Uses the nwb.check_schema utility (which in turn, uses the json-schema
# specification in file meta_schema.py).

# nwb.check_schema requires having jsonschema installed.
# available at: https://github.com/Julian/jsonschema

# to run, type ./check_schemas.sh

# check core schema
echo "doing: python -m nwb.check_schema N"
python -m nwb.check_schema N

# get list of extensions to check
extensions=`ls ../create_scripts/extensions/e-*.py`

# check schema for each extension
for fn in $extensions
do
  echo "doing: python -m nwb.check_schema $fn"
  python -m nwb.check_schema $fn
done

echo "All done"

