
# This script creates a "signature file" for the contents of all
# files in a directory.  The signature file, has a list of all the files
# and a hash code for each.  This is used to verify that files generated
# by scripts match those that were originally generated.


import sys
import glob
import os, fnmatch
import re
from sys import version_info
from nwb import value_summary as vs

def error_exit(msg):
    if msg:
        print(msg)
    print ( "Format is")
    print ("%s <dir_or_file>" % sys.argv[0])
    print ("where:")
    print ("  <dir_or_file> - a directory containing files, or a single file.")
    print ("      If a directory is given, a single signature file, named 'dircig.txt'")
    print ("      is created inside it.  If a file is given, the name and hash of the")
    print ("      file is written to standard output.")
    sys.exit(1)

def remove_sig_somments(contents):
    # remove text inside <% ... %> from string contents
    # This done to remove text that is likely to be variable across nwb files
    # that are the same (such as file_create_date) so it is not used for hash
    # comparison
    contents = re.sub(b"<%.*?%>", b"", contents)
    return contents
     

def get_file_hash(path):
    f = open(path, "rb")
    contents = f.read()
    f.close()
    contents = remove_sig_somments(contents)
    hash = vs.hashval(contents)
    # make sure hash is 6 characters
    if len(hash) < 6:
        hash = "%s%s" % (hash, hash[1]*(6-len(hash)))  # append repeats of second character
    return hash
    
def process_files(input_dir_or_file):
    if os.path.isfile(input_dir_or_file):
        hash = get_file_hash(input_dir_or_file)
        print ("%s %s" % (hash, input_dir_or_file))
    else:
        # input_dir_or_file is a directory, processes files within it
        output = []
        output_file_name = "dirsig.txt"
        for dirpath, dirnames, filenames in os.walk(input_dir_or_file):
            for filename in filenames:
                assert dirpath.startswith(input_dir_or_file)
                path = os.path.join(dirpath, filename)
                if path == os.path.join(input_dir_or_file, output_file_name):
                    continue
                hash = get_file_hash(path)
                output_path = path[len(input_dir_or_file):].lstrip("/")
                output.append("%s %s" % (hash, output_path))
                # print ("dirpath=%s, output_path=%s, filename=%s" % (dirpath, output_path, filename))
        # write output
        output_file_path = os.path.join(input_dir_or_file, output_file_name)
        f = open(output_file_path, "w")
        f.write("\n".join(output))
        f.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        error_exit("Invalid number of command line arguments: %s" % len(sys.argv))
    input_dir_or_file = sys.argv[1]
    if not os.path.exists(input_dir_or_file):
        error_exit("Input <dir_or_file> does not exist: %s" % input_dir_or_file)
    process_files(input_dir_or_file)