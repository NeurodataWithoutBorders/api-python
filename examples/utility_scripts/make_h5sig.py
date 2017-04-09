
# This script runs utility 'nwb.h5diffsig' to generate a text summary of
# hdf5 (nwb) file contents which can be used to compare one hdf5 to another.

import sys
import glob
import os, fnmatch
from subprocess import check_output
from sys import version_info

def error_exit(msg):
    if msg:
        print(msg)
    print ( "Format is")
    print ("%s <dir_or_file> <output_dir> [<extension>]" % sys.argv[0])
    print ("where:")
    print ("  <dir_or_file> - either a directory containing hdf5/nwb files or")
    print ("        a single hdf5/nwb file.")
    print ("  <output_dir>  - output directory for storing generated h5diffsig output file(s)")
    print ("  <extensions>   - comma separated list of  extension to use to find nwb or hdf5 files.")
    print ("        Default is 'nwb,h5'.  Other common values may include 'hdf5'.")
    sys.exit(1)

# the command that is run
command = ['python', '-m', 'nwb.h5diffsig']

# py3: convert bytes to str (unicode) if Python 3   
def make_str3(val):
    if isinstance(val, bytes) and version_info[0] > 2:
        return val.decode('utf-8')
    else:
        return val



def process_file(dirpath, filename, output_dir, output_path, extension):
    # output path is path to create inside output_dir
    global command
#     print("process_file output_path=%s, dirpath=%s, filename=%s, output_dir=%s, extension=%s\n" %
#         (output_path, dirpath, filename, output_dir, extension))
    output_file_name = "%stxt" % filename[0:-len(extension)]
#     print ("output_file_name=%s" % output_file_name)
    input_file = os.path.join(dirpath, filename)
    # N option to filter NWB 'variable' datasets, e.g. /file_create_date
    # a option, to sort output (groups / datasets) alphabetically
    cmd = command + [input_file] + ["-Na"]
    command_str = " ".join(cmd)
    if output_path != "":
       output_dir = os.path.join(output_dir, output_path)
       if not os.path.exists(output_dir):
           os.makedirs(output_dir)
    outpath = os.path.join(output_dir, output_file_name)
    print ("doing %s > %s" % (command_str, outpath))
    output = make_str3(check_output(cmd))
    with open(outpath, "w") as f:
        f.write(output)
    
def get_extension(file, extensions):
    # returns extension in list extensions file ends with or None
    extension = [e for e in extensions if file.endswith(".%s" % e)]
    assert len(extension) <= 1
    extension = extension[0] if len(extension) == 1 else None
    return extension
    
def process_files(input_dir_or_file, output_dir, extensions):
    # convert comma separated string to list for use with get_extension
    extensions = extensions.split(",")
    if os.path.isfile(input_dir_or_file):
        dirpath, filename = os.path.split(input_dir_or_file)
        extension = get_extension(filename, extensions)
        if extension is None:
            print("Single file specified, but does not end with extension '%s': %s" % (
                extension, filename))
            sys.exit(1)
        output_path = ""
        process_file(dirpath, filename, output_dir, output_path, extension)
    else:
        # input_dir_or_file is a directory, processes files within it
        for dirpath, dirnames, filenames in os.walk(input_dir_or_file):
            #for filename in [f for f in filenames if f.endswith(textensions)]:
            for filename in filenames:
                extension = get_extension(filename, extensions)
                if extension is not None:
                    assert dirpath.startswith(input_dir_or_file)
                    output_path = dirpath[len(input_dir_or_file):].lstrip("/")
                    process_file(dirpath, filename, output_dir, output_path, extension)

def clear_directory(path):
    if os.path.isdir(path):
        cwd = os.getcwd()
        os.chdir(path)
        for f in os.listdir("."):
            if f.endswith(".txt"):
                os.remove(f)
        os.chdir(cwd)
        print ("cleared %s" % path)
    else:
        os.mkdir(path)
        print ("created %s" % path)

def clear_output_directory(output_option):
    global txt_output_dir
    if output_option in ("f", "b"):
        clear_directory(txt_output_dir)
            

# filelist = [ f for f in os.listdir(".") if f.endswith(".bak") ]
# for f in filelist:
#     os.remove(f)

if __name__ == '__main__':
    if len(sys.argv) not in (3,4):
        error_exit("Invalid number of command line arguments: %s" % len(sys.argv))
    input_dir_or_file = sys.argv[1]
    output_dir = sys.argv[2]
    extensions = "nwb,h5" if len(sys.argv) == 3 else sys.argv[3]
    if not os.path.exists(input_dir_or_file):
        error_exit("Input <dir_or_file> does not exist: %s" % input_dir_or_file)
    if not os.path.isdir(output_dir):
        error_exit("Output <dir_or_file> does not exist: %s" % output_dir)  
    # clear_output_directory(output_dir)
    process_files(input_dir_or_file, output_dir, extensions)
    
