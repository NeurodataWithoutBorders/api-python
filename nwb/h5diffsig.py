# find differences between hdf5 files
# also generate signature of values


import re
import sys
import h5py
# import copy
import numpy as np
import zlib
from operator import itemgetter
# import combine_messages as cm
from . import combine_messages as cm
# from . import find_links
from . import value_summary as vs

from sys import version_info  # py3

import pprint
pp = pprint.PrettyPrinter(indent=4)


def display_doc():
    print ("Usage: %s <file1> [<file2>] [<opts>]" % sys.argv[0])
    print ("where: <file1> first file to compare")
    print ("       <file2> second file to compare, or empty, to generate 'signature' for <file1>")
    print ("       <opts> is a string starting with '-', followed by any of: 'N', 'a'.  These are:")
    print ("          'N' - filter signature output to allow matching NWB files.")
    print ("              Filtering removes or places characters '<%' and '%>' around the output of the")
    print ("              command lines and the the datasets which are likely to vary across NWB")
    print ("              files, e.g.: /identifier, /file_create_date, ")
    print ("              general/specifications/nwb_core.py.  Text in these <%  %> 'comments'")
    print ("              can be removed before creating a hash of the files or comparing files,")
    print ("              so these parts will not prevent matches.")
    print ("          'a' - Sort output of matching items alphabetically instead of by size")
    print ("              This useful for signatures because it prevents output lines")
    print ("              getting out of order between files due to differences in the sizes")
    print ("              of a dataset or attribute.")



# py3, set unicode to str if using Python 3 (which does not have unicode class)
try:
    unicode
except NameError:
    unicode = str

# py3, convert unicode string to bytes
def make_bytes(value):
    if isinstance(value, unicode):
        value = value.encode('utf8')
    return value
    
# py3, convert list of strings to list of bytes
# def make_bytes_list(alist):
#     assert isinstance(alist, list)
#     return [make_bytes(v) for v in alist]

# py3, convert list of bytes to list of strings
def make_str_list(alist):
    assert isinstance(alist, (list, tuple)), "parameter must be tuple, is: %s" % type(alist)
    return [v.decode('utf-8') for v in alist]

# py3, convert bytes to strings, including if in a list or tuple
# def make_str(val):
#     if version_info[0] > 2:
#         base_val = get_base_val(val)
#         if isinstance(base_val,  bytes):
#             val = make_str2(val)
#     return val

# def make_str(val):
#     return find_links.make_str(val)

# def make_str_old(val):
#     base_val = get_base_val(val)
#     if isinstance(base_val,  bytes):
#         val = make_str2(val)
#     return val

# recursive convert everything from bytes to str (unicode) for Python 3
# convert numpy ndarray to list if has str as base_val even if python 2
# this done so output from python2 and python3 will be identical because
# str(numpy.ndarray) does not have commas in the generated string,
# while str(list) does
# def make_str2_old(val):
#     if isinstance(val, (list, tuple, np.ndarray)) and len(val) > 0:
#         return [make_str2(v) for v in val]
#     elif isinstance(val, bytes) and version_info[0] > 2:
#         try:
#             vald = val.decode('utf-8')
#         except UnicodeEncodeError as e:
#             import pdb; pdb.set_trace()
#         return val.decode('utf-8')
#     else:
#         return val
    
# print nested dictionary with keys ordered alphabetically
# this written because pprint pformat gives different output for Python2 and Python3
def ppdict(hash):
    if isinstance(hash, dict):
        parts = []
        for key in sorted(list(hash)):
            value = ppdict(hash[key])
            parts.append('"%s":%s' % (key, value))
        return "{" + ", ".join(parts) + "}"
    elif isinstance(hash, str):
        return '"%s"' % hash
    else:
        return hash

# get a scalar value, either from scalar or from list or tuple
# def get_base_val(val):
#     if isinstance(val, (list, tuple, np.ndarray)) and len(val) > 0:
#         return get_base_val(val[0])
#     else:
#         return val

# global variables for file handles
# f1 = f2 = None



# class File(object):
#     """ hdf5 file """
#     def __init__(self, fname):
#         """ Open hdf5 file.  fname - name of file
#         This class created so it has the same members as the h5gate.File classs
#         that are used in value_summary; mainly; error, warning, file_pointer.
#         """
#         try:
#             f = h5py.File(file1, 'r')
#         except IOError:
#             print ("Unable to open file '%s'" % file1)
#             display_doc()
#             sys.exit(1)
#         self.file_name = fname
#         self.error =[]
#         self.warning = []
#         self.file_pointer = f
# 
#         (value_sum, vs_msg, vs_msg_type) = vs.make_value_summary(val, self.file.file_pointer)
      
# # tally all types (used for debugging, testing)
# ttypes = {}
# tetypes = {}  # shortest examples
# def tally_types(path, aid, val):
#     global ttypes
#     base_val = vs.get_base_val(val)
#     if not vs.is_str_type(base_val):
#         return
#     typ = str(type(val))
#     base_typ = str(type(base_val))
#     typ = "%s==%s" % (typ, base_typ)
#     flags="unicode=%s,bytes=%s" % (isinstance(base_val, unicode), isinstance(base_val, bytes))
#     length = len(val)
#     val_string = vs.make_value_summary(val)
#     if typ in ttypes:
#         ttypes[typ] += 1
#         if length > 1:
#             prev_len = tetypes[typ][0]
#             if length < prev_len:
#                 tetypes[typ] = (length, path, aid, val, flags, val_string)
#     elif length > 1:
#         ttypes[typ] = 1
#         tetypes[typ] = (length, path, aid, val, flags, val_string)

# def is_str_type(val):
#     """ Return True if val is a string type """
#     return isinstance(val, (bytes, unicode, np.string_, np.bytes_, np.unicode))

# def val2str(val):
#     # return string representation of value which is consistent in Python2 and Python3
#     lval = lmake_str(val)
#     val_str = str(lval)
#     return val_str
    
#     if 'Behavioral testing' in val:
#         import pdb; pdb.set_trace()
#     val_str = str(uval)
#     try:
#         val_str = str(uval)
#     except UnicodeEncodeError as e:
#         if isinstance(uval, unicode):
#             val_str = uval.encode('utf-8')
#         else:
#             print ("unable to perform str function on type %s, value:" % type(uval))
#             print (uval)
#             import pdb; pdb.set_trace()
#     # val_str = str(make_str(val))  # py3, make unicode for combine_messages
#     if len(val_str) > 40:
#         val_str = val_str[0:40]+"..." + hashval(val_str[40:])
# #     if '2017-01-17T14:56:06.203565' in val_str:
# #         import pdb; pdb.set_trace()
#     return val_str   


# def lmake_str(val):
#     base_v = get_base_val(val)
#     if isinstance(base_v,  (bytes, unicode)):
#         # convert ndarray to list, py2 strings to bytes, py3 strings to unicode
#         val = lmake_str2(val)
#     return val

# recursive convert everything from bytes to str (unicode) for Python 3
# convert numpy ndarray to list if has str as base_val even if python 2
# this done so output from python2 and python3 will be identical because
# str(numpy.ndarray) does not have commas in the generated string,
# while str(list) does
# def lmake_str2(val):
#     if isinstance(val, (list, tuple, np.ndarray)) and len(val) > 0:
#         return [lmake_str2(v) for v in val]
#     elif isinstance(val, bytes) and version_info[0] > 2:
#         try:
#             uval = val.decode('utf-8')
#         except UnicodeDecodeError as e:
#             # value is a binary string.
#             hash = hashval(val)
#             bmsg = "<<raw binary, hash=%s>>" % hash
#             return bmsg
#         return uval
#     elif isinstance(val, unicode) and version_info[0] < 3:
#         val = val.encode('utf-8')
#     elif isinstance(val, bytes) and version_info[0] < 3:
#         # data in correct format, but make sure it's printable
#         try:
#             uval = val.decode('utf-8')
#         except UnicodeDecodeError as e:
#             # value is a binary string.
#             hash = hashval(val)
#             val = "<<raw binary, hash=%s>>" % hash       
#     return val

def error_exit(msg = None):
    if msg:
        print("** Error: %s" % msg)
    print("Stack trace follows")
    print("-------------------")
    # import pdb
    # pdb.set_trace()
    traceback.print_stack()
    sys.exit(1)

# datasets that are likely to vary across NWB files.  The value, size and dtype are
# filtered out if NWB filter ("N") option is specified.
nwb_variable_datasets = ("/file_create_date", "/identifier",
    "/general/specifications/nwb_core.py", "/session_start_time",
    "/general/source_script", "/nwb_version")
# attributes likely to change across NWB files.  List of tuples: path, attribute name
nwb_variable_attributes = (("/general/source_script", "file_name"),  )

# 
# # convert an integer to an string of letters
# # this done so hashes are all letters and thus not used by function combine_messages 
# def int2alph(val):
#     assert isinstance(val, int)
#     alph = []
#     num_chars = 52  # a-z, A-Z
#     while val > 0:
#         val, r = divmod(val, num_chars)
#         new_char = chr(r + ord('a')) if r < 26 else chr(r - 26 + ord('A'))
#         alph.append(new_char)
#     strval = "".join(reversed(alph))
#     return (strval)
       
# # make a hash of value
# def hashval(val):
#     if isinstance(val, unicode):
#         val = val.encode('utf-8')
#     else:
#         assert isinstance(val, bytes)
#     crc = zlib.adler32(val) & 0xffffffff
#     hash = int2alph(crc)
#     return hash

# def reverse_dict(din):
#     dout = {}
#     for key in din:
#         val = din[key]
#         if val in dout:
#             dout[val].append(key)
#         else:
#             dout[val]= [key]
#     return dout


def make_full_path(path, name):
    """ Combine path and name to make full path"""
    # path = make_bytes(path)  #py3, this added for python3, path must be bytes, not unicode
    # import pdb; pdb.set_trace()
    name = name.decode('utf-8')  #py3, added name will be byte string and combine_messages is always expecting unicode
    if path == "/":  #py3, added b
       # full_path = b"/" + name  #py3, added b
       full_path = "/%s" % name  #py3, use format instead of +
    else:
        # assert not path.endswith(b'/'), "non-root path ends with '/' (%s)" % path #py3, added b
        assert not path.endswith('/'), "non-root path ends with '/' (%s)" % path
        # assert not path[-1] == '/', "non-root path ends with '/' (%s)" % path #py3, change to check last char
        # full_path = path + b"/" + name  #py3, added b
        full_path = "%s/%s" % (path, name) #py3, use format instead of +
    # remove any duplicate slashes, should be unnecessary
    # full_path = re.sub(r'//+',r'/', full_path)
#     print ("path=%s, name=%s, full_path=%s" % (path, name, full_path))
#     import pdb; pdb.set_trace()
    return full_path

# def values_match(x, y):
#     # call function in find_links
#     return find_links.values_match(x, y)


# def values_match_old(x, y):
#     """ Compare x and y.  This needed because the types are unpredictable and sometimes
#     a ValueError is thrown when trying to compare.  Also, if any value has NaN, then
#     the value will not match itself if doing a normal comparison.
#     """
#     # convert to matching types (unicode) if one is unicode and the other bytes
#     if isinstance(x, bytes) and isinstance(y, unicode):
#         x = x.decode('utf-8')
#     elif isinstance(x, unicode) and isinstance(y, bytes):
#         y = y.decode('utf-8')
#     if x is y:
#         return True
#     # compare arrays so corresponding NaN values are treated as a match
#     if (isinstance(x, np.ndarray) and isinstance(y, np.ndarray)
#         and np.issubdtype(x.dtype, np.float) and np.issubdtype(y.dtype, np.float)):
#         # from: http://stackoverflow.com/questions/10710328/comparing-numpy-arrays-containing-nan
#         try:
#             np.testing.assert_equal(x,y)
#         except AssertionError:
#             return False
#         return True
#     # check for two scalar NaN.  If found, treat as match
#     if (np.issubdtype(type(x), np.float) and np.issubdtype(type(y), np.float)
#         # and x.shape == () and y.shape == ()
#         and np.isnan(x) and np.isnan(y)):
#         return True
#     try:
#         eq = x==y
#     except ValueError:
#         # ValueError: shape mismatch: objects cannot be broadcast to a single shape
#         return False
#     if isinstance(eq, bool):
#         return eq
#     return eq.all()
    
def values_close(x, y):
    if (isinstance(x, np.ndarray) and isinstance(y, np.ndarray)
        and np.issubdtype(x.dtype, np.float)
        and np.issubdtype(y.dtype, np.float)
        and x.shape == y.shape):
        close = np.isclose(x, y)
        if isinstance(close, bool):
            return close
        return close.all()
    else:
        return False


def save_to_dict_array(da, key, value):
    if key not in da:
        da[key] = [value]
    else:
        da[key].append(value)
        


h5_ntypes = {    # hdf5 node types, from: http://api.h5py.org/h5g.html
    h5py.h5g.LINK: 'link',
    h5py.h5g.GROUP: 'group',
    h5py.h5g.DATASET: 'dataset',
    h5py.h5g.TYPE: 'type',
    4: 'ext_link'  # a guess
}


# def get_sorted_members(h5g):
#     # return list of tuples (object index, object name) sorted according to object name.
#     # This done so objects are processed in the same order
#     # Step 1 - get list of tuples, (id, name)
#     members = []
#     for i in range(h5g.get_num_objs()):
#         mname = h5g.get_objname_by_idx(i)
#         members.append( (i, mname) )
#     # Step 2, sort list by member name
#     members = sorted(members,key=itemgetter(1))
#     return members
        

# creates and returns a summary description for every element in a group
def get_group_info(path, grp):
    global h5_ntypes
    gi = {}
    # get group id used for low-level h5py api
    h5g = grp.id
    # members = get_sorted_members(h5g)
    # for i in range(len(members)):
        # idx, mname = members[i]
        # mtype = h5_ntypes[h5g.get_objtype_by_idx(idx)]
    for i in range(h5g.get_num_objs()):
        mname = h5g.get_objname_by_idx(i)
        mtype = h5_ntypes[h5g.get_objtype_by_idx(i)]
        try:
            minfo = h5py.h5g.get_objinfo(h5g, mname)
        except TypeError:
            objno = "ext_link:dangling"  # make a fake object number
        else:
            objno = minfo.objno
            # remove 'L' if python 2, e.g. (15760L, 0L) => (15760, 0)
            objno = (int(objno[0]), int(objno[1])) 
        if mtype == 'link':
            # target of symbolic link
            target = h5g.get_linkval(mname)
            # get target type
            if target not in grp.file:
                # must be dangling link
                ttype = None
            else:
                tnode = grp.file[target]
                ttype = "dataset" if isinstance(tnode, h5py.Dataset) else "group"
            target = target.decode('utf-8') #py3, convert to unicode for combine messages
        elif mtype == 'ext_link':
            # target of external link
            try:
                target = "\n".join(make_str_list(h5g.links.get_val(mname)))  #py3, convert list to unicode
                # target = "\n".join(h5g.links.get_val(mname))
            except TypeError as e:
                # import pdb; pdb.set_trace()
                error_exit("could not get ext_link")
            ttype = None
        else:
            target = None
            ttype = None   
        full_path = make_full_path(path, mname)
        desc = {"type": mtype, 'objno': objno, 'full_path': full_path, 'target':target, 'ttype': ttype}
        if mtype == 'dataset':
            mh5d = h5py.h5d.open(h5g, mname)
            desc['dtype'] = mh5d.dtype
            # TODO: extract and display object type and other object-specific information
            # if str(mh5d.dtype) == "object":
            #    import pdb; pdb.set_trace()
            desc['shape'] = mh5d.shape
            desc['rank'] = mh5d.rank
            desc['size'] = mh5d.get_storage_size()
            desc['compression'] = grp[mname].compression
            # print "need to get compression for dataset"
            # import pdb; pdb.set_trace()
        gi[mname] = desc
    return gi
    
# return attribute information
def get_attr_info(node, path):
    ai = {}
    # get object_id used for h5py low-level interface
    nid = node.id
    for name in node.attrs.keys():
        # name = make_bytes(name)  #py3, this added for python3, path must be bytes, not unicode
        try:
            # aid = h5py.h5a.open(nid, name=name)
            aid = h5py.h5a.open(nid, name=make_bytes(name)) #py3
        except TypeError as e:
            error_exit("Could not get attribute_id")
        # aid = h5py.h5a.open(nid, name=name)
        dtype = aid.dtype
        size = aid.get_storage_size()
        shape = aid.shape
        type = 'attribute'
        desc = {'type':type, 'dtype':dtype, 'size':size, 'full_path': path, 'shape':shape}
        ai[name] = desc
    return ai
    
def sort_by_size(messages):
    # Sort messages in descending order based on the size of the dataset or
    # attribute specified in the substring "size (n)
    def get_ad_size(message):
        match = re.search(" size \((\d+)\)", message)
        assert match, "could not find size in %s" % message
        size = int(match.group(1))
        return size
    messages.sort(key=lambda x: get_ad_size(x), reverse=True) 

def h_combine_messages(messages, description):
    """ combine messages; return combined messages and header"""
    cmsg = cm.combine_messages(messages)
    if len(cmsg) != len(messages):
        header = "%i %s (%i combined):" %(len(messages), description, len(cmsg))
    else:
        header = "%i %s:" % (len(messages), description)
    cmsg.insert(0, header)
    return cmsg
 

def find_hard_links():
    # search ci["locations"] for locations with multiple entries
    # if found, copy them to ci["hard_links_found"]
    global ci
    for ab in ("A", "B"):
        for loc in sorted(list(ci["locations"][ab])):
            nodes = ci["locations"][ab][loc]
            if len(nodes) > 1:
                # found one or more hard links
                paths = []
                type = None
                for node in nodes:
                    path, typ = node
                    if not type:
                        type = typ
                    else:
                        assert type == typ
                    paths.append(path)
                pathsc = h_combine_messages(paths, type + "s")
                # want output like
                #  1. id=(343, 3443).  34 groups (3 combined):
                pathsc[0] = "id=%s. %s" % (loc, pathsc[0])
                msg = "\n\t".join(pathsc)
                ci["hard_links"][ab][type].append(msg)


def save_soft_link(ab, cim):
    # cim is the dict created for members of group by function 
    # get_group_info.  If this is a link (i.e. hdf5 soft link or ext_link)
    # save information about the link in ci.
    # ab is either "A" or "B"
    global ci
    if cim['type'] not in ("link", "ext_link"):
        return
    full_path = cim['full_path']
    target = cim['target']
    # msg = "%s: %s => %s" % (cim['type'], full_path, target)
    if cim['type'] == "link":
        target_type = cim['ttype'] if cim['ttype'] else "unknown"
        if target in ci["tmp_soft_links"][ab][target_type]:
            ci["tmp_soft_links"][ab][target_type][target].append(full_path)
        else:
            ci["tmp_soft_links"][ab][target_type][target] = [full_path]
    else:
        msg = "%s: %s => %s" % (cim['type'], full_path, target)
        ci["ext_links"][ab].append(msg)
    return

def format_soft_links():
    # Convert soft_links from a dictionary of targets: [paths] in tmp_soft_links
    # to text representing that in ci["soft_links"]
    for ab in ("A", "B"):
        for type in ci["tmp_soft_links"][ab]:
            dmsg = ci["soft_links"][ab][type]  # destination for messages
            for target in sorted(ci["tmp_soft_links"][ab][type].keys()):
                paths = ci["tmp_soft_links"][ab][type][target]
                pathsc = h_combine_messages(paths, type + "s")
                # want output like
                # to: "target" 200 groups (3 combined):
                try:
                    # pathsc[0] = b"to: \"%s\" %s" % (target, pathsc[0].encode('utf8'))  #py3, added b, .encode('utf8')
                    pathsc[0] = "to: \"%s\" %s" % (target, pathsc[0])
                    # msg = b"\n\t".join(pathsc)  #py3, added b
                    msg = "\n\t".join(pathsc)
                except TypeError as e:
                    error_exit("unable to format_soft_links")
                dmsg.append(msg)
  
def check_link_equivalence():
    # checks to be sure that groups formed by links (hard or soft) are
    # equivalent
    global single_file
    errors = []
    num_link_groups = {"A": {"hard": {"group": 0, "dataset": 0}, "soft": {"group": 0, "dataset": 0}},
                      "B": {"hard": {"group": 0, "dataset": 0}, "soft": {"group": 0, "dataset": 0}}}
    for source_ab in ("A", "B"):
        dest_ba = "B" if source_ab is "A" else "A"
        for hard_loc in sorted(list(ci["locations"][source_ab])):
            hard_group_paths, type = get_hard_group_paths(source_ab, hard_loc)
            if hard_group_paths:
                num_link_groups[source_ab]["hard"][type] += 1
                validate_group(source_ab, "hard", type, hard_group_paths, dest_ba, errors)
        for target_type in ("group", "dataset"):
            for target in ci["tmp_soft_links"][source_ab][target_type]:
                num_link_groups[source_ab]["soft"][target_type] += 1
                soft_group_paths = [target] + ci["tmp_soft_links"][source_ab][target_type][target]
                validate_group(source_ab, "soft", target_type, soft_group_paths, dest_ba, errors)
    if errors:
        print ("%s" % ("** Above links are NOT equivalent:\n\t" + "\n\t".join(errors)))
    else:
        nlg = num_link_groups
        total_found = (nlg["A"]["hard"]["group"] + nlg["A"]["hard"]["dataset"] +
            nlg["A"]["soft"]["group"] + nlg["A"]["soft"]["dataset"] +
            nlg["B"]["hard"]["group"] + nlg["B"]["hard"]["dataset"] + 
            nlg["B"]["soft"]["group"] + nlg["B"]["soft"]["dataset"])
        if total_found == 0:
            print ("** No links found.")
        else:
            print ("** Above found links are equivalent. -- Good.\n   Total of %i link groups found:\n   %s" %(
                total_found, ppdict(num_link_groups)))
                # total_found, pp.pformat(num_link_groups)))
                # str(num_link_groups)))  # prev version, would not sort keys
        if not single_file:
            print (("   Note: links inside unpaired groups will not be found.  To guarantee "
                "finding all links, run script with just one file (comparing it to itself)."))
                
                
def validate_group(source_ab, source_link_type, type, paths, dest_ba, errors):
    """ make sure that all paths in paths are in a group in dest_ba and that
    the type (group or dataset) matches"""
    # pick any path for searching
    path = paths[0]
    # look for path in hard link group
    for hard_loc in sorted(list(ci["locations"][dest_ba])):
        hard_group_paths, hl_type = get_hard_group_paths(dest_ba, hard_loc)
        if hard_group_paths and hl_type == type and path in hard_group_paths:
            validate_groups_match(source_ab, source_link_type, type, paths, dest_ba, errors, 
                hard_group_paths, "hard")
            return
    # look for path in soft link group
    for target in ci["tmp_soft_links"][dest_ba][type].keys():
        soft_group_paths = [target] + ci["tmp_soft_links"][dest_ba][type][target]
        if path in soft_group_paths:
            validate_groups_match(source_ab, source_link_type, type, paths, dest_ba, errors, 
                soft_group_paths, "soft")
            return
    msg = "Unable to find links in %s matching %s in %s with path='%s'" % (
        dest_ba, type, source_ab, path)
    errors.append(msg)
    
def validate_groups_match(source_ab, source_link_type, type, source_paths, dest_ba, errors, 
                dest_paths, dest_link_type):
    sp = set(source_paths)
    dp = set(dest_paths)
    if sp != dp:
        msg = ("set for %s link in %s not equivalent to set for %s link in %s; type=%s.\n"
            "%s paths=%s\n%s paths=%s") % (source_link_type, source_ab, dest_link_type, dest_ba,
            type, source_ab, source_paths, dest_ba, dest_paths)
        errors.append(msg)
        
def get_hard_group_paths(ab, loc):
    """get list of paths at loc and also type if more than one path, otherwise
    return tuple (None, None)"""
    nodes = ci["locations"][ab][loc]
    if len(nodes) == 1:
        # no hard links to this location
        return (None, None)
    # found one or more hard links
    paths = []
    type = None
    for node in nodes:
        path, typ = node
        if not type:
            type = typ
        else:
            assert type == typ
        paths.append(path)
    return (paths, type)


# Initialize "compare info" (ci) structure
def initialize_ci():
    global ci
    ci = {
        "only_in": {
            "A": {"group": [], "dataset": [], "attribute": [], "other": []},
            "B": {"group": [], "dataset": [], "attribute": [], "other": []}},
        "node_types_different": [],  # e.g. group vs. dataset
        "hard_links": {
            "A": {"group": [], "dataset": []}, 
            "B": {"group": [], "dataset": []}},
        "tmp_soft_links": {  # for storing as target: [], not displayed
            "A": {"group": {}, "dataset": {}, "unknown": {}}, 
            "B": {"group": {}, "dataset": {}, "unknown": {}}},
        "soft_links": {
            "A": {"group": [], "dataset": [], "unknown": []}, 
            "B": {"group": [], "dataset": [], "unknown": []}},
        "ext_links": { "A":[], "B":[] },
        "unknown_node_types": [],
        "types_differ_values_same": { "dataset": [], "attribute": []},
        "types_same_values_differ": { "dataset": [], "attribute": []},     
        "values_and_types_differ": { "dataset": [], "attribute": []},
        "everything_matches": { "dataset": [], "attribute": []},
        "total_paired_found": { "group": 0, "dataset": 0, "attribute": 0}, # counts only
        "empty_paired_groups": [],
        "only_compressed_in": { "A": [], "B": []},
        "values_match_but_sizes_different": {"dataset": [], "attribute": []},
        # has: loc: [(path1, type1), (path2, type2), ...], loc: [ ...], ...]
        "locations": { "A": {}, "B": {} },
        # has: loc: size, loc: size (only for datasets)
        # sizes not currently used
        # "sizes": { "A": {}, "B": {} },
        "warning": [],
        "error": []
    }

def da_empty(da):
    """Returns True if all elements of dict da have values that are
    lists, and all of these lists are empty.  This done to verify
    that when using single_file mode, ci values, such as:
    ci['only_in']['A']['dataset'], ci['only_in']['B']['group'])
    do not have values."""
    for key in da:
       val = da[key]
       if (not isinstance(val, list)) or len(val) > 0:
           return False
    return True

  
def display_report():
    global ci, alpha_sort
    find_hard_links()
    format_soft_links()
    if single_file:
        # don't display these, should be empty if single file:
        assert da_empty(ci['only_in']['A'])
        assert da_empty(ci['only_in']['B'])
        assert len(ci["node_types_different"]) == 0
    else:
        display_sub_messages(ci['only_in']['A'], "only in A", zero_msg="Good")
        display_sub_messages(ci['only_in']['B'], "only in B", zero_msg="Good")
        display_messages(ci["node_types_different"], "node types differ", zero_msg="Good")
    # don't combine links, these already combined
    if single_file:
        display_sub_messages(ci["hard_links"]['A'], "hard links", combine=False)
        display_sub_messages(ci["soft_links"]['A'], "soft links", combine=False)
        display_messages(ci["ext_links"]['A'], "ext_links")
        display_messages(ci["unknown_node_types"], "unknown node types", zero_msg="Good")
    else:
        display_sub_messages(ci["hard_links"]['A'], "hard links in A", combine=False)
        display_sub_messages(ci["hard_links"]['B'], "hard links in B", combine=False)
        display_sub_messages(ci["soft_links"]['A'], "soft links in A", combine=False)
        display_sub_messages(ci["soft_links"]['B'], "soft links in B", combine=False)
        check_link_equivalence()
        display_messages(ci["ext_links"]['A'], "ext_links in A")
        display_messages(ci["ext_links"]['B'], "ext_links in B") 
        display_messages(ci["unknown_node_types"], "unknown node types (in both A and B)", zero_msg="Good")
    if alpha_sort:
        # sort by name
       ci["everything_matches"]['attribute'].sort()
       ci["everything_matches"]['dataset'].sort()
       sort_msg = "sorted alphabetically"
    else:
        # sort by size in decreasing order
        sort_by_size(ci["everything_matches"]['attribute'])
        sort_by_size(ci["everything_matches"]['dataset'])
        sort_msg = "sorted in decreasing size"
    ci["empty_paired_groups"].sort()
    if single_file:
        assert da_empty(ci["types_same_values_differ"])
        assert da_empty(ci["types_differ_values_same"])
        assert da_empty(ci["values_and_types_differ"])
        assert da_empty(ci["values_match_but_sizes_different"])
        display_messages(ci["empty_paired_groups"], "empty groups (no members or attributes)")     
        display_sub_messages(ci["everything_matches"], "(%s)" % sort_msg)
    else:
        display_messages(ci["empty_paired_groups"], "empty paired groups (no members or attributes)")
        display_sub_messages(ci["types_same_values_differ"], "types match but values differ")
        display_sub_messages(ci["types_differ_values_same"], "types differ but values match")
        display_sub_messages(ci["values_and_types_differ"], "values and types differ")
        display_messages(ci["only_compressed_in"]["A"], "datasets type and values match, but only compressed in A")
        display_messages(ci["only_compressed_in"]["B"], "datasets type and values match, but only compressed in B")   
        display_sub_messages(ci["values_match_but_sizes_different"], "values match but sizes different")
        display_sub_messages(ci["everything_matches"], "everything matches (%s)" % sort_msg)
    num_paired_groups = ci["total_paired_found"]["group"]
    num_val_match_datasets = (len(ci["types_differ_values_same"]["dataset"]) 
        + len(ci["everything_matches"]["dataset"])
        + len(ci["values_match_but_sizes_different"]["dataset"])
        + len(ci["only_compressed_in"]["A"]) + len(ci["only_compressed_in"]["B"]))
    num_val_match_attributes = (len(ci["types_differ_values_same"]["attribute"]) + 
        len(ci["everything_matches"]["attribute"]) + len(ci["values_match_but_sizes_different"]["attribute"]))
#     num_groups = (num_matching_groups + len(ci['only_in']['A']['group'])
#         + len(ci['only_in']['B']['group']))
    num_paired_datasets = ci["total_paired_found"]["dataset"] # + len(ci['only_in']['A']['dataset']) 
        # + len(ci['only_in']['B']['dataset']))
    num_paired_attributes = (ci["total_paired_found"]["attribute"]) # + len(ci['only_in']['A']['attribute']) +
        # + len(ci['only_in']['B']['attribute']))
    num_matching_datasets = len(ci["everything_matches"]['dataset'])
    num_matching_attributes = len(ci["everything_matches"]['attribute'])
    num_dont_match_attributes = num_paired_attributes - num_val_match_attributes
    num_dont_match_datasets = num_paired_datasets - num_val_match_datasets
    print ("-" * 20)
    # display any errors or warnings
    for msgtype in ('error','warning'):
        if ci[msgtype]:
            print("%i %ss:" % (len(ci[msgtype]), msgtype))
            print("\n".join(ci[msgtype]))
    print ("** Summary")
    if single_file:
        print("%i groups, %i datasets, %i attributes" % (
            num_paired_groups, num_paired_datasets, num_paired_attributes))
        return
    # display summary for file comparison:
    print ("Unpaired groups: %i only in A, %i only in B" % (
        len(ci['only_in']['A']['group']), len(ci['only_in']['B']['group'])))
    print ("Unpaired datasets: %i only in A, %i only in B" % (
        len(ci['only_in']['A']['dataset']), len(ci['only_in']['B']['dataset'])))
    print ("Unpaired attributes: %i only in A, %i only in B" % (
        len(ci['only_in']['A']['attribute']), len(ci['only_in']['B']['attribute'])))
    print ("Total paired: %i datasets, %i attributes, %i groups" % ( num_paired_datasets,
        num_paired_attributes, num_paired_groups))
    print ("Total paired with values match: %i/%i datasets, %i/%i attributes." % (num_val_match_datasets,
        num_paired_datasets, num_val_match_attributes, num_paired_attributes))
    print ("Total paired, vals don't match: %i/%i datasets, %i/%i attributes." % (num_dont_match_datasets,
        num_paired_datasets, num_dont_match_attributes, num_paired_attributes))
    print ("Total paired, everything match: %i/%i datasets, %i/%s attributes" % (
        num_matching_datasets, num_paired_datasets, num_matching_attributes, num_paired_attributes))
    # done displaying summary numbers
    # now display match messages if appropriate
    # first check for any unpaired.  If so, these files do not match
    total_unpaired = 0
    for ab in ("A", "B"):
        for comp in ("group", "dataset", "attribute", "other"):
            total_unpaired += len(ci['only_in'][ab][comp])
    if total_unpaired > 0:
        print("Files do not match, there are %i unpaired components" % total_unpaired)
    else:
        # check for exact match
        if (num_matching_attributes == num_paired_attributes and 
            num_matching_datasets == num_paired_datasets):
            # these files exactly match
            print ("** Files exactly match **")
        else:
            # check for match for NWB files
            check_for_nwb_match(num_dont_match_datasets, num_dont_match_attributes)


def check_for_nwb_match(num_dont_match_datasets, num_dont_match_attributes):
    """ Check to see if the files are matching for everything except those
    datasets and attributes that normally vary between NWB files.  If so, display
    message, 'NWB files exactly match' """
    global ci, nwb_variable_datasets, nwb_variable_attributes
    found_vds = []  # found variable datasets
    found_vat = []  # found variable attributes
    # check for datasets that should ignore for NWB match
    array_names = ["types_differ_values_same", "types_same_values_differ", "values_and_types_differ"]
    for arn in array_names:
        for msg in ci[arn]["dataset"]:
            for vds in nwb_variable_datasets:
                if msg.startswith("%s:" % vds):  # append colon to data set path for matching
                    found_vds.append(vds)
                    continue
    # check for attributes that should ignore for NWB match
    for arn in array_names:
        for msg in ci[arn]["attribute"]:
            for vat in nwb_variable_attributes:
                apath, aid = vat
                if msg.startswith("%s %s:" % (apath, aid)):
                    found_vat.append(vat)
                    continue
    # now see is the found variable datasets and attributes account for all errors
    if len(found_vds) == num_dont_match_datasets and len(found_vat) == num_dont_match_attributes:
        vds_list = ", ".join(found_vds)
        vat_list = ", ".join(["%s %s" % (vat[0],vat[1]) for vat in found_vat])
        attr_msg = " and attributes: %s" % vat_list if vat_list else ""
        print("** NWB files exactly match ** (only %s%s differ)" % (
                    vds_list, attr_msg))

    
#     
#     elif num_val_match_attributes == num_paired_attributes:
#         if num_matching_attributes == num_paired_attributes:
#             attr_msg = "" # "attribute types and values all match"
#         else:
#             num_attr_types_dont_match = num_paired_attributes - num_matching_attributes
#             attr_msg = ", attribute types %i of %i do not match -but all values do" % (num_attr_types_dont_match,
#                 num_matching_attributes)
#         # check if only datasets that are normally variable in NWB files are preventing matching
#         if num_val_match_datasets + len(nwb_variable_datasets) >= num_paired_datasets:
#             # it's possible that only difference is due to datasets that may normally change
#             # when the nwb file is created at different times or with a slightly modified schema
#             # check for this
#             found_vds = []
#             array_names = ["types_differ_values_same", "types_same_values_differ", "values_and_types_differ"]
#             for arn in array_names:
#                 for msg in ci[arn]["dataset"]:
#                     for vds in nwb_variable_datasets:
#                         if msg.startswith("%s:" % vds):  # append colon to data set path for matching
#                             found_vds.append(vds)
#                             continue
#             if len(found_vds) + num_val_match_datasets == num_paired_datasets:
#                 print("** NWB files exactly match ** (only %s differ%s)" % (
#                     ", ".join(found_vds), attr_msg))      

def display_messages(messages, description, quote="", zero_msg=None, combine=True):
    """Prints description and messages.  "messages" is a list of messages.
    quote is set to a quote character used to enclose each message.
    zero_msg is append to description message for the case of no messages,
    e.g. zero_msg = "Good" to produce:  No errors.  -- Good.
    combine==True if should combine message, False otherwise
    """
    if not messages:
        msg = "No %s." % description
        if zero_msg:
            msg = msg + " -- %s" % zero_msg
        print ("** %s" % msg)
    else:
        # messages =  make_bytes_list(messages) # py3, convert to array of byte strings
        cmsg = cm.combine_messages(messages) if combine else messages
        if len(cmsg) != len(messages):
            print ("** %i %s (%i combined):" %(len(messages), description, len(cmsg)))
        else:
            print ("** %i %s:" % (len(messages), description))
        i = 0
        for m in cmsg:
            i = i + 1
            mt = m.replace("\n", "\n     ")  # insert tab after new line char
            # convert message to bytes if unicode to prevent error
            # UnicodeEncodeError: 'ascii' codec can't encode characters in position 44-45: ordinal not in range(128)
            # when output is being written to a file
            if isinstance(mt, unicode) and version_info[0] < 3:
                mt = mt.encode('utf-8')
            print ("%3i. %s%s%s" % (i, quote, mt, quote))
            
            
def display_sub_messages(sub_messages, description, zero_msg = None, qualifier=None, combine=True):
    """ Display messages that are in subparts (dictionary entires) of sub_messages.
    qualifier is text to put in front of word "group" or "dataset" in
    generated message.  e.g. "recommended" 
    """
    quote = "'"
    for type in sorted(sub_messages.keys()):
        quantity = len(sub_messages[type])
        if type == "unknown" and quantity == 0:
            # don't display unknown types if there are none
            continue
        types = type + "s" if quantity != 1 else type
        if qualifier:
            desc = "%s %s %s" % (qualifier, types, description)
        else:
            desc = "%s %s" % (types, description)
        display_messages(sub_messages[type], desc, quote, zero_msg, combine=combine)


# Save groups, datasets, or attributes that are only in one file but not the other
# fab will be "A" or "B", ids list of ids, desc dictionary of info for all ids
# grp is the hdf5 group containing datasets or groups (if ids is datasets or groups)
# or is the node (group or dataset) containing the attributs, if ids are all
# attributes.  f is the h5py file object.
def save_only_in(fab, ids, desc, grp, f):
    global ci
    for id in ids:
        path = desc[id]["full_path"]
        type = desc[id]['type']
        if type not in ("group", "dataset", "attribute"):
            type = "other"
        if type == 'attribute':
            path = path + ": %s" % id
            value = grp.attrs[id]
            # tally_types(desc[id]["full_path"], id, value)
            compress = None
        elif type == "dataset":
            value = grp[id].value
            # tally_types(desc[id]["full_path"], '', value)
            compress = desc[id]["compression"]
        if type in ("attribute", "dataset"):
            size = desc[id]['size']
            val_msg = make_value_summary(value, f)
            typ_msg = "dtype=%s, shape=%s" % (desc[id]['dtype'], desc[id]['shape'])
            compress_msg = ", compress=%s" % compress if compress else ""
            msg = "%s type (%s) size (%i)%s, val='%s'" % (path, typ_msg, size, compress_msg,
                val_msg)
        else:
            msg = path
        ci['only_in'][fab][type].append(msg)


def diff_attributes(node1, node2, path):
    """ generate diff of attribute values.  Returns total number of unique
    attribute identifiers (num_aids).  That is only used to detect groups that
    have no attributes or members"""
    global single_file, f1, f2, nwb_variable_attributes, filter_nwb
    ai1 = get_attr_info(node1, path)
    ai2 = get_attr_info(node2, path) if not single_file else ai1
    in_a = set(ai1.keys())
    in_b = set(ai2.keys())
    only_in_a = list(in_a - in_b)
    only_in_b = list(in_b - in_a)
    save_only_in("A", only_in_a, ai1, node1, f1)
    save_only_in("B", only_in_b, ai2, node2, f2)
    common = sorted(list(in_a.intersection(in_b)))
    num_aids = len(only_in_a) + len(only_in_b) + len(common)  # number attribute ids
    for aid in common:
        try:
            v1 = node1.attrs[aid]
        except Exception as e:
            # unable to read attribute, assume because h5py cannot read fixed length utf-8
            v1 = "<<Unable to read; fixed size utf?>>"
#         tally_types(path, aid, v1)
        if single_file:
            v2 = v1
        else:
            try:
                v2 = node2.attrs[aid]
            except Exception as e:
                # unable to read attribute, assume because h5py cannot read fixed length utf-8
                v2 = "<<Unable to read; fixed size utf?>>"
        do_filtering = False
        if filter_nwb:
            # check if should filter this attribute
            for vat in nwb_variable_attributes:
                vpath, vaid = vat
                if path == vpath and vaid == aid:
                   do_filtering = True
                   continue
        save_dataset_or_attribute_diff("attribute", aid, path, ai1, ai2, v1, v2, do_filtering)
    return num_aids


# def save_dataset_or_attribute_diff(ctype, mid, mpath, ci1, ci2, vals_match, vals_close):
def save_dataset_or_attribute_diff(ctype, mid, mpath, ci1, ci2, v1, v2, do_filtering=False):
    # ctype - container type, either 'dataset' or 'attribute'
    # mid - member id (id of dataset or attribute)
    # ci1 - information for all members of container 1 (from file "A")
    # ci2 - information for all members of container 2 (from file "B")
    # v1, v2 - values from file 1 (a) and file 2 (b)
    # do_filtering - True if info (dtype, size, value) about this value should not be displayed
    global ci, single_file, f1, f2
#     if mpath == '/analysis/regref_data/raw_rref' and mid == 'raw_rref':
#         import pdb; pdb.set_trace()
#     search_str = "Theta oscillations provide temporal wind"
#     if search_str in v1 or search_str in v2:
#         import pdb; pdb.set_trace()
    vals_match = vs.values_match(v1, v2, f1, f2) if not single_file else True
    vals_close = values_close(v1, v2) if not vals_match else None
    ci["total_paired_found"][ctype] += 1
    if do_filtering:
        # need to filter display of these values for generating signatures of NWB files
        a_size = b_size = a_dtype = b_dtype = "--"
        v1 = v2 = "--value removed for NWB signature--"
    else:
        a_size = str(ci1[mid]['size'])
        b_size = str(ci2[mid]['size'])
        a_dtype = ci1[mid]['dtype']
        b_dtype = ci2[mid]['dtype']
    # compare data types, shape  Don't include rank since shape has that
    com = "compression"  # shorthand
    a_compress = ci1[mid][com] if com in ci1[mid] and ci1[mid][com] else None
    b_compress = ci2[mid][com] if com in ci2[mid] and ci2[mid][com] else None
    a_type = "dtype=%s, shape=%s" % (a_dtype, ci1[mid]['shape'])
    b_type = "dtype=%s, shape=%s" % (b_dtype, ci2[mid]['shape'])
    types_match = a_type == b_type
    sizes_match = a_size == b_size
    compress_match = a_compress == b_compress
    size_message = "size (%s) matches" % a_size if sizes_match else "size A:%s, B:%s" % (
        a_size, b_size)
    compress_message = (", compress A:%s B:%s" % (a_compress, b_compress) 
        if a_compress or b_compress else "")
    sc_message = size_message + compress_message
    loc = "%s %s" % (mpath, mid) if ctype == "attribute" else mpath
    vals_cmatch = vals_match or vals_close
    cmatch_str = "closly " if vals_close else ""
#     if mpath == '/identifier':
#         import pdb; pdb.set_trace()
    vsum = make_values_summary(v1, v2, vals_cmatch)
    if types_match and not vals_cmatch:
        msg = "%s: types match (%s), but not values; %s %s" % (loc, a_type, vsum, sc_message)
        ci["types_same_values_differ"][ctype].append(msg)
    elif not types_match and vals_cmatch:
        msg = "%s: type A: (%s) B: (%s), values %smatch, %s %s" % (loc, a_type, b_type, cmatch_str, vsum, sc_message)
        ci["types_differ_values_same"][ctype].append(msg)
    elif not types_match and not vals_cmatch:
        # import pdb; pdb.set_trace()
        msg = "%s: type A: (%s) B: (%s), and values differ. %s %s" % (
            loc, a_type, b_type, vsum, sc_message)
        ci["values_and_types_differ"][ctype].append(msg)
    elif a_compress != b_compress:
        assert types_match, "types should match, but don't"
        assert vals_cmatch, "vals should match, but don't"
        msg = "%s: types match (%s), values %smatch; %s" %(loc, a_type, cmatch_str, sc_message)
        cf = "A" if a_compress else "B"
        ci["only_compressed_in"][cf].append(msg)    
    elif not sizes_match:
        msg = "%s: types match (%s), values %smatch; sizes differ. %s" % (loc,
            a_type, cmatch_str, sc_message)
        ci["values_match_but_sizes_different"][ctype].append(msg)     
    else:
        assert types_match
        assert vals_cmatch
        assert sizes_match
        assert compress_match
        # everything matches
        short_compress_msg = ", compress=%s" % a_compress if a_compress else ""
        sclosly_msg = "closly matches " if vals_close else ""
        # msg = "%s: (%s) %s size (%i)%s" % (loc, a_type, sclosly_msg, a_size, short_compress_msg)
        try:
            msg = "%s: %s %ssize (%s)%s %s" % (loc, a_type, sclosly_msg, a_size, short_compress_msg, vsum)
        except UnicodeDecodeError as e:
            error_exit("UnicodeDecodeError")
        ci["everything_matches"][ctype].append(msg)

# make summary for two values that may or may not match
def make_values_summary(v1, v2, vals_cmatch):
    """ Make short summary of values, or value if they match"""
    global f1, f2
    v1s = make_value_summary(v1, f1)
    if vals_cmatch:
        val_sum = " val='%s'" % v1s
    else:
        v2s = make_value_summary(v2, f2)
        val_sum = " val A='%s' b='%s'" % (v1s, v2s)
    return val_sum

# make summary for single value
def make_value_summary(val, fileObj):
    global ci
    (value_summary, vs_msg, vs_msg_type) = vs.make_value_summary(val, fileObj)
    if vs_msg:
        assert vs_msg_type in ('warning', 'error')
        if vs_msg not in ci[vs_msg_type]:
            # only include message once
            ci[vs_msg_type].append(vs_msg)
    return value_summary


# def lmake_value_summary(val):
#     # make summary for a single value
#     uval = val2str(val)
#     # use json.dumps to get full representation of value; str(uval) does not show all values
#     val_str = json.dumps(uval, separators=(',',':'))
#     if len(val_str) > 40:
#         val_str = val_str[0:40]+"..." + hashval(val_str[40:])
#     return val_str


# def make_value_summary(val):
#     # make summary for a single value
#     return val2str(val)
# #     if isinstance(val, np.ndarray) and len(val) > 0 and val[0] == b'2017-01-19T11:07:23.280599':
# #         print("found b'2017-01-19T11:07:23.280599'")
# #         import pdb; pdb.set_trace()
#     uval = make_str(val)
# #     if 'Behavioral testing' in val:
# #         import pdb; pdb.set_trace()
# #     val_str = str(uval)
#     try:
#         val_str = str(uval)
#     except UnicodeEncodeError as e:
#         if isinstance(uval, unicode):
#             val_str = uval.encode('utf-8')
#         else:
#             print ("unable to perform str function on type %s, value:" % type(uval))
#             print (uval)
#             import pdb; pdb.set_trace()
#     # val_str = str(make_str(val))  # py3, make unicode for combine_messages
#     if len(val_str) > 40:
#         val_str = val_str[0:40]+"..." + hashval(val_str[40:])
# #     if '2017-01-17T14:56:06.203565' in val_str:
# #         import pdb; pdb.set_trace()
#     return val_str


def diff_groups(grp1, grp2, path):
    ggp = (grp1, grp2, path)
    # use list to avoid recursion (more efficient)
    to_check = [ggp]
    while to_check:
        ggp = to_check.pop(0)
        member_groups = diff_groups2(ggp)
        to_check.extend(member_groups)
    
# this used within pdb to determine why some 2-D arrays did not match (had some elements NaN)    
# def cmp_arrays(v1, v2):
#     nx, ny = v1.shape
#     for x in range(nx):
#         for y in range(ny):
#             if(v1[x, y] != v2[x, y]):
#                 import pdb; pdb.set_trace()
    

# compare members of groups specified by ggp
# return list of additional groups to process
def diff_groups2(ggp):
    global ci
    global f1, f2
    global filter_nwb, single_file
    global nwb_variable_datasets
    ci["total_paired_found"]["group"] += 1
    grp1, grp2, path = ggp
    num_aids = diff_attributes(grp1, grp2, path)  # num_aids - number unique attribute ids
    gi1 = get_group_info(path, grp1)
    gi2 = get_group_info(path, grp2) if not single_file else gi1
    in_a = set(gi1.keys())
    in_b = set(gi2.keys())
    only_in_a = list(in_a - in_b)
    only_in_b = list(in_b - in_a)
    save_only_in("A", only_in_a, gi1, grp1, f1)
    save_only_in("B", only_in_b, gi2, grp2, f2)
    common = sorted(list(in_a.intersection(in_b)))
    num_mids = len(only_in_a) + len(only_in_b) + len(common)
    if num_aids == 0 and num_mids == 0:
        # these paired groups have no members or attributes
        ci["empty_paired_groups"].append(path)
    member_groups = []
    for mid in common:
        mpath = make_full_path(path, mid)
        type_a = gi1[mid]['type']
        type_b = gi2[mid]['type']
        # in case either are soft links, save them
        save_soft_link("A", gi1[mid])
        save_soft_link("B", gi2[mid])
        # use locations (object no) for detecting common paths (hard links)
        loc_a = str(gi1[mid]['objno'])
        loc_b = str(gi2[mid]['objno'])
        previously_found = loc_a in ci['locations']['A'] and loc_b in ci['locations']['B']
        # save current location and path for both groups (appends path if was found before)
        if type_a in ("group", "dataset"):
            save_to_dict_array(ci['locations']['A'], loc_a, (mpath, type_a))
        if type_b in ("group", "dataset"):
            save_to_dict_array(ci['locations']['B'], loc_b, (mpath, type_b))
        if previously_found:
            # both of these nodes were found previously (because of links), no need to process
            continue
        if type_a != type_b:
            msg = "%s node types different. A type='%s', B type='%s'" % (mpath, 
                type_a, type_b)
            ci["node_types_different"].append(msg)
            continue
        # from here on, type_a == type_b.  Using type_a
        if type_a in ("ext_link", "link"):
            # external link, and soft links are already saved, in function save_soft_link
            continue
        # node types are the same, make sure they are either group or dataset
        if type_a not in ("group", "dataset"):
            msg = "%s unknown node type (%s)" % (mpath, type_a)
            ci["unknown_node_types"].append(msg)
            continue
        if type_a == "dataset":
            diff_attributes(grp1[mid], grp2[mid], mpath)
            # set true if should filter this
            do_filtering = filter_nwb and mpath in nwb_variable_datasets
            v1 = grp1[mid].value
            v2 = grp2[mid].value
            save_dataset_or_attribute_diff("dataset", mid, mpath, gi1, gi2, v1, v2, do_filtering)
        else:
            # Type is group, add to list of groups to process
            mg1 = grp1[mid]
            mg2 = grp2[mid]
            ggp = (mg1, mg2, mpath)
            member_groups.append(ggp)
    return member_groups
            
# def diff_files_old(file1, file2):
#     global filter_nwb, single_file
#     # file handles
#     global f1, f2
#     ci = initialize_ci()
#     if not filter_nwb:
#         if single_file:
#             print ("command was: python %s %s" % (sys.argv[0], file1))
#         else:
#             print ("command was: python %s %s %s" % (sys.argv[0], file1, file2))
#     if single_file:
#         print ("Generating signiture for %s" % file1)
#     else:
#         print ("comparing %s (A) and %s (B)" % (file1, file2))
#     print("")
#     try:
#         f1 = h5py.File(file1, 'r')
#     except IOError:
#         print ("Unable to open file '%s'" % file1)
#         sys.exit(1)
#     if not single_file:
#         try:
#             f2 = h5py.File(file2, 'r')
#         except IOError:
#             print ("Unable to open file '%s'" % file2)
#             sys.exit(1)
#     else:
#         f2 = f1
#     # get_sizes(f1, file1)
#     diff_groups(f1["/"], f2["/"], "/")
#     display_report()
# #     print("python%i" % version_info[0])
# #     global ttypes
# #     pp.pprint(ttypes)
# #     print("examples:")
# #     pp.pprint(tetypes)


def open_h5file(fname):
    try:
        f = h5py.File(fname, 'r')
    except IOError:
        print ("Unable to open file '%s'" % fname)
        display_doc()
        sys.exit(1)
    return f

def diff_files(file1, file2):
    global filter_nwb, single_file
    # file handles
    global f1, f2
    ci = initialize_ci()
    if not filter_nwb:
        if single_file:
            print ("<%% command was: python %s %s %%>" % (sys.argv[0], file1))
        else:
            print ("<%% command was: python %s %s %s %%>" % (sys.argv[0], file1, file2))
    if single_file:
        print ("<%% Generating signature for %s %%>" % file1)
    else:
        print ("<%% comparing %s (A) and %s (B) %%>" % (file1, file2))
    print("")
    f1 = open_h5file(file1)
    if not single_file:
        f2 = open_h5file(file2)
    else:
        f2 = f1
    # get_sizes(f1, file1)
    diff_groups(f1["/"], f2["/"], "/")
    display_report()


# used for profiling
# import cProfile

if __name__ == '__main__':
    if len(sys.argv) not in (2, 3, 4):
        display_doc()
        sys.exit(1)
    file1 = sys.argv[1]
    opts = sys.argv[-1].lstrip("-") if sys.argv[-1].startswith('-') and len(sys.argv[-1]) > 2 else None
    if len(sys.argv) == 4 and opts is None:
        print("Third input parameter should be <opts>, but value found does not start with '-': %s" % sys.argv[3])
        display_doc()
        sys.exit(1)
    file2 = sys.argv[2] if (len(sys.argv) == 3 and opts is None) or len(sys.argv) > 3 else None
    if opts is not None:
        given_opts = set(list(opts))
        possible_options = set(['N', 'a'])
        found_options = possible_options.intersection(given_opts)
        unknown_options = list(given_opts - found_options)
        if len(unknown_options) > 0:
            print ("Unknown option(s) specified: %s.  Should include only: %s" % (unknown_options,
            possible_options))
            display_doc()
            sys.exit(1)
    else:
        found_options = []
    filter_nwb = ("N" in found_options)
    alpha_sort = ("a" in found_options)
    # set to True if this file is being compared to itself
    single_file = file2 is None
    if single_file:
        # compare file to itself to get information about links and sizes
        diff_files(file1, file1)
        # cProfile.run('diff_files("%s", "%s")' % (sys.argv[1], sys.argv[1]))
    else:
        diff_files(file1, file2)
