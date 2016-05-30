# this script generates PDF files from html files, adding page numbers
# it requires the "wkhtmltopdf" utility be installed

if [ "$#" -ne 2 ]; then
   script_name=${0##*/}
   echo "Requires two command-line arguments:"
   echo "<doc_dir> <html_file_base_name>"
   echo "Example:"
   echo "./$script_name ../text_output_files/doc/ nwb_file_format_specification_1.0.3_beta"
   exit 1
fi

docdir=$1
base_name=$2
html="$base_name.html"
pdf="$base_name.pdf"

echo "doc dir=$docdir"
echo "html file=$html"
echo "pdf file=$pdf"

wd=`pwd`
cd $docdir
wkhtmltopdf --footer-center [page]/[topage] $html $pdf
cd $wd


