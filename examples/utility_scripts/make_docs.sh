
echo
echo "This script demonstrates creating documentation for the NWB format."
echo
echo "Documentation may be created for the core format alone, or the"
echo "core format combined with one or more extensions."
echo
echo "The documentation is generated from the format specifications."
echo "The format specifications can be in standalone '.py' files or"
echo "can be loaded from a created NWB file.  The latter method "
echo "is useful for generating documentaiton that is guaranteed to"
echo "describe a particular NWB file."

echo
echo "Making core doc by doing:"
cmd="python -m nwb.make_docs > ../text_output_files/doc/core_doc.html"
echo "$cmd"
python -m nwb.make_docs > ../text_output_files/doc/core_doc.html

echo
echo "Making core doc with two extensions by doing:"
cmd="python -m nwb.make_docs ../create_scripts/extensions/e-intracellular.py,../create_scripts/extensions/e-general.py > \
../text_output_files/doc/core_intra_gen.html"
python -m nwb.make_docs ../create_scripts/extensions/e-intracellular.py,../create_scripts/extensions/e-general.py > \
../text_output_files/doc/core_intra_gen.html

echo
echo "Making documentation from created NWB file by doing:"
cmd="python -m nwb.make_docs ../created_nwb_files/interface-e.nwb ../created_nwb_fles/interface-e.nwb > ../text_output/doc/interface-e.html"
echo "$cmd"
python -m nwb.make_docs ../created_nwb_files/interface-e.nwb > ../text_output_files/doc/interface-e.html

