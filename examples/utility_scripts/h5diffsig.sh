
echo "Demonstrate running HDF5 diff utility 'h5diffsig.py'"


echo "This demo finds difference between:"
echo "  ../created_nwb_files/motion_correction.nwb, and:"
echo "  ../created_nwb_files/motion_correction2.nwb"
echo
echo "The difference is displaed on the screen, and saved"
echo "in file: ../text_output_files/diff/motion_correction1_2_diff.txt"


python -m nwb.h5diffsig ../created_nwb_files/motion_correction.nwb ../created_nwb_files/motion_correction2.nwb > \
../text_output_files/diff/motion_correction1_2_diff.txt

cat  ../text_output_files/diff/motion_correction1_2_diff.txt




