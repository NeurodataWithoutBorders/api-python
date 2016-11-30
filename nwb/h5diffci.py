# find differences between hdf5 files


import re
import sys
import h5py
# import copy
import numpy as np
import combine_messages as cm

import pprint
pp = pprint.PrettyPrinter(indent=4)

def reverse_dict(din):
    dout = {}
    for key in din:
        val = din[key]
        if val in dout:
            dout[val].append(key)
        else:
            dout[val]= [key]
    return dout


def make_full_path(path, name):
    """ Combine path and name to make full path"""
    if path == "/":
       full_path = "/" + name
    else:
        assert not path.endswith('/'), "non-root path ends with '/' (%s)" % path
        full_path = path + "/" + name
    # remove any duplicate slashes, should be unnecessary
    # full_path = re.sub(r'//+',r'/', full_path)
    return full_path


def values_match(x, y):
    """ Compare x and y.  This needed because the types are unpredictable and sometimes
    a ValueError is thrown when trying to compare.  Also, if any value has NaN, then
    the value will not match itself if doing a normal comparison.
    """
    if x is y:
        return True
    # compare arrays so corresponding NaN values are treated as a match
    if (isinstance(x, np.ndarray) and isinstance(y, np.ndarray)
        and np.issubdtype(x.dtype, np.float) and np.issubdtype(y.dtype, np.float)):
        # from: http://stackoverflow.com/questions/10710328/comparing-numpy-arrays-containing-nan
        try:
            np.testing.assert_equal(x,y)
        except AssertionError:
            return False
        return True
    # check for two scalar NaN.  If found, treat as match
    if (np.issubdtype(type(x), np.float) and np.issubdtype(type(y), np.float)
        # and x.shape == () and y.shape == ()
        and np.isnan(x) and np.isnan(y)):
        return True
    try:
        eq = x==y
    except ValueError:
        # ValueError: shape mismatch: objects cannot be broadcast to a single shape
        return False
    if isinstance(eq, bool):
        return eq
    return eq.all()
    
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


# creates and returns a summary description for every element in a group
def get_group_info(path, grp):
    global h5_ntypes
    gi = {}
    # get group id used for low-level h5py api
    h5g = grp.id
    for i in range(h5g.get_num_objs()):
        mname = h5g.get_objname_by_idx(i)
        mtype = h5_ntypes[h5g.get_objtype_by_idx(i)]
        try:
            minfo = h5py.h5g.get_objinfo(h5g, mname)
        except TypeError:
            objno = "ext_link:dangling"  # make a fake object number
        else:
            objno = minfo.objno
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
        elif mtype == 'ext_link':
            # target of external link
            target = "\n".join(h5g.links.get_val(mname))
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
        aid = h5py.h5a.open(nid, name=name)
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
        for loc in ci["locations"][ab]:
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
                pathsc[0] = "to: \"%s\" %s" % (target, pathsc[0])
                msg = "\n\t".join(pathsc)
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
        for hard_loc in ci["locations"][source_ab]:
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
                total_found, str(num_link_groups)))
        if not single_file:
            print (("   Note: links inside unpaired groups will not be found.  To guarantee "
                "finding all links, run script with just one file (comparing it to itself)."))
                
                
def validate_group(source_ab, source_link_type, type, paths, dest_ba, errors):
    """ make sure that all paths in paths are in a group in dest_ba and that
    the type (group or dataset) matches"""
    # pick any path for searching
    path = paths[0]
    # look for path in hard link group
    for hard_loc in ci["locations"][dest_ba]:
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
        "only_compressed_in": { "A": [], "B": []},
        "values_match_but_sizes_different": {"dataset": [], "attribute": []},
        # has: loc: [(path1, type1), (path2, type2), ...], loc: [ ...], ...]
        "locations": { "A": {}, "B": {} },
        # has: loc: size, loc: size (only for datasets)
        # sizes not currently used
        # "sizes": { "A": {}, "B": {} },
    }
    
def display_report(file1, file2):
    global ci
    find_hard_links()
    format_soft_links()
    display_sub_messages(ci['only_in']['A'], "only in A", zero_msg="Good")
    display_sub_messages(ci['only_in']['B'], "only in B", zero_msg="Good")
    display_messages(ci["node_types_different"], "node types differ", zero_msg="Good")
    # don't combine links, these already combined
    display_sub_messages(ci["hard_links"]['A'], "hard links in A", combine=False)
    display_sub_messages(ci["hard_links"]['B'], "hard links in B", combine=False)
    display_sub_messages(ci["soft_links"]['A'], "soft links in A", combine=False)
    display_sub_messages(ci["soft_links"]['B'], "soft links in B", combine=False)
    check_link_equivalence()
    display_messages(ci["ext_links"]['A'], "ext_links in A")
    display_messages(ci["ext_links"]['B'], "ext_links in B"),   
    display_messages(ci["unknown_node_types"], "unknown node types (in both A and B)", zero_msg="Good")
    display_sub_messages(ci["types_same_values_differ"], "types match but values differ")
    display_sub_messages(ci["types_differ_values_same"], "types differ but values match")
    display_sub_messages(ci["values_and_types_differ"], "values and types differ")
    display_messages(ci["only_compressed_in"]["A"], "datasets type and values match, but only compressed in A")
    display_messages(ci["only_compressed_in"]["B"], "datasets type and values match, but only compressed in B")   
    display_sub_messages(ci["values_match_but_sizes_different"], "values match but sizes different")
    sort_by_size(ci["everything_matches"]['attribute'])
    sort_by_size(ci["everything_matches"]['dataset'])
    display_sub_messages(ci["everything_matches"], "everything matches (sorted in decreasing size)")
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
    print ("** Summary")
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
        cmsg = cm.combine_messages(messages) if cm else messages
        if len(cmsg) != len(messages):
            print ("** %i %s (%i combined):" %(len(messages), description, len(cmsg)))
        else:
            print ("** %i %s:" % (len(messages), description))
        i = 0
        for m in cmsg:
            i = i + 1
            mt = m.replace("\n", "\n     ")  # insert tab after new line char
            print ("%3i. %s%s%s" % (i, quote, mt, quote))
            
            
def display_sub_messages(sub_messages, description, zero_msg = None, qualifier=None, combine=True):
    """ Display messages that are in subparts (dictionary entires) of sub_messages.
    qualifier is text to put in front of word "group" or "dataset" in
    generated message.  e.g. "recommended" 
    """
    quote = "'"
    for type in sorted(sub_messages.keys()):
        quantity = len(sub_messages[type])
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
# attributes.
def save_only_in(fab, ids, desc, grp):
    global ci
    for id in ids:
        path = desc[id]["full_path"]
        type = desc[id]['type']
        if type not in ("group", "dataset", "attribute"):
            type = "other"
        if type == 'attribute':
            path = path + ": %s" % id
            value = grp.attrs[id]
            compress = None
        elif type == "dataset":
            value = grp[id].value
            compress = desc[id]["compression"]
        if type in ("attribute", "dataset"):
            size = desc[id]['size']
            val_msg = make_value_summary(value)
            typ_msg = "dtype=%s, shape=%s" % (desc[id]['dtype'], desc[id]['shape'])
            compress_msg = ", compress=%s" % compress if compress else ""
            msg = "%s type (%s) size (%i)%s, val='%s'" % (path, typ_msg, size, compress_msg,
                val_msg)
        else:
            msg = path
        ci['only_in'][fab][type].append(msg)


def diff_attributes(node1, node2, path):
    ai1 = get_attr_info(node1, path)
    ai2 = get_attr_info(node2, path)
    in_a = set(ai1.keys())
    in_b = set(ai2.keys())
    only_in_a = list(in_a - in_b)
    only_in_b = list(in_b - in_a)
    save_only_in("A", only_in_a, ai1, node1)
    save_only_in("B", only_in_b, ai2, node2)
    common = sorted(list(in_a.intersection(in_b)))
    for aid in common:
        v1 = node1.attrs[aid]
        v2 = node2.attrs[aid]
        save_dataset_or_attribute_diff("attribute", aid, path, ai1, ai2, v1, v2)

       
# def save_dataset_or_attribute_diff(ctype, mid, mpath, ci1, ci2, vals_match, vals_close):
def save_dataset_or_attribute_diff(ctype, mid, mpath, ci1, ci2, v1, v2):
    # ctype - container type, either 'dataset' or 'attribute'
    # mid - member id (id of dataset or attribute)
    # ci1 - information for all members of container 1 (from file "A")
    # ci2 - information for all members of container 2 (from file "B")
    # v1, v2 - values from file 1 (a) and file 2 (b)
    global ci
    vals_match = values_match(v1, v2)
    vals_close = values_close(v1, v2) if not vals_match else None
    ci["total_paired_found"][ctype] += 1
    a_size = ci1[mid]['size']
    b_size = ci2[mid]['size']
    # compare data types, shape  Don't include rank since shape has that
    com = "compression"  # shorthand
    a_compress = ci1[mid][com] if com in ci1[mid] and ci1[mid][com] else None
    b_compress = ci2[mid][com] if com in ci2[mid] and ci2[mid][com] else None
    a_type = "dtype=%s, shape=%s" % (ci1[mid]['dtype'], ci1[mid]['shape'])
    b_type = "dtype=%s, shape=%s" % (ci2[mid]['dtype'], ci2[mid]['shape'])
    types_match = a_type == b_type
    sizes_match = a_size == b_size
    compress_match = a_compress == b_compress
    size_message = "size (%i) matches" % a_size if sizes_match else "size A:%i, B:%i" % (
        a_size, b_size)
    compress_message = (", compress A:%s B:%s" % (a_compress, b_compress) 
        if a_compress or b_compress else "")
    sc_message = size_message + compress_message
    loc = "%s %s" % (mpath, mid) if ctype == "attribute" else mpath
    vals_cmatch = vals_match or vals_close
    cmatch_str = "closly " if vals_close else ""
    vs = make_values_summary(v1, v2, vals_cmatch)
    if types_match and not vals_cmatch:
        msg = "%s: types match (%s), but not values; %s %s" % (loc, a_type, vs, sc_message)
        ci["types_same_values_differ"][ctype].append(msg)
    elif not types_match and vals_cmatch:
        msg = "%s: type A: (%s) B: (%s), values %smatch, %s %s" % (loc, a_type, b_type, cmatch_str, vs, sc_message)
        ci["types_differ_values_same"][ctype].append(msg)
    elif not types_match and not vals_cmatch:
        msg = "%s: type A: (%s) B: (%s), and values differ. %s %s" % (
            loc, a_type, b_type, vs, sc_message)
        ci["values_and_types_differ"][ctype].append(msg)
    elif a_compress != b_compress:
        assert types_match, "types should match, but dont"
        assert vals_cmatch, "vals should match, but dont"
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
        msg = "%s: (%s) %s size (%i)%s" % (loc, a_type, sclosly_msg, a_size, short_compress_msg)
        ci["everything_matches"][ctype].append(msg)

def make_values_summary(v1, v2, vals_cmatch):
    """ Make short summary of values, or value if they match"""
    v1s = make_value_summary(v1)
    if vals_cmatch:
        vs = " val='%s'" % v1s
    else:
        v2s = make_value_summary(v2)
        vs = " val A='%s' b='%s'" % (v1s, v2s)
    return vs
    
def make_value_summary(val):
    # make summary for a single value
    val_str = str(val)
    if len(val_str) > 40:
        val_str = val_str[0:40]+"..."
    return val_str
        
        

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
    ci["total_paired_found"]["group"] += 1
    grp1, grp2, path = ggp
    diff_attributes(grp1, grp2, path)
    gi1 = get_group_info(path, grp1)
    gi2 = get_group_info(path, grp2)
    in_a = set(gi1.keys())
    in_b = set(gi2.keys())
    only_in_a = list(in_a - in_b)
    only_in_b = list(in_b - in_a)
    save_only_in("A", only_in_a, gi1, grp1)
    save_only_in("B", only_in_b, gi2, grp2)
    common = sorted(list(in_a.intersection(in_b)))
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
        if type_a == "ext_link":
            # external link, already saved
            continue
        # node types are the same, make sure they are either group or dataset
        if type_a not in ("group", "dataset"):
            msg = "%s unknown node type (%s)" % (mpath, type_a)
            ci["unknown_node_types"].append(msg)
            continue
        if type_a == "dataset":
            diff_attributes(grp1[mid], grp2[mid], mpath)
            v1 = grp1[mid].value
            v2 = grp2[mid].value
            save_dataset_or_attribute_diff("dataset", mid, mpath, gi1, gi2, v1, v2)
        else:
            # Type is group, add to list of groups to process
            mg1 = grp1[mid]
            mg2 = grp2[mid]
            ggp = (mg1, mg2, mpath)
            member_groups.append(ggp)
    return member_groups
            
def diff_files(file1, file2):
    ci = initialize_ci()
    print ("")
    print ("command was: python %s %s %s" % (sys.argv[0], file1, file2))
    if file1 == file2:
        print ("comparing %s (A) to itself (B)" % file1)
    else:
        print ("comparing %s (A) and %s (B)" % (file1, file2))
    print
    try:
        f1 = h5py.File(file1, 'r')
    except IOError:
        print ("Unable to open file '%s'" % file1)
        sys.exit(1)
    try:
        f2 = h5py.File(file2, 'r')
    except IOError:
        print ("Unable to open file '%s'" % file2)
        sys.exit(1)

    # get_sizes(f1, file1)
    
    diff_groups(f1["/"], f2["/"], "/")
    display_report(file1, file2)

if len(sys.argv) not in (2, 3):
    print ("Usage: %s <file1.h5> [<file2.h5>]" % sys.argv[0])
    sys.exit(1)
# set to True if this file is being compared to itself
single_file = len(sys.argv) == 2
    
if single_file: 
    # compare file to itself to get information about links and sizes
    diff_files(sys.argv[1], sys.argv[1])
else:
    diff_files(sys.argv[1], sys.argv[2])