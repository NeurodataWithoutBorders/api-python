# script to show any difference between generated signature files
# But ignoring those in nwb_test_samples if only one of the signature
# files has those.

import sys
import os
# import glob
import re
 
# name of signature file
sig_file_name = "dirsig.txt"
# name of directory containing output from processing nwb_test_files (may not be present)
# the value for this must match that used in script make_curr
nwb_tf_dir="nwb_test_files"

# test_files_dir = "nwb_test_files"

# global structure storing all signature information
si = {
    "curr": {        # sitop == "curr"
        "sdir": "",        # directory storing curr/dirsig.txt (default is "curr")
        "sigs": {},        # map file path to signature
        "only_in": [],     # names of files only in curr (but not nwb_test_files)
        "oi_prefix": {},   # prefix (top directories) => files only in curr, e.g. 'matlab_bridge'
        "tf_only_in": [],  # names of nwb_test_files that are only in curr
        "contents": "",    # file contents, temporary storage
         }, 
    "orig": {        # sitop == "orig"
        "sdir": "",        # directory storing orig/dirsig.txt (default is "orig")         
        "sigs": {},        # map file path to signature
        "only_in": [],     # names of files only in curr (but not nwb_test_files)
        "oi_prefix": {},   # prefix (top directories) => files only in orig, e.g. 'matlab_bridge'
        "tf_only_in": [],  # names of nwb_test_files that are only in curr
        "contents": "",    # file contents, temporary storage
    	},
    "common_tf": [],       # list of test_files common to both "curr" and "orig"
    }         


def display_doc():
    print ("Format is:")
    print ("python %s [<curr> [<orig>] ]" % sys.argv[0])
    print ("Where:")
    print ("   <curr> is a directory containing the signiture file (dirsig.txt)")
    print ("          for the current installation.  Default is 'curr'.")
    print ("   <orig> is a directory containing the signature file for the reference")
    print ("          installation.  Default is 'orig'.")

def load_contents():
    # load contents of signature file in directory described by dir_desc
    global si, sig_file_name
    for sitop in ("curr", "orig"):
        sdir = si[sitop]["sdir"]
        sig_path = os.path.join(sdir, sig_file_name)
        if not os.path.isfile(sig_path):
            print ("'%s' file not found at: %s" % (sitop, sig_path))
            display_doc()
            sys.exit(1)
        f = open(sig_path)
        contents = f.read()
        si[sitop]["contents"] = contents
        f.close()

def build_si():
    # builds si structure from loaded contents
    build_sigs()
    find_only_ins()


def find_only_ins():
    # find files that are in si["curr"]["sigs"] or si["orig"]["sigs"] but not both
    # save in si "only_in" structures ("only_in", "tf_only_in")
    in_curr = set(list(si["curr"]["sigs"]))
    in_orig = set(list(si["orig"]["sigs"]))
    # store set in "only_in" temporarily.  These will be updated by fill_tf_only_in
    si["curr"]["only_in"] = in_curr - in_orig
    si["orig"]["only_in"] = in_orig - in_curr
    fill_oi_prefix()
    fill_tf_only_in() 
    common = in_curr.intersection(in_orig)
    # get test_file names that are in common
    si["common_tf"] = get_tf_names(get_tf_paths(common))
    filter_sigs(common)

def filter_sigs(common):
    # remove sigs entries that are not common to both "curr" and "orig"
    global si
    for sitop in ("curr", "orig"):
        for path in list(si[sitop]["sigs"]):
            if path not in common:
                del si[sitop]["sigs"][path]

def get_prefix(path):
    # return top directory (prefix) in path, or None if nothing before first '/'
    idxs = path.find('/')
    if idxs != -1:
        # save prefix
        prefix = path[0:idxs]
    else:
        prefix = None
    return prefix


def fill_oi_prefix():
    # move files that are in 'only_in' which have a prefix in 'oi_prefix' to the
    # list in 'oi_prefix'.  This done so these files are not counted as missing,
    # since all files in the directories in 'oi_prefix' are ignored.
    # Expected instances of this will be with prefix 'matlab_bridge' or 'nwb_test_files'
    global si
    for sitop in ("curr", "orig"):
        for file in list(si[sitop]["only_in"]):
            file_prefix = get_prefix(file)
            if file_prefix in si[sitop]["oi_prefix"]:
                # append file to list of oi_prefix
                si[sitop]["oi_prefix"][file_prefix].append(file)
                # remove file from only_in
                si[sitop]["only_in"].remove(file)


def fill_tf_only_in():
    # find which only_ins are nwb test files.  Remove those from only_ins and put just
    # the file names in tf_only_ins.  Also convert set "only_ins" to sorted list
    global si
    for sitop in ("curr", "orig"):
        # get set of paths starting with test file directory
        tf_only_in = get_tf_paths(si[sitop]["only_in"])
        # remove test files from only_in sets, since these will be ignored.  Convert to sorted list
        si[sitop]["only_in"] = sorted(list(si[sitop]["only_in"] - tf_only_in))
        # get file names from tf_only_in entries by removing prefix
        si[sitop]["tf_only_in"] = get_tf_names(tf_only_in)

def get_tf_paths(paths):
    # return set of strings in paths that start with test file directory
    global nwb_tf_dir
    test_files_pattern = "%s/" % nwb_tf_dir  # append slash
    tf_paths = set([ x for x in paths if x.startswith(test_files_pattern)])
    return tf_paths

def get_tf_names(paths):
    # returns sorted list of test_file names extracted from paths by removing prefix
    global nwb_tf_dir
    tf_names = set([])
    tf_pattern = "%s/(?:validate|h5sig)/(.+)" % nwb_tf_dir
    for path in paths:
        match = re.match(tf_pattern, path)
        if not match:
            sys.exit("get_tf_names, could not match: %s" % path)
        tf_name = match.group(1)
        tf_names.add(tf_name)
    return sorted(list(tf_names))


# def has_nwb_test_files(contents):
#     # return True if string contents contains signatures for nwb test files otherwise False
#     global test_files_dir
#     pattern = "\n[a-zA-Z]{6} %s/" % test_files_dir
#     match = re.search(pattern, contents)
#     return match is not None
    
# def yesno(val):
#     assert isinstance(val, bool)
#     msg = "Yes" if val else "No"
#     return msg


# def get_test_file_status(curr_contents, curr_dir, orig_contents, orig_dir):
#     # Return True if both curr_contents and orig_contents contain nwb test file results
#     # return False otherwise.  Also display a message indicating which files have the
#     # test file results.
#     global test_files_dir
#     curr_has_nwb_test = has_nwb_test_files(curr_contents)
#     orig_has_nwb_test = has_nwb_test_files(orig_contents)
#     msg1 = ("Contains %s: %s -%s, %s -%s" % (test_files_dir, curr_dir, yesno(curr_has_nwb_test),
#         orig_dir, yesno(orig_has_nwb_test)))
#     check_nwb_test_files = curr_has_nwb_test and orig_has_nwb_test
#     msg2 = "(%s %s)" % ("Including" if check_nwb_test_files else "Not including", test_files_dir)
#     msg = "%s; %s" % (msg1, msg2)
#     print (msg)
#     return check_nwb_test_files

def build_sigs():
    # build "sigs", e.g. dictionary of file names => signatures for si[sitop]
    # also compute oi_prefix (only in prefix)
    global si
    prefix_found = { "curr": set([]), "orig": set([]) }
    for sitop in ("curr", "orig"):
        sdir = si[sitop]["sdir"]
        # contents is raw text contents of file for sitop
        contents = si[sitop]["contents"]
        lines = contents.splitlines()
        pattern = "([a-zA-Z]{6}) (.*)"
        for line in lines:
            match = re.match(pattern, line)
            if not match:
                sys.exit("Unable to match hash and file path in %s: %s" % (sdir, line))
            hash = match.group(1)
            path = match.group(2)
            # save the path and signature
            assert path not in si[sitop]["sigs"]
            si[sitop]["sigs"][path] = hash
            # save prefix
            prefix = get_prefix(path)
            if prefix:
                # save prefix
                prefix_found[sitop].add(prefix)
        # clear contents since its no longer needed
        del si[sitop]["contents"]
    # compute oi_prefix
    for sitop in ("curr", "orig"):
        inv_top = get_inv_top(sitop)
        oi_prefix = prefix_found[sitop] - prefix_found[inv_top]
        for prefix in oi_prefix:
            # initialize to empty list of files, fill in later in function fill_oi_prefix
            si[sitop]['oi_prefix'][prefix] = []      

def format_list_lines(prefix, vals, max_line_width=80, indent=4):
    # formats list "vals", with string "prefix" before it, packing values onto as few of
    # lines as possible with each line not longer than line_width.  Also indent lines after
    # the first "indent" number of characters.
    line_width = len(prefix) + 2  # current line width, +2 for ":" and space after prefix
    # build up message in msg
    msg = "%s: " % prefix
    first_on_line = True
    for i in range(len(vals)):
        val = vals[i]
        comma = ", " if not first_on_line else ""
        msg = "%s%s%s" % (msg, comma, val)
        first_on_line = False
        line_width += len(comma) + len(val)
        if line_width > max_line_width and i + 1 < len(vals):
            # start new line
            msg = "%s,\n%s" % (msg, " "*indent)  # add indent on new line
            line_width = 0
            first_on_line = True
    return msg
    
    
#     
#     nl_elements = []  # index of elements that should have a newline character displayed after them
#     # compute nl_elements
#     for idx in range(len(vals)):
#         val = vals[idx]
#         len_val = len(val)
#         line_width += len_val + 2  # 2 for comma and space
#         if line_width > max_line_width and idx < len(vals):
#             nl_elements.append(idx)
#             line_width = indent
#     # format and display
#     ne = nl_elements  # shorthand
#     lne = length(ne)  # shorthand
#     vl = vals         # shorthand
#     indent_s = " "*indent  # indent string
#     lines = "".join([ 
#         vals[i] if i==0 and length(vals) == 1 # only one value
#         else "%s%s" % (indent_s, vals[i]) if i-1 in nl_elements  # first val on new line
#         else "
#         else ", %s" % vals[i] if i > 0 and i not in nl_elements and i # middle value
#     # eol value
#     # start new line value
#     
#     
#         else "%slen(nl_else ", %s" % vals[i] if i not in
#     msg = "\n".join(

def check_consistency():
    # check consistency between files in the same top dir, e.g. between
    # matlab and python hdf5 files
    global si, cc_check_count
    cc_check_count = {}    # consistency check count, for displaying report
    diffs = []
    for sitop in ("curr", "orig"):
        diffs.extend(ccheck(sitop, "matlab_bridge/unittest/h5sig/", "unittest/h5sig/"))
        diffs.extend(ccheck(sitop, "matlab_bridge/examples/h5sig/", "examples/h5sig/"))
    return diffs


def ccheck(sitop, path1, path2):
    # compare hashes of matching files that start with path1 and path2
    # return any differences if matching files do not have the same hash
    files1 = get_path_files(sitop, path1)
    files2 = get_path_files(sitop, path2)
    # files1 and files2 are dicts, keys are rest of file name after path, values
    # are the hash
    global cc_check_count
    key = "%s - %s" % (path1, path2)
    cc_check_count[key] = 0
    diffs = []
    for name in files1:
        if name in files2:
            if files1[name] == files2[name]:
                # keep track of number of matches found
                cc_check_count[key] += 1
            else:
                msg = "Inconsistency: '%s' in '%s' and '%s' should match, but don't." % (
                    name, path1, path2)
                diffs.append(msg)
    return diffs

def get_path_files(sitop, path):
    # return dict with keys any files that start with path (but with path removed in
    # the key), and value the hash for the file
    files = {}
    global si
    assert path.endswith('/')
    for file in si[sitop]["sigs"]:
        if file.startswith(path):
            hash = si[sitop]["sigs"][file]
            base_name = file[len(path):]
            files[base_name] = hash
    return files


def get_inv_top(sitop):
    # give the alternate top directory
    inv_top = "curr" if sitop == "orig" else "orig"
    return inv_top
    

def find_diff():
    # return differences between si["curr"] and si["orig"]
    global si, cc_check_count
    diffs = []
    # display messages about oi_prefix
    for sitop in ("curr", "orig"):
#         if si[sitop]["oi_prefix"]:
#             sdir = si[sitop]["sdir"]
#             diffs.append("Only in %s:\n%s" % (sdir, "\n".join(si[sitop]["only_in"])))
        if si[sitop]["oi_prefix"]:
            sdir = si[sitop]["sdir"]
            other_dir = si[get_inv_top(sitop)]["sdir"]
            for prefix in si[sitop]["oi_prefix"]:
                print(("Ignoring directory '%s' because it's only in '%s'"
                    " (%i files) but not in '%s'.") % (prefix, sdir, 
                    len(si[sitop]["oi_prefix"][prefix]), other_dir))
                # Only in prefix %s:\n%s" % (sdir, "\n".join(si[sitop]["oi_prefix"])))

    # display messages about test files
    if len(si["curr"]["tf_only_in"]) > 0 or len(si["orig"]["tf_only_in"]) > 0:
        print ("Ignoring following test files because they are not common to both '%s' and '%s':" % (
           si["curr"]["sdir"], si["orig"]["sdir"]))
        if len(si["curr"]["tf_only_in"]) > 0:
            print("%s" % format_list_lines("Only in %s (%i)" % (si["curr"]["sdir"],
                len(si["curr"]["tf_only_in"])), si["curr"]["tf_only_in"]))
        if len(si["orig"]["tf_only_in"]) > 0:
            print("%s" % format_list_lines("Only in %s (%i)" % (si["orig"]["sdir"],
                len(si["orig"]["tf_only_in"])), si["orig"]["tf_only_in"]))
    if len(si["common_tf"]) > 0:
        print("Including %i test files that are common to '%s' and '%s'." % (len(si["common_tf"]),
            si["curr"]["sdir"], si["orig"]["sdir"]))
    # check only_in other than test files.  If any, they are differences
    for sitop in ("curr", "orig"):
        if si[sitop]["only_in"]:
            sdir = si[sitop]["sdir"]
            diffs.append("Only in %s:\n%s" % (sdir, "\n".join(si[sitop]["only_in"])))
#         if si[sitop]["oi_prefix"]:
#             sdir = si[sitop]["sdir"]
#             diffs.append("Only in prefix %s:\n%s" % (sdir, "\n".join(si[sitop]["oi_prefix"])))


    # display information about test files
#     if si[sitop]["tf_only_in"]:
#         print ("%i test files only in %s:\n%s" % (len(si[sitop]["tf_only_in"]),
#            si[sitop]["sdir"], "\n".join(si[sitop]["tf_only_in"])))
#     print("%s test files in both %s and %s:" % (len(si["common_tf"]), si["curr"]["sdir"],
#         si["orig"]["sdir"]))
#     print("%s" % "\n".join(si["common_tf"]))
    diff_hashes = []
    assert sorted(list(si["curr"]["sigs"])) == sorted(list(si["orig"]["sigs"]))
    for path in sorted(list(si["curr"]["sigs"])):
        hash_curr = si["curr"]["sigs"][path]
        hash_orig = si["curr"]["sigs"][path]
        if hash_curr != hash_orig:
            diff_hashes.append(path)
    if diff_hashes:
        msg = "%i files in both, but hashes different:\n%s" % (len(diff_hashes),
            "\n".join(diff_hashes))
        diffs.append(msg)
    # check consistency between files in the same top dir, e.g. between
    # matlab and python hdf5 files
    diffs.extend(check_consistency())
    if diffs:
        print ("Differences found:\n%s" % "\n".join(diffs))
        return diffs
    else:
        print("All paired files (%i) match." % len(sorted(list(si["curr"]["sigs"]))))
        print("Consistency check counts are:")
        for key in sorted(cc_check_count):
            print("%s - %i" % (key, cc_check_count[key]))
        return None


if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Too many input parameters: %i" % len(sys.argv))
        display_doc()
        sys.exit(1)
    si["curr"]["sdir"] = sys.argv[1] if len(sys.argv) > 1 else "curr"
    si["orig"]["sdir"] = sys.argv[2] if len(sys.argv) > 1 else "orig"
    load_contents()
    build_si()
    diff = find_diff()
    if diff is None:
        print ("Signature files match.")
        sys.exit(0)
    else:
        sys.exit(1)


### Original code: scratch

#  
# # name of signature file
# sig_file_name = "dirsig.txt"
# # name of directory containing nwb_test_samples (may not be present):
# test_files_dir = "nwb_test_samples"
# # global variable for storing dictionary of file_names => signatures
# # sigs = {"curr": {}, "orig": {}}
# 
# # global structure storing all signature information
# si = {"curr": {
#         "sigs": {},        # map file path to signature
#         "only_in": [],     # names of files only in curr (but not nwb_test_files)
#         "tf_only_in": []   # names of nwb_test_files that are only in curr
#          }, {
#         "sigs": {},        # map file path to signature
#         "only_in": [],     # names of files only in curr (but not nwb_test_files)
#         "tf_only_in": []   # names of nwb_test_files that are only in curr
# }}         
# 
# 
# def display_doc():
#     print ("Format is:")
#     print ("python %s [<curr> [<orig>] ]" % sys.argv[0])
#     print ("Where:")
#     print ("   <curr> is a directory containing the signiture file (dirsig.txt)")
#     print ("          for the current installation.  Default is 'curr'.")
#     print ("   <orig> is a directory containing the signature file for the reference")
#     print ("          installation.  Default is 'orig'.")
# 
# def load_sig(sig_dir, desc):
#     # load contents of signature file in directory sig_dir, described by desc
#     global sig_file_name
#     sig_path = os.path.join(sig_dir, sig_file_name)
#     if not os.path.isfile(sig_path):
#         print ("'%s' file not found at: %s" % (desc, sig_path))
#         display_doc()
#         sys.exit(1)
#     f = open(sig_path)
#     contents = f.read()
#     f.close()
#     return contents
# 
# def has_nwb_test_files(contents):
#     # return True if string contents contains signatures for nwb test files otherwise False
#     global test_files_dir
#     pattern = "\n[a-zA-Z]{6} %s/" % test_files_dir
#     match = re.search(pattern, contents)
#     return match is not None
#     
# def yesno(val):
#     assert isinstance(val, bool)
#     msg = "Yes" if val else "No"
#     return msg
# 
# 
# # def get_test_file_status(curr_contents, curr_dir, orig_contents, orig_dir):
# #     # Return True if both curr_contents and orig_contents contain nwb test file results
# #     # return False otherwise.  Also display a message indicating which files have the
# #     # test file results.
# #     global test_files_dir
# #     curr_has_nwb_test = has_nwb_test_files(curr_contents)
# #     orig_has_nwb_test = has_nwb_test_files(orig_contents)
# #     msg1 = ("Contains %s: %s -%s, %s -%s" % (test_files_dir, curr_dir, yesno(curr_has_nwb_test),
# #         orig_dir, yesno(orig_has_nwb_test)))
# #     check_nwb_test_files = curr_has_nwb_test and orig_has_nwb_test
# #     msg2 = "(%s %s)" % ("Including" if check_nwb_test_files else "Not including", test_files_dir)
# #     msg = "%s; %s" % (msg1, msg2)
# #     print (msg)
# #     return check_nwb_test_files
# 
# def build_sigs(sdir, contents):
#     # build dictionary of file names => signatures for directory sdir
#     # contents is raw text contents of file for sdir
#     global sigs
#     global test_files_dir
#     assert sdir in ('curr', 'orig')
#     lines = contents.splitlines()
#     pattern = "([a-zA-Z]{6}) (.*)"
#     test_files_pattern = "%s/" % test_files_dir  # append slash
#     for line in lines:
#         match = re.match(pattern, line)
#         if not match:
#             sys.exit("Unable to match hash and file path in %s: %s" % (sdir, line))
#         hash = match.group(1)
#         path = match.group(2)
#         # save the path and signature
#         assert path not in sigs[sdir]
#         sigs[sdir][path] = hash
# 
# def find_diff(curr_dir, orig_dir):
#     global sigs, test_files_dir
#     in_curr = set(sigs['curr'].keys())
#     in_orig = set(sigs['orig'].keys())
#     only_in_curr = in_curr - in_orig
#     only_in_orig = in_orig - in_curr
#     
#     test_files_dirp = "%s/" % test_files_dir  # append slash
#     test_files_only_in_curr = set([ x for x in only_in_curr if x.startwith(test_files_dirp)])
#     test_files_only_in_orig = set([ x for x in only_in_orig if x.startwith(test_files_dirp)])
#     # remove test files from only_in sets, since these will be ignored
#     only_in_curr = sorted(list(only_in_curr - test_files_only_in_curr))
#     only_in_orig = sorted(list(only_in_orig - test_files_only_in_orig))
#     # get names of test files that are not matched (in both curr and orig)
#     tf_names = set([])
#     pattern = "/%s/(validate|h5sig)/(.+)" % test_files_dir
#     for path in test_files_only_in_curr:
#         match = re.match(pattern, path)
#         if not match:
#             sys.exit("could not match: %s" % path)
#         tf_name = match.group(1)
#         tf_names.add(tf_name)
#     
#    
# 
# #     only_in_curr = list(in_curr - in_orig)
# #     only_in_orig = list(in_orig - in_curr)
#     
#     #         if not check_nwb_test_files and path.startswith(test_files_pattern):
# #             # don't save this path, it's for a nwb_test file, and those are not being checked
# #             continue
# 
#     diffs = []
#     if only_in_curr:
#         diffs.append("Only in %s:\n%s" % (curr_dir, "\n".join(sorted(only_in_curr))))
#     if only_in_orig:
#         diffs.append("Only in %s:\n%s" % (orig_dir, "\n".join(sorted(only_in_orig))))
#     common = sorted(list(in_curr.intersection(in_orig)))
#     num_files = len(only_in_curr) + len(only_in_orig) + len(common)
#     diff_hashes = []
#     for path in common:
#         hash_curr = sigs['curr'][path]
#         hash_orig = sigs['orig'][path]
#         if hash_curr != hash_orig:
#             diff_hashes.append(path)
#     if diff_hashes:
#         msg = "%i files in both, but hashes different:\n%s" % (len(diff_hashes),
#             "\n".join(diff_hashes))
#         diffs.append(msg)
#     if diffs:
#         print "Differences found:\n%s" % "\n".join(diffs)
#         return diffs
#     else:
#         return None
# 
# if __name__ == "__main__":
#     if len(sys.argv) > 3:
#         print("Too many input parameters: %i" % len(sys.argv))
#         display_doc()
#         sys.exit(1)
#     curr_dir = sys.argv[1] if len(sys.argv) > 1 else "curr"
#     orig_dir = sys.argv[2] if len(sys.argv) > 1 else "orig"
#     curr_contents = load_sig(curr_dir, "curr")
#     orig_contents = load_sig(orig_dir, "orig")
#     # check_nwb_test_files = get_test_file_status(curr_contents, curr_dir, orig_contents, orig_dir)
#     build_sigs("curr", curr_contents)
#     build_sigs("orig", orig_contents)
#     diff = find_diff(curr_dir, orig_dir)
#     if diff is None:
#         print "Signature files match."
#         sys.exit(0)
#     else:
#         sys.exit(1)






