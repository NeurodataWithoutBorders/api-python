# h5gate documentation tools
# (generate documentation from specification language definition(s)

import sys
import cgi
import urllib
import pprint
import re
import os.path
pp = pprint.PrettyPrinter(indent=4)
import h5gate
import traceback
import copy

    
def get_lids(f):
    """get identifiers that specify an absolute location (i.e. start with '/')"""
    lids={}
    for ns in f.ddef.keys():
        lids[ns] = []
        structures = f.ddef[ns]['structures']
        for id in structures:
            if id[0] == '/':
                lids[ns].append(id)
    return lids

def get_starting_group(lids):
    """finds the namespace and id of the group that is closest to the root.
    Normally, this will be the root itself, but sometimes it might not be."""
    sl = None
    for ns in lids:
        for id in lids[ns]:
            if id.endswith('/') and '<' not in id:  # make sure variable name path not used
                level = id.count('/')
                if sl is None or level < sl:
                    sl = level
                    slns = ns
                    slid = id
    return (slns, slid)
    

    
    
def build_node_tree(f):
    """ Build node tree from structure definitions starting with id & ns found by
    'get_starting_group'.  Keep track of any location id's used when building
    tree in array 'used_lids'.
    """
    lids = get_lids(f)
    slns, slid = get_starting_group(lids)
    used_lids = [ slid,]
    sdef = f.get_sdef(slid, slns, "referenced in build_node_tree")
    parent_path, name = f.get_name_from_full_path(slid)
    parent = f.path2node[parent_path] if parent_path in f.path2node else None
    link_info = None  # assume this is not a link
    attrs = {}
    name = ""  # only used for variable named nodes
    # Create the starting node so it's saved in the node tree
    node = h5gate.Group(f, sdef, name, parent_path, attrs, parent, link_info)
    make_group_members(f, node)

    
# keep track of variable id's and where they are made
created_ids = {}
    
def get_source_id(sl):
    """sl is list of sources in form: ns:id.  Return
    the ns and id of the last entry"""
    source = sl[len(sl) - 1]  # get last source item
    ns, id = source.split(':')
    return (ns, id)

# global variable for storing dict of "av_ids"
av_ids = {}
# global variable for storing nodes (h5gate Group object) for av_ids
avid_nodes = []

def find_av_ids(f):
    """ Find "absolute-variable" ids; that is Ids in the schema that are an
    absolute path, e.g. starts with "/", but the last component in the
    path is a variable id, e.g. enclosed in <>.  Example is:
    "/stimulus/presentation/<VoltageClampStimulusSeries>/"
    Members in structures like this are automatically merged into the group made
    with the matching type (e.g. "<VoltageClampStimulusSeries>/" at the specified
    location, e.g. "/stimulus/presentation/".
    These "av structures" enable extensions in which the additional members are
    place in one location, (e.g. "/stimulus/presentation/"), but not another,
    e.g. "/stimulus/templates/".
    To make documentation for the av-structure, when a group is created, (in
    function make_group_members), there must be a test to see if the group
    overlaps the variable id.  This is so a version of the group will be created
    for each overlap in addition to any version created without an overlap.
    TODO: this will introduce a bug if the id is never referenced by itself, without
    overlaps.  Need to fix by creating group someplace if it's not referenced by
    itself.
    To help find the overlaps, this routine creates a dict (av_overlaps) with the
    following form:
    { path_prefix: { vid1: ns1, vid2: ns2, ...}, path_prefix2: { ... } }
    where path_prefix is the absolute path prefix, e.g. "/stimulus/presentation"
    (without a trailing slash)
    vid is the variable id append at the end, e.g.  "<VoltageClampStimulusSeries>/"
    ns - is the namespace of the structure containing the av_id.
    """
    global av_ids
    for ns in f.ddef:
        structures = f.ddef[ns]['structures']
        for id in structures:
            if id[0] == '/':
            # found absolute path, check for variable id at end
                path_prefix, name = f.get_name_from_full_path(id)
                v_id = re.match( r'^<[^>]+>/$', name) # True if variable_id (in < >)
                if v_id:
                    # found variable id at end, save this av_id
                    if path_prefix in av_ids:
                        av_ids[path_prefix][name] = ns
                    else:
                        av_ids[path_prefix] = {name: ns}
#     print "found av_ids:"
#     pp.pprint(av_ids)
#     sys.exit(0)

def get_avid_ns(f, id):
    """ Checks to see if the provide id is an "av_id".  If so, return the namespace
    for the id.  If not, return None"""
    global av_ids
    path_prefix, name = f.get_name_from_full_path(id)
    ns = (av_ids[path_prefix][name] if path_prefix in av_ids
        and name in av_ids[path_prefix] else None)
    return ns


def make_group_members(f, node):
    """ Make members of h5gate group node (in mstats) that are groups"""
    global created_ids, avid_nodes
    # build av_ids global variable
    find_av_ids(f)
    to_check = [node]
    while to_check:
        node = to_check.pop(0)
        mstats = node.mstats
        includes = node.includes
        member_ids = mstats.keys()
        if hasattr(node, 'subclass_merge_ids'):
            # remove keys made by subclass merge from member_ids list so don't create them
            subclass_ids = node.subclass_merge_ids[1:]
            member_ids = [id for id in member_ids if id not in subclass_ids]
        for mid in member_ids:
            if (mstats[mid]['type'] == 'dataset' or 'link' in mstats[mid]['df']):
                # either is a dataset, or is a link.  don't create it
                continue
            was_included = mid in includes
            id_path = f.make_full_path(node.full_path, mid)
            # returns ns if this is an "av_id" otherwise None
            avid_ns = get_avid_ns(f, id_path)
            if was_included and mid in created_ids and not avid_ns:
                # this id already created and it's not an "av_id"
                continue
            # need to create this group
            v_id = re.match( r'^<[^>]+>/?$', mid) # True if variable_id (in < >)
            if v_id:
                name = mid.strip('<>/')     # use name same as variable
            else:
                name = ''  # don't specify a name since it's a fixed name group
            id_noslash = mid.rstrip('/')
            grp = node.make_group(id_noslash, name=name)
            # print "made %s, avid_ns=%s" % (grp.full_path, avid_ns)
#             if grp.full_path == "/stimulus/presentation/VoltageClampStimulusSeries":
#                 import pdb; pdb.set_trace()
            # add this group to to_check to later check if should create members of this group
            to_check.append(grp)
            if was_included and not avid_ns:
                created_ids[mid] = node  # save node for later use in creating doc
            elif avid_ns:
                # created_ids[id_path] = grp  # save group for later use in creating doc for av_id
                avid_nodes.append(grp)
                
#                 t # save associated node for add_id_doc (routine add_iid_doc)   
#                 # see if source location was absolute
#                 source = node.mstats[id]['source']
#                 ns, sid = get_source_id(source)
#                 if sid[0] != '/':
#                     # source is not at absolute location, always save node
#                     created_ids[mid] = node  # save node for later use in creating doc
#                     print "saved node for relative id %s" % mid 
#                 else:
#                     if v_id and sid.endswith(vid):
#                         # source is an absolute path ending with a variable id, e.g.:
#                         # /stimulus/presentation/<VoltageClampStimulusSeries>
#                         # save full link to node
#                         print "saved node for absolute id with vid at end %s" % sid
#                         created_ids[sid] = node
#                 if sid[0] != '/':
#                     # found structure included that does not have absolute path
#                     # save the node that it's in for add_id_doc
#                     created_ids[id] = node  # save node for later use in creating doc
#     print "created_ids has:"
#     pp.pprint(sorted(created_ids.keys()))
#     print "stopping for now"
#     sys.exit(0)

# def get_avid_nodes(f):
#     """ Return list of nodes (h5gate Group objects) which store av_ids (id's with
#     an absolute path with a variable named id at the end."""
#     global av_ids, created_ids
#     avid_nodes = []
#     for path_prefix in av_ids:
#         for mid in av_ids[path_prefix]:
#             id_path = f.make_full_path(path_prefix, mid)
#             node = created_ids[id_path]
#             avid_nodes.append(node)
#     return avid_nodes
    

# def make_group_members_old(node):
#     """ Make members of h5gate group node (in mstats) that are groups"""
#     global
#     mstats = node.mstats
#     for id in mstats:
#         v_id = re.match( r'^<[^>]+>/?$', id) # True if variable_id (in < >)
#         if v_id or not id.endswith('/'):
#             # either a variable named member (in <>) or a dataset (does not have '/' at end)
#             continue
#         # found a group id that is not variable, create it
#         id_noslash = id.rstrip('/')
#         grp = node.make_group(id_noslash)
#         # and create any group members it might have
#         make_group_members(grp)


  
def make_header(title):
    """Return html for page header"""
    # allow specifying html5 or html4 doctype
    doctype = "html5"
    assert doctype in ('html5', 'html4')
    if doctype == "html4":
        doc_start = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
  <head>
    <meta content="text/html; charset=utf-8" http-equiv="content-type">
    <title>""" + title + """</title>"""
    else:
        # html5 doctype 
        doc_start = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>""" + title + """</title>"""
    # combine doc_start with the rest of the header
    html = doc_start + """
    <style type="text/css">
table {
    border-collapse: collapse;
    width: 100%;
    font-size: 9pt;
}
table, td, th {
    border: 1px solid black;
}
h2, h3 {
    padding-bottom: 0px;
    margin-bottom: 0px;
}


table.print-friendly tr td, table.print-friendly tr th {
        page-break-inside: avoid; !important;
        page-break-after: avoid
}
/*
table, tr, td, th, tbody, thead, tfoot {
    page-break-inside: avoid !important;
}
@media print
{
  table { page-break-after:auto }
  tr    { page-break-inside:avoid; page-break-after:auto }
  td    { page-break-inside:avoid; page-break-after:auto }
  thead { display:table-header-group }
  tfoot { display:table-footer-group }
}
*/
/*
@page {
   size: 6in 9.25in;
   margin: 27mm 16mm 27mm 16mm;
}
*/

body {
    font-family: Arial, Helvetica, sans-serif;
}
p {
    font-size: 12pt;
    text-align: justify;
}

p, ul{
     padding-bottom:0px; 
     margin-bottom:0px;
     padding-top:0px; 
     margin-top:0px;
}
table tr th {
    border-top: 1px solid #000000;
    border-bottom: 1px solid #000000;
    border-left: 1px solid #000000;
    border-right: none;
    padding-top: 0.04in;
    padding-bottom: 0.04in;
    padding-left: 0.04in;
    padding-right: 0in;
    background-color: #c0c0c0;
    font-size: 10pt;
   -webkit-print-color-adjust:exact;
}
table.dimensions {
    width: 50%;
}

span.hy {
    background-color: yellow;
    -webkit-print-color-adjust:exact;
}
span.red {
    color: red;
    -webkit-print-color-adjust:exact;
}
span.blue {
    color: blue;
    -webkit-print-color-adjust:exact;
}
span.del {
    text-decoration:line-through;
    text-decoration-color: red;
}
span.notbold{
    font-weight:normal
}

span.comment {
    font-style: italic;
    background-color: LightBlue;  /* Aqua;*/
    -webkit-print-color-adjust:exact;
}

/* Remove underline from links */

a:link {
    text-decoration: none;
}

a:visited {
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

a:active {
    text-decoration: underline;
}
    </style>
  </head>
  <body>
"""
    return html
   
def font_size(size, text):
    """ return html css stype to specify font size for text"""
    html = "<span style=\"font-size: %ipt\">%s</span>" % (size, text)
    return html
    
# html5_escape_table = {
#      "&": "%26",
#      '"': "%22",
#      "'": "%27",
#      ">": "%3E",
#      "<": "%3C;",
#      }
     
# html_list_bullets = [
#     "&bullet;",
#     "&cir;",
#     "&blacksquare;",
#     "&rtrif;",
#     "&rtri;"]
    
# def html_list_bullet(level):
#     """ Return character for bullet of html list"""
#     global html_list_bullets;
#     return html_list_bullets[level]
    
     
# html5_escape_table = {
#      "&": "&amp;",
#      '"': "&quot;",
#      "'": "&apos;",
#      ">": "&gt;",
#      "<": "&lt;",
#      }

# def html_escape(text):
#     """Produce entities within text."""
#     return cgi.escape(text)
#     # return "".join(html5_escape_table.get(c,c) for c in text)

def make_required_from_qty(qty):
    required = "yes" if qty in ("!", "+") else "recommended" if qty == "^" else "no"
    return required

def get_element(dict, key, default=None):
    """" if dict[key] present, return that.  Otherwise return default value"""
    value = dict[key] if key in dict else default
    return value   
    
# global variable to keep track of merges and includes
merges_found = {}
includes_found = {}

# global variable to keep track of ids used (referenced as a source)
ids_used = set()

def add_to_dict_array(da, key, value):
    """ da is a "dict_array", ie a dictionary mapping each key to an array of values.
    Add key and value to it."""
    if key in da:
        if value not in da[key]:
            da[key].append(value)
    else:
        da[key] = [value,]
    
 
def combine_dict_arrays(dest, source):
    """ dest and source are both dicts with arrays as values.  Put all entries
    in source into dest"""
    for key in source:
        values = source[key]
        for value in values:
            add_to_dict_array(dest, key, value)

def expand_targets(source_to_target):
    """ Make dictionary mapping each source to an expanded list of targets.
    The expanded list of targets is formed by finding any targets the targets
    in the initial list may map too. """ 
    source_to_expanded_targets = {}
    for source in source_to_target:
        tlist = source_to_target[source][:]  # make copy
        est = tlist[:]  # makes a copy of the copy
        while tlist:
            target = tlist.pop()
            if target in source_to_target:
                tlist2 = source_to_target[target]
                for item in tlist2:
                    if item not in est:
                        est.append(item)
                        tlist.append(item)
        source_to_expanded_targets[source] = sorted(est)
    return source_to_expanded_targets

def pack_dict_values(dict):
    """dict is a dictionary in which all values are a list of strings.  Create
    a "packed_dict" in which the array values are replaced by a comma separated
    list of the values"""
    packed = {}
    for key in dict:
        value = dict[key]
        packed[key] = ','.join(value)
    return packed

def reverse_dict(din):
    """ Make reverse dictionary.  din is a dictionary with each key
    mapped to a value.  Return (dout) is is a dictionary with keys equal to the
    values of din mapped to the list of keys in din.
    """
    dout = {}
    for key in din:
        value = din[key]
        add_to_dict_array(dout, value, key)
    return dout
    
def reverse_dict_array(din):
    """ Make reverse of dictionary, with each key mapped to an array of values"""
    dout = {}
    for key in din:
        val_arr = din[key]
        for value in val_arr:
            add_to_dict_array(dout, value, key)
    return dout 
            
def make_expanded_targets_to_sources(source_to_expanded_targets):
    """ make dictionary mapping expanded targets to all the sources that depend
    on those targets"""
    global expanded_targets_to_sources
    packed = pack_dict_values(source_to_expanded_targets)
    expanded_targets_to_sources = reverse_dict(packed)

def get_new_ids(tcids, ids_adding):
    """Given id's in table of contents (tcids), return a list of new ids that can
    be added to table of contents based on the id's present.  The new ids are sources
    that have targets which are all in tcids.  However, do not return any ids in ids_adding
    because those are already in the process of being added.
    """
    global source_to_expanded_targets
    new_ids = []
    for id in source_to_expanded_targets:
        if id not in tcids and id not in ids_adding:
            targets = source_to_expanded_targets[id]
            found_all = True
            for target in targets:
                if target not in tcids:
                    found_all = False
                    break
            if found_all:
                new_ids.append(id)
    return new_ids
    
def add_to_tc(id, level, tc, tcids, ids_adding):
    """add id to table of contents.
    id - id to add.
    level - indentation level for id.
    tc - table of contents.  Is a list of form:
        [(id1 level1) (id2 level2), ...]
    tcids - ids in table of contents
    ids_adding - id's that are currently being added to table of contents
        but are not yet stored in it.
    """
    global expanded_targets_to_sources
    # add id to table of contents and tcids
    tc.append((id, level))
    tcids.append(id)
    if id in ids_adding:
        ids_adding.remove(id)
    # check for new id's to add
    new_ids = get_new_ids(tcids, ids_adding)
    ids_adding.extend(new_ids)
    for new_id in sorted(new_ids):
        add_to_tc(new_id, level+1, tc, tcids, ids_adding)
            
# def build_tc(top_ids):
#     """Build table of contents listing id's ordered hierarchically under the
#     id's that they depend on.  top_ids are the 'top-level' ids from which other
#     id's depend.  Returns:
#     tc - table of contents.  List of form: [(id1 level1) (id2 level2), ...]
#     tcids - list of id that were added to table of contents).
#     """
#     import pdb; pdb.set_trace()
#     tc = []
#     tcids = []
#     ltop = top_ids[:]  # local top_ids, make copy of it
#     while ltop:
#         tcs = {}  # for storing all table of contents generated
#         llongest = None
#         for id in ltop:
#             ltc = tc[:]
#             ltcids = tcids[:]
#             level = 1
#             ids_adding = []
#             add_to_tc(id, level, ltc, ltcids, ids_adding)
#             # save table of contents found using this id
#             tcs[id] = {'tc': ltc, 'tcids': ltcids}
#             if llongest == None or len(ltcids) > llongest:
#                 llongest = len(ltcids)
#                 lid = id  # longest id
#         # now know which of the top ids found the most ids within it.  Use that id
#         tc = tcs[lid]['tc']
#         tcids = tcs[lid]['tcids']
#         # import pdb; pdb.set_trace()
#         ltop.remove(lid)
#     rv = (tc, tcids)
#     return rv
    
# def build_class_include_dict(classes):
#     """ Build dict mapping each class in classes, to a list of the classes that
#     are included by the class, either directly or indirectly.  This is done
#     to figure out the order in which the table of contents for the classes should
#     be made."""
#     # make dict mapping each class to list of class and any subclasses
#     subclasses = {}
#     for source in classes:
#         subclasses[source] = [source]
#         if source in merges_found:
#             subclasses[source].extend(merges_found[source])
#     # now find includes using subclasses
#     class_includes = {}
#     for source in classes:
#         class_includes[source] = []
#         for target in classes:
#             if source == target:
#                 continue
#             for souce_subclass in subclasses[source]:
#                 if source_subclass in includes_found:
#                     
#             source_set = [source] + 

        
def get_base_class_map():
    """ build dict mapping each class to it's base class (should be only one).  Classes
    are defined by merges."""
    base_class_map = {}
    for source in merges_found:
        key = source
        while key in merges_found:
            target_list = merges_found[key]
            assert len(target_list) == 1, "should only be one base class"
            key = target_list[0]
        base_class_map[source] = key
    return base_class_map

def get_base_class(source, base_class_map, classes):
    """ return base class corresponding to source.  Should either be given
    by base_class_map, or already be a base class listed in classes."""
    base = base_class_map[source] if source in base_class_map else source
    assert base in classes, "base '%s' not found in classes %s" % (base, classes)
    return base
               
def collapse_includes_found(classes):
    """ Convert "includes_found" dict to a new dict which replaces each class
    by the base class (as determined through merges).  This done to determine
    which classes depend on other classes, which is needed to figure out
    the order in which the classes should be displayed.
    classes is the list of classes to which all entries in includes_found
    should be either a class or subclass.
    """
    base_class_map = get_base_class_map()
    collapsed_includes_found = {}
    for source in includes_found:
        source_base = get_base_class(source, base_class_map, classes)
        for target in includes_found[source]:
            target_base = get_base_class(target, base_class_map, classes)
            add_to_dict_array(collapsed_includes_found, source_base, target_base)
    # print "collapsed_includes_found="
    # pp.pprint(collapsed_includes_found)
    return collapsed_includes_found
    
def get_tc_top_order(collapsed_includes, top_nodes, promoted_nodes):
    """ Deduce order in which ids at top of table of contents should be displayed.
    This done by using collapsed_includes, which contains the id's which must either
    be in top_nodes or promoted_nodes.
    collapsed_includes is a dictionary mapping a source id to target id's it includes.  Example is:
    { '<Interface>/': ['<TimeSeries>/'], '<Module>/': ['<Interface>/']}
    Rule is if source_id is in top_nodes (e.g. Interface, TimeSeries), target_id should become
    before the source.  If source_id is in promoted_nodes (Module), it should come immediately
    before target_id."""
    # split collapsed_includes pairs into two dicts, one for top_nodes, one for promoted_nodes
    top_ci = {}
    pro_ci = {}
    for source in collapsed_includes:
        assert len(collapsed_includes[source]) == 1, "more than one included class for source %s: %s" %(
            source, collapsed_includes[source])
        target = collapsed_includes[source][0]
        assert target in top_nodes
        if source in top_nodes:
            top_ci[source] = target
        elif source in promoted_nodes:
            pro_ci[source] = target
        else:
            print "collapsed_includes source %s not in top_nodes %s or promoted_nodes %s" % (
                source, top_nodes, promoted_nodes)
    tc_top_order = []
    # process all top_nodes first since promoted nodes must be placed immediately in
    # front of corresponding top_node
    for source in top_ci:
        target = top_ci[source]
        add_to_list(tc_top_order, target, source)  # add target before source
    # now process all promoted_nodes
    for source in pro_ci:
        target = pro_ci[source]
        add_to_list(tc_top_order, source, target)  # add source before target
    return tc_top_order
        
def add_to_list(arr, v1, v2):
    """ Add v1 and v2 to list 'arr'.  First check if v2 is in list.  If not,
    append it.  Then insert v1 in front of v2.  Final result is that v1 is
    before v2.
    """
    if v2 not in arr:
        arr.append(v2)
    idx = arr.index(v2)
    arr.insert(idx, v1)

def get_new_ids2(tcids, ids_adding):
    """Given id's in table of contents (tcids), return a list of new ids that can
    be added to table of contents based on the id's present.  The new ids are sources
    that have targets which are all in tcids.  However, do not return any ids in ids_adding
    because those are already in the process of being added.
    """
    # global source_to_expanded_targets
    global merges_to_expanded_targets
    new_ids = []
    for id in merges_to_expanded_targets:
        if id not in tcids and id not in ids_adding:
            targets = merges_to_expanded_targets[id]
            found_all = True
            for target in targets:
                if target not in tcids:
                    found_all = False
                    break
            if found_all:
                new_ids.append(id)
    return new_ids

def add_to_tc2(id, level, tc, tcids, ids_adding):
    """add id to table of contents.
    id - id to add.
    level - indentation level for id.
    tc - table of contents.  Is a list of form:
        [(id1 level1) (id2 level2), ...]
    tcids - ids in table of contents
    ids_adding - id's that are currently being added to table of contents
        but are not yet stored in it.
    """
    # global expanded_targets_to_sources
    # add id to table of contents and tcids
    tc.append((id, level))
    tcids.append(id)
    if id in ids_adding:
        ids_adding.remove(id)
    # check for new id's to add
    new_ids = get_new_ids2(tcids, ids_adding)
    ids_adding.extend(new_ids)
    for new_id in sorted(new_ids):
        add_to_tc2(new_id, level+1, tc, tcids, ids_adding)


def build_tc2(tc_top_order):
    """Build table of contents listing id's ordered hierarchically under the
    id's that they depend on.  tc_top_order are the top level id's in the
    table of contents.  Returns:
    tc - table of contents.  List of form: [(id1 level1) (id2 level2), ...]
    tcids - list of id that were added to table of contents).
    """
    tc = []
    tcids = []
    level = 1
    for top_id in tc_top_order:
        ids_adding = []
        add_to_tc2(top_id, level, tc, tcids, ids_adding)
    rv = (tc, tcids)
    return rv


def make_id_order_tree():
    """ uses merges_found and includes_found (both of which map an id to a target_id)
    to create a tree with order of id's to display, so that id's are displayed before
    those that depend on them.  This used to make the table of contents and also to
    order the inclusion of id's in the generated documentation."""
    global merges_found, includes_found, expanded_targets_to_sources
    global source_to_expanded_targets
    global merges_to_expanded_targets
    # combine merges_found and includes_found
#     print "merges found:"
#     pp.pprint(merges_found)
#     print "includes found:"
#     pp.pprint(includes_found)
    source_to_target = {}
    combine_dict_arrays(source_to_target, merges_found)
    combine_dict_arrays(source_to_target, includes_found)
    # make a reverse list, target_to_source
    target_to_source = {}
    for key in source_to_target:
        values = source_to_target[key]
        for value in values:
            add_to_dict_array(target_to_source, value, key)
#     print "source_to_target:"
#     pp.pprint(source_to_target)
#     print "target_to_source:"
#     pp.pprint(target_to_source)
    # top_nodes are those that are targets but not sources
    top_nodes = []
    for node in target_to_source:
        if node not in source_to_target:
            top_nodes.append(node)
#    print "top nodes: %s" % top_nodes
    # promoted_nodes (as computed below) are groups that are source of a top_node, but are
    # not source of a merge; hence must be source of an include to a top_node
    promoted_nodes = []
    for tn in top_nodes:
        promoted_nodes.extend([ x for x in target_to_source[tn] if x not in merges_found.keys()])
#    print "promoted_nodes: %s" % promoted_nodes
    top_and_promoted = top_nodes + promoted_nodes
    collapsed_includes = collapse_includes_found(top_and_promoted)
    tc_top_order = get_tc_top_order(collapsed_includes, top_nodes, promoted_nodes)
#    print "tc_top_order=%s" % tc_top_order
    source_to_expanded_targets = expand_targets(source_to_target)
#     print "\n\nsource_to_expanded_targets ="
#     pp.pprint(source_to_expanded_targets)
    # make dependency group - expanded_targets_to_sources
    make_expanded_targets_to_sources(source_to_expanded_targets)
#     print "\n\nexpanded_targets_to_sources ="
#     pp.pprint(expanded_targets_to_sources)
    merges_to_expanded_targets = expand_targets(merges_found)
    rv = build_tc2(tc_top_order)
    tc, tcids = rv
#     print "\nTable of contents2:"
#     pp.pprint(tc)
#     import pdb; pdb.set_trace()
    # build table of contents based on top nodes
#    rv = build_tc(top_nodes)
    # rv = build_tc(top_and_promoted)
#    tc, tcids = rv
#     print "\nTable of contents:"
#     pp.pprint(tc)
    return rv
    
#   #build table of contents for each top node
#     tcs = {}
#     for id in top_nodes:
#         tl = []
#         tc = []
#         found_ids=[]
#         level = 0
#         add_to_tc(tl, id, level, tc, found_ids)
#         tcs[id] = {'tc': tc, 'found_ids': found_ids}
#     print "\nfound table of contents:"
#     pp.pprint(tcs)
    
    

def make_doc(f):
    """ Main routine for generating documentation.
    """
    global h5gate_file
    # save in global variable for Id_doc routines (so do not have to pass it as parameter)
    h5gate_file = f
    doc_parts = {
        'header': [],
        'toc': [], # table of contents
        'main': [], # main documentation
        'footer': [], # end of documentation
    }
    doc_source = ", ".join(f.spec_files) if f.spec_files else os.path.basename(f.file_name)
    title = "%s documentation" % doc_source
    header = doc_parts['header']  # convenient for appending
    header.append(make_header(title))
    header.append('<div style="text-align: center">')
    header.append(font_size(12, "Documentation for: %s" % doc_source))
    # following has default namespace last
    name_spaces = f.name_spaces
    # make default namespace first and sort all others
    if len(name_spaces) > 1:
        name_spaces = [name_spaces[-1]] + sorted(name_spaces[0:-1])    
    for ns in name_spaces:
        color = ns_color(f, ns)
        file_name = os.path.basename(f.ddef[ns]['file_name'])
        name = f.ddef[ns]['info']['name']
        version = f.ddef[ns]['info']['version']
        date = f.ddef[ns]['info']['date']
        header.append("<br /><br />\n")
        header.append(font_size(22, name) + "<br />")
        version_str = "Version %s, %s" % (version, date)
        header.append(font_size(12, version_str) + "<br />")
        cns = ("<span style=\"background-color: "
            "%s;\">%s</span>") % (color, ns) if color else ns
        ns_str = "(File '%s', namespace '%s')" % (file_name, cns)
        header.append(font_size(10, ns_str) + "\n")
    header.append("</div>")
        
#         ns_info = ("<center>\n<span class=\"fs26\">%s</span><br />"
#             "<span class=\"fs20\">Version %s, %s</span><br />\n"
#             "(namespace '%s', file '%s').\n</center>") % (name, version, date, ns, file_name)
#         doc_parts['header'].append(ns_info)
    
#     title = "Documentation for specification file(s): '%s'" % (
#         f.spec_files)
#     title = f.ddef[f.default_ns]['info']['name']
#     version = f.ddef[f.default_ns]['info']['version']
#     header = make_header(title)
#     doc_parts['header'].append(header)
#     doc_parts['header'].append("<center><h1>%s</h1></center>" % title)
#     doc_parts['header'].append("<center><font style=""font-size:16pt"">Version %s</font></center>" % version)
    doc_parts['toc'].append("<h2>Table of contents</h2>")
    # dictionary mapping each id (in schema) to html documentation for it
    ids_documented = {}
    root_toc, tree_toc, id_toc, orphan_toc, other_toc = make_tree_doc(f, ids_documented)
    all_toc = ["_toc_top"] + root_toc + id_toc + tree_toc + orphan_toc + other_toc + ["_toc_bottom"]
    add_fs_doc(f, all_toc, ids_documented)
    add_id_doc(doc_parts, all_toc, ids_documented)
    footer = "</body>\n</html>"
    doc_parts['footer'].append(footer)
    # done build doc_parts, now make document
    html = "\n".join(doc_parts['header'] + doc_parts['toc'] + doc_parts['main'] + doc_parts['footer'])
    return html

# def add_id_doc_indent(doc_parts, toc, ids_documented):
#     """ Add documentation for ids listed in 'toc' (table of contents) to the 'toc' and
#     'main' sections of doc_parts"""
#     for id in toc:
#         if id not in ids_documented:
#             # assume is a position label, e.g. "_toc_top".  Ignore it
#             continue
#         idoc = ids_documented[id]
#         level = idoc.level
#         link = idoc.make_toc_link()
#         main_doc = idoc.make_doc()
#         indent = (" &nbsp; &nbsp; " * level)
#         # bullet simulates <ul> and </ul> without requiring <li> nested properly
#         bullet = html_list_bullet(level - 2) + " &nbsp; " if level >= 2 else ""
#         toc_entry = indent + bullet + link + "<br />"
#         doc_parts['toc'].append(toc_entry)
#         doc_parts['main'].append(main_doc)


def add_id_doc(doc_parts, toc, ids_documented):
    """ Add documentation for ids listed in 'toc' (table of contents) to the 'toc' and
    'main' sections of doc_parts.  For table of contents, use html unordered lists <li>
    to make indentation if indentation level is >= 2, otherwise, if level is
    0 or 1, just use spaces to indent. """
    prev_level = None
    ul_count = 0
    for id in toc:
        if id not in ids_documented:
            # assume is a position label, e.g. "_toc_top".  Ignore it
            continue
        idoc = ids_documented[id]
        link = idoc.make_toc_link()
        level = idoc.level
        increase_indent = prev_level is None or level > prev_level
        decrease_indent = prev_level is not None and level < prev_level
        same_indent = prev_level is not None and level == prev_level
        if prev_level > 1 and decrease_indent:
            close_toc_ul(doc_parts, level, prev_level)
        if level >= 2:
            # only use <ul> for level >= 2
            if increase_indent:
                doc_parts['toc'].append('<ul>')
            elif decrease_indent:
                # already handled above
                pass
            elif same_indent:
                doc_parts['toc'][-1] += '</li>'
            else:
                exit("Unexpected indentation when making table of contents")
            toc_entry = "<li>%s" % link
        else:
            # not using <ul>, just spaces indentation
            toc_entry = (" &nbsp; &nbsp; " * level) + link + "<br />"
        doc_parts['toc'].append(toc_entry)
        main_doc = idoc.make_doc()
        doc_parts['main'].append(main_doc)
        prev_level = level
    if prev_level > 1:
        close_toc_ul(doc_parts, 1, prev_level)

def close_toc_ul(doc_parts, level, prev_level):
    """ Output </li> and </ul> tags needed to decrease table of contents
    indent from prev_level to level, if level > 1 (e.g. using <ul>). """
    close_count = prev_level - max(1, level)
    for i in range(close_count):
        doc_parts['toc'][-1] += '</li>'
        doc_parts['toc'].append('</ul>')


# def add_id_doc_orig(doc_parts, toc, ids_documented):
#     """ Add documentation for ids listed in 'toc' (table of contents) to the 'toc' and
#     'main' sections of doc_parts"""
#     prev_level = None
#     for id in toc:
#         if id not in ids_documented:
#             # assume is a position label, e.g. "_toc_top".  Ignore it
#             continue
#         idoc = ids_documented[id]
#         level = idoc.level
#         if not prev_level:
#             prev_level = level
#         if level > prev_level and level >= 2:
#             doc_parts['toc'].append('<ul>')
#         elif level < prev_level and prev_level >= 2:
#             doc_parts['toc'].append('</ul>')
#         main_doc = idoc.make_doc()
#         link = idoc.make_toc_link()
# #         safe_id = cgi.escape(id)
# #         link = "<a href=\"#%s\">%s</a>" % (safe_id, safe_id)
# #         anchor = "<a name=\"%s\"></a>\n" % safe_id
#         toc_entry = "<li>%s</li>" % link if level >= 2 else (" &nbsp; &nbsp; " * level) + link + "<br />"
#         doc_parts['toc'].append(toc_entry)
#         doc_parts['main'].append(main_doc)
#         prev_level = level
#     while level >= 2:
#         doc_parts['toc'].append('</ul>')
#         level = level - 1

def add_fs_doc(f, toc, ids_documented):
    """ Add any documentation provided in "doc" section of format specification."""
    for ns in f.ddef.keys():
        if "doc" in f.ddef[ns]:
            fs_doc = f.ddef[ns]['doc']
            for dinfo in fs_doc:
                insert_doc_content(dinfo, toc, ids_documented, ns)

                
def insert_doc_content(dinfo, toc, ids_documented, ns):
    """Insert documentation stored in format specification "doc" section into
    id's listed in table of contents, or into table of contents itself"""
    doc_id = dinfo['id']
    location = dinfo['location']
    content = add_css(dinfo['content'])
    lid = location['id']
    if lid not in toc:
        print "namespace: %s, doc id '%s' location id '%s' not in table of contents" %(
            ns, doc_id, lid)
        traceback.print_stack()
        import pdb; pdb.set_trace()
    position = location['position']
    if position in ('before', 'after'):
        # doc inserted as new entry in table of contents.  Make new Id_doc object
        lindex = toc.index(lid)
        level = dinfo['level']
        idoc = Id_doc(doc_id, [content,], level=level)
        ids_documented[doc_id] = idoc
        # insert id into table of contents, either before or after location id
        insert_index = lindex if position == "before" else lindex+1
        toc.insert(insert_index, doc_id)
        return
    # doc not inserted as a new entry in table of contents; but instead inserted into
    # into documentation for an existing id.  Get Id_doc for that id it's inserted into
    idoc = ids_documented[lid]
    if position == "pre":
        # content goes in "pre_text" part of lid
        idoc.pre_text.append(content)
    elif position == "mid":
        # content goes in "mid_text" part of lid
        idoc.mid_text.append(content)
    elif position == "post":
        # content goes in "post_text" part of lid
        idoc.post_text.append(content)
    else:
        print "namespace: %s, doc id '%s' location '%s', position '%s' not implemented." % (
            ns, doc_id, location, position)
        sys.exit(1)


def ns_color(f, ns):
    """ Return color associated with namespace ns.  Color is used to highlight
    specification parts from extensions."""
    if ns == f.default_ns:
        # no color for default namespace
        return None
    colors = ["LawnGreen", "LightSkyBlue", "MediumOrchid", "RoyalBlue", "Magenta"]
    name_spaces = f.name_spaces  # default_ns will always be last
    num_extensions = len(name_spaces) - 1
    assert num_extensions <= len(colors), ("More extensions (%i) than colors (%i).  "
        "Modify routine ns_color to add more colors.") % (num_extensions, len(colors))
    idx = name_spaces.index(ns)
    color = colors[idx]
    return color

def make_safe_anchor(text):
    """ replace spaces by underscore then url escape special chars"""
    safe_anchor = urllib.quote(remove_spaces(text))
    return safe_anchor


class Id_doc(object):
    """ Class for documentation about an individual id.  Usually this corresponds to
    a group or dataset in the schema.  But it can also include headers that are added
    to the table of contents and the document."""
    def __init__(self, anchor, content, level=None, toc_label=None, doc_label=None, pre_text=None,
        mid_text=None, post_text=None, namespaces=None):
        """
        anchor - used to link from table of contents to item in document.  Also used
            as key in ids_documented.
        content - list containing main content of documentation for item (usually a table)
        level     - level of indentation in table of contents
        toc_label - displayed label in table of contents
        doc_label - displayed label (header) in document
        pre_text  - text to display before label in document
        mid_text  - text to display between label in document and content
        post_text - text to display after content for item
        namespaces - list of namespaces that are used.  Used to create namespaces
            appended to table of contents entry.
        """
        global h5gate_file
        self.file = h5gate_file
        self.anchor = anchor   # used to link from table of contents to item in document
#         if 'newds' in anchor:  # == '/now/for/something/newds':
#             import pdb; pdb.set_trace()
        self.content = content  
        self.level = level     # level of indentation in table of contents
        self.toc_label = toc_label if toc_label else anchor
        self.doc_label = doc_label if doc_label else anchor
        self.pre_text = pre_text if post_text is not None else []
        self.mid_text = mid_text if mid_text is not None else []
        self.post_text = post_text if post_text is not None else []
        self.namespaces = namespaces if namespaces is not None else []
        self.toc_link = None
        self.doc = None

    def make_safe_anchor(self):
        """remove angle brackets, replace spaces by underscore, escape any special chars"""
        return make_safe_anchor(self.anchor)
        # safe_anchor = urllib.quote(remove_spaces(self.anchor))
        # safe_anchor = html_escape(remove_spaces(self.anchor))
        # return safe_anchor

    def make_nslist(self):
        """Make list namespaces referenced.  This appended to table of contents
        entry.  Namespace are color highlighted."""
        f = self.file
        nsl = []
        for ns in self.namespaces:
            color = ns_color(f, ns)
            html = "<span style=\"background-color: %s;\">%s</span>" % (color, ns)
            nsl.append(html)
        nsl = ", ".join(nsl)
        if nsl:
            nsl = "&nbsp; " + nsl
        return nsl
        
    def make_toc_link(self):
        """ Generate link text for table of contents"""
        safe_anchor = self.make_safe_anchor()
        safe_label = cgi.escape(self.toc_label)
        if self.level == 0:
            # make labels at level 0 in table of contents bold
            safe_label = "<b>%s</b>" % safe_label
        nslist = self.make_nslist()
        self.toc_link = "<a href=\"#%s\">%s%s</a>" % (safe_anchor, safe_label, nslist)
        return self.toc_link

   
    def get_subclass(self):
        """ Return id of most immediate subclass of qid, to use in
        "extends subclass" clause in heading.  Subclass is only returned if
        it's not abstract.  This is so the  "extends x" clause is only shown
        when a non-abstract class is subclassed.
        """
        global merges_found
        f = self.file
        id = self.anchor
        idg = id + "/"  # id's in merges_found have a trailing slash
        if idg in merges_found:
            subclass = merges_found[idg][0]
            sdef = f.get_sdef(subclass, f.default_ns, "called from get_subclass")
            df = sdef['df']
            abstract = f.is_abstract(df)
            if not abstract:
                return subclass.rstrip('/')
        return None
        
        
    def make_doc(self):
        """ Generate documentation for id to go in main body of document.  Include anchor"""
        safe_anchor = self.make_safe_anchor()
        subclass = self.get_subclass()
        if subclass:
            # safe_sc = html_escape(subclass)
            # sc_link = "<a href=\"#%s\">%s</a>" % (safe_sc, safe_sc)
            sc_link = "<a href=\"#%s\">%s</a>" % (make_safe_anchor(subclass), cgi.escape(subclass))
            extends_text = " extends %s" % sc_link
        else:
            extends_text = ""
        safe_label = cgi.escape(self.doc_label) + extends_text
        anchor_text = "<a name=\"%s\">&nbsp;</a>\n" % safe_anchor
        # make label <h2> if it's level zero in table of contents, else <h3>
        label_size = 2 if self.level == 0 else 3
        # label_text = "<h%i>%s%s</h%i>" % (label_size, safe_label, anchor_text, label_size)
        # label_text = "<h%i id=\"%s\">%s</h%i>" % (label_size, safe_anchor, safe_label, label_size)
        safe_id = remove_spaces(self.anchor)
        label_text = "<h%i id=\"%s\">%s</h%i>" % (label_size, safe_id, safe_label, label_size)
        # label_text = "<h3>%s</h3>" % safe_label
        # put the a anchor around the label.  This seems to be needed for: wkhtmltopdf
        # anchor_label = "<a name=\"%s\">%s</a>\n" % (safe_anchor, label_text)
        # self.doc = "\n".join(self.pre_text + [label_text, anchor_text] +
        self.doc = "\n".join(self.pre_text + [ label_text ] +
            self.mid_text + self.content + self.post_text)
        return self.doc
        
#     def remove_spaces(self, str):
#         """ Replace any spaces with underscore.  This for links."""
#         return re.sub(" ","_",str)
        
def remove_spaces(str):
    """ Replace any spaces with underscore.  This for links."""
    return re.sub(" ","_",str)
    
def save_id_doc(id, doc, level, toc, ids_documented, doc_label=None, namespaces=None):
    """ Save documentation about id both in table of contents array (toc) and in
    ids_documented"""
    idoc = Id_doc(id, doc, level, doc_label=doc_label, namespaces=namespaces)
    toc.append(id)
    ids_documented[id] = idoc  
    
def save_label(label, toc, ids_documented):
    """Save label in table of contents and in ids_documented"""
    level = 0
    id = label
    doc = []
    save_id_doc(id, doc, level, toc, ids_documented)


# def save_id_doc_old(id, doc, level, toc, ids_documented):
#     """ Save documentation about id both in table of contents array (toc) and in
#     ids_documented"""
#     item = (id, level)
#     toc.append(item)
#     ids_documented[id] = "\n".join(doc)
# 
# def save_label_old(label, toc, ids_documented):
#     """Save label in table of contents and in ids_documented"""
#     level = 0
#     id = label
#     doc = []
#     doc.append("<h2>%s</h2>" % label)
#     save_id_doc(id, doc, level, toc, ids_documented)

class Table(object):
    """ Class for creating html tables documenting groups or datasets.
    Needs to be a class so can determine if comments are in description
    before creating the table.  file is h5gate file object."""
    def __init__(self, file, filter=None):
        self.file = file
        self.rows = []
        self.has_comment = None
        self.header_keys = None
        self.html = []
        self.dimensions = {}
        self.cmt_str = "COMMENT:"
        self.filter = filter  # group, dataset or none
        self.required_messages = []
        self.exclude_ids = None
        self.closed_ids = []
        # self.more_info_str = "MORE_INFO:"
        
    def add(self, id, id_str, type, description, required, ns=None, override=None, closed=False):
        """Add a row to the table.
        id - actual id (key) for member.
        id_str - string to display for id.  Might include indentation.
        type - usually "group" or dataset data type.  Could be link, maybe others.
        description - description displayed, also may include comments separated by "COMMENT:"
        required - displayed in required column.  Usually "Yes" or "No".
        ns - namespace associated with item.  Used to display namespace if it's not the default
            (i.e. is from an extension).
        override - True if this item overrides one in a subclass (because of merge).  False otherwise.
        closed - True if this is a closed group (specified by '_closed': True). False otherwise
        """
        row = {'id': id, 'Id':id_str, 'Type':type, 'Description':description, 'Required':required,
            'ns': ns, 'override': override, 'closed': closed}
        self.rows.append(row)
        
    def save_required_message(self, ids, message):
        self.required_messages.append((ids, message))
        
    def save_exclude_ids(self, exclude_ids):
        self.exclude_ids = exclude_ids
        
    def get_has_comment(self):
        if self.has_comment is None:
            self.has_comment = False
            for row in self.rows:
                if self.cmt_str in row['Description']:
                    self.has_comment = True
                    break
        return self.has_comment

    def get_header_keys(self):
        """ Returns list of header keys based on type of table"""
        hk = ["Id",]
        if self.filter != "group":
            hk.append("Type")
        hk.append("Description")
        if self.get_has_comment():
            hk.append("Comment")
        hk.append("Required")
        self.header_keys = hk
                
    def make_header(self):
        self.get_header_keys()
        header = "<table class=\"print-friendly\">\n<tr>" + "".join(["<th>%s</th>" %
            key for key in self.header_keys]) + "</tr>"
        self.html.append(header)
                     
#         if self.get_has_comment():
#             header = ("<tr><th>id</th><th>type</th><th>description</th>"
#                 "<th>comment</th><th>required</th></tr>")
#         else:
#             header = "<tr><th>id</th><th>type</th><th>description</th><th>required</th></tr>"
#         self.html.append(header)
        
    def get_description_comment(self, description):
        """Splits description into description and comments"""
        assert self.has_comment, "get_description_comment called, but no comments found"
        # idx_more_info = description.find(self.more_info_str)
        # end_desc_idx = idx_more_info if idx_more_info != -1 else len(description)
        idx_comment = description.find(self.cmt_str)
        if idx_comment != -1:
            comment = description[idx_comment + len(self.cmt_str):] # end_desc_idx]
            description = description[0:idx_comment]
        else:
            comment = "&nbsp;"
            description = description[0:] # end_desc_idx]
        return (description, comment)

    def get_required_message(self, id):
        """ returns message in '_required' clause if id is in any _required condition"""
        if self.required_messages:
            msgs = []
            for ids_msg in self.required_messages:
                if id in ids_msg[0]:
                    msgs.append(ids_msg[1])
            return add_css('; '.join(msgs))
        return ''
        
    def get_exclude_message(self, id):
        """ returns message describing exclusion if id is in any _exclude_in specification"""
        if not self.exclude_ids or id not in self.exclude_ids:
            return ''
        phrases = { '!':'must not be present', '^':'should not be present', '?':'optional'}
        msgs = []
        for pq in self.exclude_ids[id]:
            [path, qty] = pq
            msg = "%s under '%s'" % (phrases[qty], path)
            msgs.append(msg)
        msgs = '; '.join(msgs) + "."
        msgs = msgs[0].upper() + msgs[1:] # capitalize first character
        return msgs

    def get_closed_message(self, row):
        """ return message indicating group is closed if closed was specified."""
        msg = 'This group is closed (no additional members allowed).' if row['closed'] else ''
        return msg
    
    def get_id_css(self, id_str, ns, override):
        """ if either an extension namespace or subclass override is specified
        add css style to the id_str.  Colors for namespace, underline for
        override."""
        css = []
        color = ns_color(self.file, ns) if ns else None
        if color:
            css.append("background-color: %s" % color)
        if override:
            css.append("text-decoration: underline;")
        css = "; ".join(css)
        if css:
            css_str = "<span style=\"%s\">%s</span>" % (css, id_str)
            return css_str
        return None
        
    
    def make_table(self):
        self.make_header()
        for row in self.rows:
            tmp_row = dict(row)  # make copy so don't change original
            ns = tmp_row['ns']
            override = tmp_row['override']
            css_style = self.get_id_css(tmp_row['Id'], ns, override)
            if css_style:
                tmp_row['Id'] = css_style
            id = row['id']
            required_message = self.get_required_message(id)
            exclude_message = self.get_exclude_message(id)
            # closed message only applies to first row since it's for the entire group
            closed_message = self.get_closed_message(tmp_row)
            qualifier_message = " ".join([m for m in [required_message, exclude_message, closed_message] if m])
            if qualifier_message:
                tmp_row['Description'] = tmp_row['Description'] + " <b>%s</b>" % qualifier_message
            if self.has_comment:
                description = tmp_row['Description']
                description, comment = self.get_description_comment(description)
                if comment == "&nbsp;":
                    dc_html = "<td colspan=\"2\">%s</td>" % description
                else:
                    dc_html = "<td>%s</td><td>%s</td>" % (description, comment)
            else:
                dc_html = "<td>%s</td>" % tmp_row['Description']
#                 tmp_row['Description'] = description
#                 tmp_row['Comment'] = comment
#             trow = ("<tr>" + "".join(["<td>%s</td>" % tmp_row[k]
#                 for k in self.header_keys]) + "</tr>")
            trow = "<tr>"
            for k in self.header_keys:
                if k == "Description":
                    trow = trow + dc_html
                elif k == "Comment":
                    # any comment added by dc_html
                    continue
                else:
                    trow = trow + ("<td>%s</td>" % tmp_row[k])
            trow = trow + "</tr>"
            self.html.append(trow)
        self.html.append("</table>")
        self.format_dimensions()
        return "\n".join(self.html)
        
    def namespaces(self):
        """Return list of name spaces other than default_ns referenced in table"""
        ns_list = []
        for row in self.rows:
            ns = row['ns']
            if ns and ns != self.file.default_ns and ns not in ns_list:
                ns_list.append(ns)
        return sorted(ns_list)


        
    def add_dimension(self, dname, dim_def):
        """ Add definition of explicitly defined dimension so can display at end of table"""
        self.dimensions[dname] = dim_def
        
    def format_dimensions(self):
        """ create table with dimensions and components.  dimensions will have one set of
        components, "type 1": like:
        {   'whd': {   'components': [   {   'alias': 'width', 'unit': 'meter'},
                                 {   'alias': 'height', 'unit': 'meter'},
                                 {   'alias': 'depth', 'unit': 'meter'}],
                'type': 'struct'}}
        *OR* multiple component options "type 2", looks like:
        {   'fov': {   'components': [   [   {   'alias': 'width', 'unit': 'meter'},
                                     {   'alias': 'height', 'unit': 'meter'}],
                                 [   {   'alias': 'width', 'unit': 'meter'},
                                     {   'alias': 'height', 'unit': 'meter'},
                                     {   'alias': 'depth', 'unit': 'meter'}]],
               'type': 'structure'}}
               
        First form, components is is a list of dicts
        Second form, components is a a list of list of dicts
        """
        if not self.dimensions:
            return
        # find largest number of components
        # and convert all dimensions to a standard form, like:
        # [ [name, [option_1, option_2, ...]], [name, [option_1]] ... ]
        # where each option is a list of components (list of dicts, like type 1 above)
        sdc = []  # stands for "standard dimension components"
        max_num_components = 0
        for dname in sorted(self.dimensions.keys()):
            dinfo = self.dimensions[dname]
            components = dinfo['components']
            has_options = isinstance(components[0], list)
            if has_options:
                # more than one component option (type 2 above)
                sdc.append([dname, components] )
                for option in components:
                    num_components = len(option)
                    if num_components > max_num_components:
                        max_num_components = num_components
            else:
                # only one option (type 1 above)
                sdc.append([dname, [components,]])
                num_components = len(components)
                if num_components > max_num_components:
                    max_num_components = num_components
            title = "<br />\n<p>Structured dimension(s):</p>"
            self.html.append(title)
#             dinfo = add_css_to_escaped_html(str(pp.pformat(self.dimensions)))
#             dinfo = ("<pre>\n%s\nNum components=%i\nsdc=%s</pre>") % (dinfo,
#                 max_num_components, pp.pformat(sdc))
#             self.html.append(dinfo)
            tbl = []
            tbl.append("<table class=\"dimensions\">")
            span_cols = max_num_components
            tbl.append("<tr><th>Dimension</th><th colspan=\"%i\">Components "
                "<span class=\"notbold\">[ name (unit) ]</span></th></tr>" % (
                max_num_components))
            for dco in sdc:
                dname, options = dco
                opt_num = 0
                for components in options:
                    opt_num = opt_num + 1
                    opt_str = " (option %i)" % opt_num if len(options) > 1 else "" 
                    tr = "<tr><td>%s%s</td>" % (dname, opt_str)
                    for component in components:
                        cname = get_element(component, 'alias', "*alias missing*")
                        cunit = get_element(component, 'unit', "*unit missing*")
                        nu = "<td>%s (%s)</td>" % (cname, cunit)
                        tr = tr + nu
                    # add in empty columns if this option did not have max_num_components
                    for i in range(max_num_components - len(components)):
                        tr = tr + "<td>&nbsp;</td>"
                    tr = tr + "</tr>"
                    tbl.append(tr)
            tbl.append("</table>")
            self.html.append("\n".join(tbl))
            
class Task_list(object):
    """Simple class for keeping track of a "to_do" and a "done" list,
    to make sure don't do the same task twice."""
    def __init__(self, initial_todo=[]):
        self.todo = initial_todo
        self.done = []
    
    def add(self, task):
        """Only add if not already done and not in todo list"""
        if task not in self.done and task not in self.todo:
            self.todo.append(task)
    
    def next(self):
        """Return next task from front of todo.  Put in done.  Return
        None of no more"""
        if self.todo:
            task = self.todo.pop(0)
            self.done.append(task)
            return task
    
    def more(self):
        """Return True if todo list is not empty."""
        return len(self.todo) > 0

        

def make_tree_doc(f, ids_documented):
    """ Build documentation about node_tree.  Store documentation about each
    id in schema in dict ids_documented (maps id to documentation for id.
    Returns table of contents for: id's that are an absolute path (root_toc and
    tree_toc), id's that are not an absolute path but are referenced (id_toc)
    and other id's (other_toc).
    """
    global merges_found, includes_found, avid_nodes
    starting_group = f.node_tree;
    to_process = [starting_group,]
    # add in "av_id" groups directly since these may not be found when
    # to_process.extend(avid_nodes)
    grp_tl = Task_list(to_process)  # make task list of groups to process
    root_toc = []
    tree_toc = []
    level = 1
    save_label("File organization", tree_toc, ids_documented)
    while grp_tl.more():
        doc = []
        # grp = to_process.pop(0)
        # processed.append(grp)
        grp = grp_tl.next()  
        full_path = grp.full_path
        # print "processing %s" % full_path
        if full_path == "/":
            # for root group, separate members into top-level groups and datasets
            id = "Top level groups"
            # doc.append("<h2>%s</h2>" % id)
            mlevel = 0
            tbl = process_top_group_members(f, grp, mlevel, ids_documented, grp_tl, filter="group")
            doc.append(tbl.make_table())
            save_id_doc(id, doc, level, root_toc, ids_documented, namespaces=tbl.namespaces())
            doc = []
            id = "Top level datasets"
            # doc.append("<h2>%s</h2>" % id)
            tbl = process_top_group_members(f, grp, mlevel, ids_documented, grp_tl, filter="dataset")
            doc.append(tbl.make_table())
            save_id_doc(id, doc, level, root_toc, ids_documented, namespaces=tbl.namespaces())
            continue
#         if grp in avid_nodes:
#             # this group is an av_id group (see function "find_av_ids" for an explanation)
#             # the id is set to the full path, but the last component replaced by the 
#             # variable id
#             path_prefix, name = f.get_name_from_full_path(full_path)
#             mid = grp.sdef['id']
#             v_id = re.match( r'^<[^>]+>/?$', mid) # True if variable_id (in < >)
#             assert v_id, "%s is avid_node, but id (%s) is not variable" % (full_path, mid)
#             id = f.make_full_path(path_prefix, mid)
#             import pdb; pdb.set_trace()
#         else:
        id = full_path
        # anchor = "<a name=\"%s\"></a>\n" % cgi.escape(full_path)
        # doc.append(anchor)
        # doc.append("<h3>Group: %s</h3>\n" % cgi.escape(full_path))
        doc_label = "Group: %s" % id
        df = grp.sdef['df']
        description = get_description(grp.sdef['df'], in_group=False)
        doc.append("<p>%s</p>\n" % description)
        if not grp.mstats and not grp.attributes:
            doc.append("<p>No members or attributes specified for this group</p>")
            save_id_doc(id, doc, level, tree_toc, ids_documented, doc_label)
            continue
        # this group has members and/or attributes, make a table of them
        tbl = process_top_group_members(f, grp, level, ids_documented, grp_tl)
        doc.append(tbl.make_table())
        save_id_doc(id, doc, level, tree_toc, ids_documented, doc_label, namespaces=tbl.namespaces())
    # process all avid nodes separately
    make_avid_doc(f, ids_documented)
    # done with fixed named groups at top level
#     print "stopping for now"
#     sys.exit(0)
    # sort the id's in the table of contents so they appear in depth first order
    # this based on:
    # http://stackoverflow.com/questions/29732298/file-paths-hierarchial-sort-in-python
    # std = sorted(tree_toc, key=lambda file: (os.path.dirname(file), os.path.basename(file)))
    tree_label = tree_toc.pop(0)  # keep label in front
    std = sorted(tree_toc, key=lambda id: id.split("/") + ["Z", "z", "z"])    
    tree_toc = [tree_label] + std
    # now create table of contents for ids documented that do not have absolute path
    id_toc = []
    # save_label("Class Hierarchies", id_toc, ids_documented)
    (tc, tcids) = make_id_order_tree()
    # convert from tc which has pairs like (id, level) to form that has just id's listed
    # and level stored in Id_doc object in ids_documented
    for item in tc:
        (id, level) = item
        id = remove_trailing_slash(id)
        id_toc.append(id)
        if id not in ids_documented:
            import pdb; pdb.set_trace()
        ids_documented[id].level = level
    # id_toc.extend(tc)
    # put any ids in ids_documented not yet included in a table of contents in ophan_toc
    all_tocs = root_toc + tree_toc + id_toc
    orphan_ids = []
    for id in ids_documented.keys():
        if id not in all_tocs:
            orphan_ids.append(id)
            # set table of contents level to 1, indenting from label below
            ids_documented[id].level = 1
    orphan_toc = []
    if orphan_ids:
        save_label("Ids not in a Class Hierarchy", orphan_toc, ids_documented)
        orphan_toc.extend(sorted(orphan_ids))
        # import pdb; pdb.set_trace()
    # check if there are any ids not documented
    other_toc = []
    undocumented_ids=[]
    global ids_used
    for ns in f.ddef.keys():
        structures = f.ddef[ns]['structures']
        for id in structures:
            # make qualified id (qualified by namespace if not default)
            pqid = "%s:%s" % (ns, id)
            cid = remove_trailing_slash(id)
            qid = cid if ns == f.default_ns else "%s:%s" % (ns, cid)
            if (qid not in ids_documented and cid not in ids_documented
                and qid != starting_group.full_path
                and pqid not in ids_used):
                undocumented_ids.append(qid)
    if undocumented_ids:
        save_label("Other documentation", other_toc, ids_documented)
        id = "Undocumented ID's"
        doc = []
        # doc.append("<h2>**** Undocumented ID's ****</h2>")
        doc_label = "**** Undocumented ID's ****"
        doc.append(cgi.escape(str(undocumented_ids)))
        save_id_doc(id, doc, level, other_toc, ids_documented, doc_label)
#     doc = []
#     id = "merges found"
#     # doc.append("<h2>***** merges_found*****</h2>")
#     doc.append("\n<pre>\n%s\n</pre>\n" % cgi.escape(str(pp.pformat(merges_found))))
#     save_id_doc(id, doc, level, other_toc, ids_documented)
#     doc = []
#     id = "includes found"
#     # doc.append("<h2>***** includes_found*****</h2>")
#     doc.append("\n<pre>\n%s\n</pre>\n" % cgi.escape(str(pp.pformat(includes_found))))
#     save_id_doc(id, doc, level, other_toc, ids_documented)
    # finally, return the toc's
    return (root_toc, tree_toc, id_toc, orphan_toc, other_toc)
#     doc.append("<h2>**** ID definitions ****</h2>")
#     for id in sorted(ids_documented.keys()):
#         doc.append(ids_documented[id])
#     doc.append("</body>\n</html>")
    # make_id_order_tree()
    # sys.exit(0)
#     doc = "\n".join(doc)
#     return doc


    
def process_top_group_members(f, grp, level, ids_documented, grp_tl, filter=None):
    """ Generate table of documentation for members in "top-level" (i.e. group that has
    a known absolute path specified in the schema.  This called from function
    make_tree_doc.  grp_tl is a "task list" of groups to processes.
    Return table object.
    """
    df = grp.sdef['df']
    tbl = Table(f, filter=filter)
    if filter is None or filter is 'group':
        # make 'id_info' structure needed by add_attributes
        id_info = { 'df':df, 'created':[grp]}
        add_attributes(f, id_info, tbl, level)
        # add_attributes(f, df, tbl, level+1)
#     include_list = []
#     if 'include' in df:
#         for mid in df['include']:
#             include_list.append(mid.rstrip("?*!+^"))
    for mid in sorted(grp.mstats.keys()):
        id_info = grp.mstats[mid]
        # import pdb; pdb.set_trace()
        mtype = id_info['type']
        if filter and filter != mtype:
            continue
        mdf = id_info['df']
        mns = id_info['ns']
        mqty = id_info['qty']
#         if mid == "general/":
#             import pdb; pdb.set_trace()
        # make qualified id (qualified by namespace if not default)
        # mqid = mid if mns == f.default_ns else "%s:%s" % (mns, mid)
        # added_by_include = mqid in include_list or '_source_id' in mdf
        # added_by_include = mid in grp.includes
        added_by_include = 'include_info' in id_info
        id_path = f.make_full_path(grp.full_path, mid)
        # returns ns if this is an "av_id" otherwise None
        avid_ns = get_avid_ns(f, id_path)
#         if added_by_include != added_by_include2:
#             print "added by includes are different"
#             import pdb; pdb.set_trace()
        if mtype == 'dataset':
            # always include details about datasets in table for group
            add_dataset_doc(f, mid, id_info, tbl, level)
            continue
        if not added_by_include and not avid_ns:
            # group not added by include and also not an "av_id"
            # Include all of it (all members) in this table
            add_group_doc(f, mid, id_info, tbl, level, ids_documented, mode="in_group")
            continue
        required = make_required_from_qty(mqty)
        # more_info = filter is None  # don't trim if this is for top-level groups or datasets                
        # description = get_description(mdf, more_info=more_info)
        in_group = filter is not None
        description = get_description(mdf, in_group=in_group)
        v_id = re.match( r'^<[^>]+>/?$', mid) # True if variable_id (in < >)
        # if id_info['created'] and not v_id:
        if id_info['created'] and ((not v_id) or avid_ns):
            # todo:  need to better document exactly what is being done here
            # an instance of this id was created
            # It must be a group with a fixed name, added by include; make a link to it                   
            mg = id_info['created'][0]    
            # to_process.append(mg)
            grp_tl.add(mg)
            if avid_ns:
                print "added %s, avid_ns=%s" % (mg.full_path, avid_ns)
            mg_full_path = make_safe_anchor(remove_trailing_slash(mg.full_path))
            safe_id = cgi.escape(remove_trailing_slash(mid))
            id_link = "<a href=\"#%s\">%s</a>" % (mg_full_path, safe_id)
        else:
            # must be a relative-id group added by include  Make a link to it
            # id_link = "<a href=\"#%s\">%s</a>" % (safe_id, safe_id)
            id_link = make_link(mid)
        indent = ".&nbsp;" * level
        id_str = "%s%s" % (indent, id_link)
        override = 'source' in id_info and len(id_info['source']) > 1
        tbl.add(mid, id_str, mtype, description, required, mns, override)
#         doc.append("<tr><td>%s</td><td>%s</td><td>%s</td><td style=\"text-align:center\">%s</td></tr>" % (
#             id_link, mtype, description, required))
        # make documentation for id if needed
        # if present use _source_id for id in id_doc since that has the actual path to the item
        smid = mdf['_source_id'] if '_source_id' in mdf else mid
        # make sure it's a group.  mid could be early part of path, e.g. foo in /foo/bar/baz
        # mid will be group. The the actual item could be a dataset (baz does not have trailing slash).
        # Only make entry for group.  Datasets incorporated into table for parent group.
        if smid.endswith('/'):
            # this will make the documentation for top-level id's that are absolute path
            # print "calling make_id_doc from process_to_group_members, mid=%s, type=%s, smid=%s" % (mid, mtype, smid)
            make_id_doc(f, smid, id_info, ids_documented)
    # doc.append("</table>")
    return tbl
 
def remove_trailing_slash(id):
    """ Remove trailing slash if not root"""
    if id != '/':
       id = id.rstrip('/')
    return id
    
def make_link(id):
    """ Make link to target id"""
    idns = remove_trailing_slash(id)
    link = "<a href=\"#%s\">%s</a>" % (make_safe_anchor(idns), cgi.escape(idns))
    return link

def make_id_doc(f, id, id_info, ids_documented, sdef=None):
    """ make documentation about id.  Add to ids_documented (dict mapping id
    to documentation about id (an Id_doc object).  sdef is structure definition if
    obtained for id not created (not an absolute path without a variable-id).
    ids that are created in mstats have a absolute path, definition for
    them is in the mstats entry; sdef is not used.
    In any case, sdef only used to find overlapping definitions for variable-id
    items for merging extensions."""
    global merges_found
    # make qualified id (qualified by namespace if not default)
    ns = id_info['ns']
    qid = id if ns == f.default_ns else "%s:%s" % (ns, id)
    qid = remove_trailing_slash(qid)
    # if qid in ids_documented:
    # use id rather than qid so do not have namespaces in table of contents
    tcid = remove_trailing_slash(id)
    if tcid in ids_documented:
        # already have documented this id
        return
#     if "MyNew" in id:
#         print "in make_id_doc, id=%s" % id
#         import pdb; pdb.set_trace()
    # make entry to ids_documented so do not try to document this id again when processing members
    # ids_documented[qid] = "doc for %s being made" % qid
    ids_documented[tcid] = "doc for %s being made" % tcid
#     safe_id = cgi.escape(id)
    html = []
#     anchor = "<a name=\"%s\"></a>" % safe_id
#     html.append(anchor)
#     header = "<h2>%s</h2>" % safe_id
#     html.append(header)
    type = id_info['type']
    df = id_info['df']
    # qty = id_info['qty']
    # Check for extensions to merge in, if this is a relative id
    if id[0] != "/":
        # is relative id
        tsdef = sdef if sdef else {'id': id, 'ns':ns, 'df':df}
        to_merge = f.find_overlapping_structures(tsdef, None)
        if to_merge:
#             print "************"
#             print "%s: found overlapping structures: %s" % (id, to_merge)
            df = copy.deepcopy(df)  # make copy so don't modify original
            to_include = []
            id_sources = {}
#             print "before merge, df="
#             pp.pprint(df)
            f.process_merge(df, to_merge, to_include, id_sources, ns, qid)
#             print "after merge, df="
#             pp.pprint(df)
#             print "id_sources=%s" % id_sources
            id_info = dict(id_info)  # copy so don't change original
            id_info['df'] = df
            if to_include:
                # not sure what to do with to_include right now
                print "Did merge of %s into %s, found to_include=%s" % (
                    to_merge, qid, to_include)
                sys.exit(1)
    # description = cgi.escape(get_description(df, more_info=True))
    description = get_description(df, in_group=False)
    html.append("<p>%s</p>" % description)
    if type == 'group':
        merge = get_element(df, 'merge', None)
        # include = get_element(df, 'include', None)
        # required = get_element(df,'_required', None)
        if merge:
            ml = []
            for mqid in merge:
                # remove ns if it's the default_ns
                dns_id = mqid[len(f.default_ns)+1:] if mqid.startswith("%s:" % f.default_ns) else mqid
                # save merges found for later ordering id's and making table of contents
                if id in merges_found:
                    merges_found[id].append(dns_id)
                else:
                    merges_found[id] = [dns_id, ]
                # mlink = make_link(mqid)
                mlink = make_link(dns_id)
#                 safe_id = cgi.escape(remove_trailing_slash(mqid))
#                 mlink = "<a href=\"#%s\">%s</a>" % (safe_id.strip("<>"), safe_id)
#                 import pdb; pdb.set_trace()
                ml.append(mlink)
                # make sure documentation about this merged id is included
                mns, mid = f.parse_qid(mqid, ns)
                # make_vid_doc(f, mid, ids_documented)
                make_iid_doc(f, mid, mns, ids_documented)
#                 msdef = f.get_sdef(mid, mns, "referenced in doc_tools, make_id_doc, merge")
#                 mtype = msdef['type']
#                 mdf = msdef['df']
#                 mid_info = { 'ns': mns, 'df': mdf, 'type': mtype, 'qty': '!' }
#                 make_id_doc(f, mid, mid_info, ids_documented, msdef)
            if len(ml) == 1:
                ml = ml[0]
            if "core" in ml:
                print "found ml: %s" % ml
                import pdb; pdb.set_trace()
            html.append("<p><i>%s</i> includes all elements of <i>%s</i> with the "
                "the following additions or <u>changes</u>:</p>" % (cgi.escape(qid), ml))
    tbl = Table(f)
#    table_start = ("<table>\n<tr><th>id</th><th>type</th><th>description</th><th>required</th></tr>")
#    html.append(table_start)
    level = 0  # indicate top level members of group or dataset
    if type == 'group':
        add_group_doc(f, id, id_info, tbl, level, ids_documented)
    else:
        add_dataset_doc(f, id, id_info, tbl, level)
    # html.append("</table>")
    html.append(tbl.make_table())
#     if type == 'group' and merge:
#         html.append("Merge: %s" % ml)
    # Uncomment the following two lines to display the definition of each id
#     ppdf = pp.pformat(df)
#     html.append("<pre>\n%s\n</pre>" % cgi.escape(ppdf))
    # do not know table of contents level so don't specify
    # ids_documented[qid] = Id_doc(qid, html, namespaces=tbl.namespaces())
    # used id rather than qid so do not have namespaces in table of contents
    ids_documented[tcid] = Id_doc(tcid, html, namespaces=tbl.namespaces())
        
    
def record_sources(id_info):
    """ Save any source referenced so can determine if used later (when compiling list
    of undocumented_ids"""
    global ids_used
    if 'source' in id_info:
        sources = id_info['source']
        for source in sources:
            ids_used.add(source)
            
    
def add_dataset_doc(f, id, id_info, tbl, level):
    df = id_info['df']
    qty = id_info['qty']
    ns = id_info['ns']
    record_sources(id_info)
    qid = id if ns == f.default_ns else "%s:%s" % (ns, id)
    description = get_description(df)
    data_type = get_element(df, 'data_type', "*none_specified*")
    dimensions = get_element(df, 'dimensions', "")
    required = make_required_from_qty(qty)
    indent = ".&nbsp;" * level
    dim_str = " array; dims: %s" % dimensions if dimensions else ""
    type = data_type + dim_str 
#     te = "<tr><td>%s%s</td><td>%s</td><td>%s</td><td style=\"text-align:center\">%s</td></tr>" % (
#                 indent, cgi.escape(id), type, cgi.escape(description), required)
#     html.append(te)
    id_str = "%s%s" % (indent, cgi.escape(qid))
    override = 'source' in id_info and len(id_info['source']) > 1
    tbl.add(qid, id_str, type, description, required, ns, override)
    add_attributes(f, id_info, tbl, level+1)
    if dimensions:
        add_dimensions(f, df, tbl)

def add_dimensions(f, df, tbl):
    """Add any explicitly defined dimensions to Table object so can display after
    table is shown.  This is only for dimensions that have a definition, currently
    type "structure.
    """
    dimensions = get_element(df, 'dimensions', "")
    dim_names = []
    for dlist in dimensions:
        if isinstance(dlist, str):
            dim_names.append(dlist)
        elif isinstance(dlist, (list, tuple)):
            for dim in dlist:
                dim_names.append(dim)
        else:
            print "invalid type for dimensions: %s" % dimensions
    for dname in dim_names:
        if dname in df:
            # found dimension in definition
            dim_def = df[dname]
            tbl.add_dimension(dname, dim_def)

    
def add_group_doc(f, id, id_info, tbl, level, ids_documented, mode="stand_alone"):
    global includes_found
    # id = remove_trailing_slash(id)
    qty = id_info['qty']
    ns = id_info['ns']
    df = id_info['df']
    # import pdb; pdb.set_trace()
    # if available, get id_sources from node associated with this group
    # id_sources = node.id_sources if node else {}
    # include name, description of group
#     if "EventDetection" in id:
#         import pdb; pdb.set_trace()
    if level == 0 and mode == "stand_alone":
        description = "Top level group for %s." % remove_trailing_slash(cgi.escape(id))
        v_id = re.match( r'^<[^>]+>/?$', id) # True if variable_id (in < >)
        abstract = f.is_abstract(df)
        if v_id and not abstract:
            description = description + " Name should be descriptive."
        if abstract:
            description = description + (" This is an abstract group which can only be "
                "used by subclassing.")
        required = "yes"
    else:
        description = get_description(df)
        required = make_required_from_qty(qty)
    # get type
    link_spec = get_link_spec(df)
    if link_spec:
        # safe_tt = html_escape(remove_trailing_slash(link_spec['target_type']))
        # tt_link = "<a href=\"#%s\">%s</a>" % (safe_tt, safe_tt)
        tt_link = make_link(link_spec['target_type'])
        type = "link; target type=%s" % tt_link
        if link_spec['allow_subclasses']:
            type = type + " (or subtype)"
    elif 'merge' in df and level > 0:
        # type of this group is group being merged in
#         print "found merge in group, id=%s, df=" % id
#         pp.pprint(df)
#         import pdb; pdb.set_trace()
        mlist = df['merge']
        assert len(mlist) == 1, "For generated doc, merge in group can only be length 1, is: %s" % (
            mlist)
        mtarget = mlist[0]
        # remove namespace from link
        mtype = mtarget if ':' not in mtarget else mtarget.split(':')[1]
        # safe_tt = html_escape(remove_trailing_slash(mtype))
        # tt_link = "<a href=\"#%s\">%s</a>" % (safe_tt, safe_tt)
        tt_link = make_link(mtype)
        # if this was made by a "subclass merge" add text "(or subclass)"
        # attribute 'subclass_merge_base' is set in h5gate function "prune_subclass_merges"
        node = id_info['created'][0]
        subclass_txt = " (or subtype)" if hasattr(node, 'subclass_merge_base') else ''
        type = tt_link + subclass_txt + " (group)"
    else:
        type = 'group'
#     te = "<tr><td>%s%s</td><td>%s</td><td>%s</td><td style=\"text-align:center\">%s</td></tr>" % (
#         indent, cgi.escape(id), type, cgi.escape(description), required)
#     html.append(te)
    indent = ".&nbsp;" * level
    qid = id if ns == f.default_ns else "%s:%s" % (ns, id)
    override = 'source' in id_info and len(id_info['source']) > 1
    closed = "_closed" in df and df["_closed"]
    id_str = "%s%s" % (indent, cgi.escape(remove_trailing_slash(qid)))
    tbl.add(qid, id_str, type, description, required, ns, override, closed)
    add_attributes(f, id_info, tbl, level+1)
    if link_spec:
        # if this is a link there should not be any members to process
        return
    # process members of group
    level = level + 1
    indent = ".&nbsp;" * level
    includes = {}
    # used mstats created entry if available since that includes all merges
    have_mstats = 'created' in id_info and len(id_info['created']) > 0
    mdict = id_info['created'][0].mstats if have_mstats else df
    mdict = df
    # print "id=%s, have_mstats = %s" % (id, have_mstats)
#     if id == "/general/":
#         import pdb; pdb.set_trace()
    # for mkey in sorted(df.keys()):
    for mkey in sorted(mdict.keys()):
#         if mkey == "extracellular_ephys/":
#             import pdb; pdb.set_trace()
        # print "mkey=%s" % mkey
        if mkey == '_description' or (mkey == 'description' and isinstance(df[mkey], str)):
            # skip description, that's already displayed
            continue
        if mkey == "attributes":
            # skip attributes.  Those already displayed
            continue
        if mkey == "_required":
            process_required_clause(tbl, df[mkey])
            continue
        if mkey == "_exclude_in":
            process_exclude_in_clause(tbl, df[mkey])
            continue
        if mkey == "_closed":
            # was processed previously and added to table
            continue
        if mkey == "_properties":
            # properties not displayed.  They are used to flag that a group is "abstract"
            continue
        if mkey in ("_source_id", "_qty", "_source"):
            # these are used to keep track of sources of includes.  Not needed for display
            continue
        if mkey == "autogen":
            # used to specify autogen "create".  No need to display here
            continue
        if mkey == 'include':
            # this only occurs if not using mstats, i.e. just df.  That should
            # normally not happen since all id's except abstract classes should be
            # created and abstract classes should not have an include
            f.save_includes(ns, includes, df[mkey], id)
            continue
        if mkey == "merge":
            # both level==1 and level >1 merges already displayed.
            continue
        # mid, mqty = f.parse_qty(mkey, "!")
        mid = mkey
        # get id_info for this member (mid) from mstats entry for this mid
        # this assumes mstats entry always exists, which should be the case
        mid_info = id_info['created'][0].mstats[mid]
        if 'include_info' in mid_info:
            # this item was added by an include.  Don't create doc in this
            # table for it, but make a link
            includes[mid] = mid_info['include_info']
            continue
        mtype = 'group' if mid.endswith('/') else 'dataset'
        # mid_info = {'df': mdf, 'qty': mqty, 'ns':mns, 'type':mtype}
        if mtype == 'group':
            add_group_doc(f, mid, mid_info, tbl, level, ids_documented)
        else:
            add_dataset_doc(f, mid, mid_info, tbl, level)
    # add any includes:
    combined_includes = get_combined_includes(f, includes, ns, ids_documented)
    for mkey in sorted(combined_includes.keys()):
        inc_info = combined_includes[mkey]
        mns = inc_info['ns']
        mid = inc_info['id']
        mqty = inc_info['qty']
        mqid = "%s:%s" % (ns, mid) if ns != f.default_ns else mid
        if level == 1 and mode == "stand_alone":
            if (inc_info['source'] == 'implicit' or inc_info['id'][0] == '/' or
                not mkey.endswith('/')
                or id[0] == '/'):
                # don't save information about implicit includes or includes of
                # datasets or includes inside absolute path (e.g. "/processing" include "<Module>/".)
                # They are not used to make subclass hierarchy 
                continue            
            # is group that is not inside another group in schema
            # save includes for determining dependencies for ordering documentation
            if ':' in mqid:
                # print "adding %s to includes_found" % mqid
                # test replacing by mid
                mqid = mid
                # import pdb; pdb.set_trace()
            if id in includes_found:
                includes_found[id].append(mqid)
            else:
                includes_found[id] = [mqid,]
        msdef = f.get_sdef(mid, mns, "referenced in doc_tools, add_group_doc")
        mtype = msdef['type']
        mdf = msdef['df']
        mdescription = get_description(mdf, in_group=True, by_include=True)
        mrequired = make_required_from_qty(mqty)
        # safe_mqid = cgi.escape(remove_trailing_slash(mqid))
        # mlink = "<a href=\"#%s\">%s</a>" % (safe_mqid, safe_mqid)
        mlink = make_link(mqid)
#         te = "<tr><td>%s%s</td><td>%s</td><td>%s</td><td style=\"text-align:center\">%s</td></tr>" % (
#             indent, mlink, mtype, cgi.escape(mdescription), mrequired)
#         html.append(te)
        if inc_info['source']=='subclass':
            # this is the base class of an include with _option subclasses
            # replace type, id and description with info for subclass references
            abstract = f.is_abstract(mdf)
            # import pdb; pdb.set_trace()
            if len(inc_info['subclasses']) > 1:
                sub_links = ", ".join([inc_info['subclasses'][x] 
                    for x in sorted(inc_info['subclasses'].keys()) if x != mqid])
            else:
                sub_links = None
            if abstract:
                id_str = "%s%s subtype" % (indent, mlink)
                mdescription = "Any subtype of %s." % mlink
                if sub_links:
                    mdescription += " These include: %s" % sub_links
            else:
                id_str = "%s%s or subtype" % (indent, mlink)
                mdescription = "%s or any subtype." % mlink
                if sub_links:
                    mdescription += " Subtypes include: %s" % (sub_links)
        else:
            id_str = "%s%s" % (indent, mlink)
        tbl.add(mlink, id_str, mtype, mdescription, mrequired, mns)
        # make documentation for element if not already made
#         mid_info = { 'ns': mns, 'df': mdf, 'type': mtype, 'qty': mqty }
#         make_id_doc(f, mid, mid_info, ids_documented, msdef)
        make_iid_doc(f, mid, mns, ids_documented)

def make_iid_doc(f, id, ns, ids_documented):
    """ Generate documentation for included id's.  Usually, id's that have an
    unspecified (i.e. relative) location in the schema, not specified to be
    located at an absolute path.  Sometimes id's with absolute path's are
    also included "implicitly" because the path overlaps (used for extensions).
    This function always calls make_id_doc, which has parameter id_info.
    To get the "id_info" parameter (which contains all the information needed to
    create the id, this function tries to retrieve an mstats entry for a created
    id.  If that fails, the structure definition (sdef) is retrieved and used
    to create the id_info."""
    global created_ids
    id_info = None
    # first, try to get parent node created for id
    if id in created_ids:
        # node is an relative id that was included.  created_ids has parent node
        node = created_ids[id]
        id_info = node.mstats[id]
    else:
        if id[0] == '/':
            # id is an absolute, try to get parent node
            parent_path, name = f.get_name_from_full_path(id)
            node = f.get_node(parent_path, abort=False) 
            if node:
                # found parent node, use that to make id_info
                id_info = node.mstats[name]
    if id_info:
        make_id_doc(f, id, id_info, ids_documented)
    else:
        # parent node does not exist, use sdef df to make id_info
        sdef = f.get_sdef(id, ns, "referenced in doc_tools, make_relative_id_doc")
        type = sdef['type']
        df = sdef['df']
        qty = "?"  # display not required
        id_info = { 'ns': ns, 'df': df, 'type': type, 'qty': qty}
        make_id_doc(f, id, id_info, ids_documented, sdef)

def make_avid_doc(f, ids_documented):
    """Make documentation for "av ids".  The id in the schema is an absolute path
    with the last component set to a variable id."""
    global avid_nodes
    for grp in avid_nodes:
        full_path = grp.full_path
        path_prefix, name = f.get_name_from_full_path(full_path)
        mid = grp.sdef['id']
        v_id = re.match( r'^<[^>]+>/?$', mid) # True if variable_id (in < >)
        assert v_id, "%s is avid_node, but id (%s) is not variable" % (full_path, mid)
        id = f.make_full_path(path_prefix, mid)
        df = {}
        tsdef = {'id': mid, 'ns':f.default_ns, 'df':{}}
        to_merge = f.find_overlapping_structures(tsdef, full_path)
#         print "***\navid '%s', to_merge='%s'" % (id, to_merge)
        to_include = {}
        id_sources = {}
        descriptions = []
        f.process_merge(df, to_merge, to_include, id_sources, f.default_ns, id, descriptions)
#         print "after merge, df="
#         pp.pprint(df)
#         print "id_sources=%s" % id_sources
#         print "descriptions="
#         pp.pprint(descriptions)
        # build description
        if len(descriptions) == 1:
            # just one id merged (the normal situation).  Just use it's description
            description = descriptions[0][1]
        else:
            # multiple ids merged (from multiple extensions).  Combine descriptions
            # and prefix each by the namespace
            description = []
            for pair in descriptions:
                dqid, desc = pair
                dns, did = dqid.split(';')
                description.append("<b>%s</b>: %s" % (dns, desc))
                description = "\n".join(description)
        # Add description to definition
        df['_description'] = description
        # Add in 'merge' to definition
        df['merge'] = [mid]
        # now process this as a normal relative id
        # but replace the definition in mstats with the new one
        # TODO: Should figure out a better way of doing this (so don't change mstats)
        grp.parent.mstats[mid]['df'] = df
        id_info = grp.parent.mstats[mid]
        make_id_doc(f, id, id_info, ids_documented)
        
#       import pdb; pdb.set_trace()
#         type = 'group'
#         qty = "?"  # display not required
#         id_info = { 'ns': f.default_ns, 'df': df, 'type': type, 'qty': qty}
#         make_id_doc(f, id, id_info, ids_documented, sdef)

def get_combined_includes(f, includes, ns, ids_documented):
    """ Make new includes list that replaces all items with source type "subclass"
    with the subclass.  This done so the generated table will have a single reference
    to the subclass rather than explicitly listing all of the items of that subclass.
    """
    global created_ids
    combined_includes = {}
    for mkey in includes:
        iinfo = includes[mkey]
        if iinfo['source'] == 'subclass':
            # fist process included subclass to make link and also to make_id_doc 
            mns = iinfo['ns']
            mid = iinfo['id']
            mqty = iinfo['qty']
            mqid = "%s:%s" % (ns, mid) if ns != f.default_ns else mid
            # mqid = "%s:%s" % (mns, mid) if mns != f.default_ns else mid # possibly new
            # safe_mqid = html_escape(remove_trailing_slash(mqid))
            # mlink = "<a href=\"#%s\">%s</a>" % (safe_mqid, safe_mqid)
            mlink = make_link(mqid)
            # make documentation for element if not already made
            make_iid_doc(f, mid, mns, ids_documented)
            
#             msdef = f.get_sdef(mid, mns, "referenced in doc_tools, get_combined_includes")
#             mtype = msdef['type']
#             mdf = msdef['df']
#             mid_info = { 'ns': mns, 'df': mdf, 'type': mtype, 'qty': mqty }
#             make_id_doc(f, mid, mid_info, ids_documented, msdef)
            
            # now save information about subclass in combined_includes
            base = iinfo['base']
            if base in combined_includes:
                combined_includes[base]['subclasses'][mkey] = mlink
            else:
                combined_includes[base] = {'id': base, 'ns': ns,
                    'qty': iinfo['qty'], 'source': 'subclass', 'subclasses': {mkey: mlink}}
        else:
            # normal include, just copy info
            combined_includes[mkey] = includes[mkey]
    return combined_includes
        

def process_required_clause(tbl, required_clause):
    """Process 'required_clause', which is a list of [condition, message] lists.  e.g.:
    [ ["starting_time XOR timestamps",
        "Only one of starting_time and timestamps should be present"],
    ["(control AND control_description) OR (NOT control AND NOT control_description)",
        "If either control or control_description are present, then both must be present."]],
    Extract list of variables in message, add message to description of each variable.
    """
    for key in required_clause:
        if key == "_source":
            # ignore source
            continue
        condition, message = required_clause[key]
        # remove reserved words and parenthesis
        c_vars = re.sub(r'(?:\(|\)|XOR|AND|NOT|OR)','',condition)
        # remove extra spaces
        c_vars = re.sub(r' +',' ', c_vars)
        # split into list of variables
        c_vars = c_vars.split(" ")
        tbl.save_required_message(c_vars, message)
        

def process_exclude_in_clause(tbl, exclude_clause):
    """Process 'exclude_in' specification, which is a list of paths and variables
    excluded from those paths.  "exclude_in" spec has a form like:
    { '/stimulus/templates': ['starting_time!', 'timestamps!', 'num_samples?'] }
    Before saving it in tbl, convert to form that has variable as the index:
    { 'starting_time': [('/stimulus/templates', '!'), (...), ...],
      'timestamps':  [('/stimulus/templates', '!'), ... ],
      'num_samples': [('/stimulus/templates', '?'), ... ]}
    """
    exclude_ids = {}
    for path in exclude_clause:
        if path == "_source":
            # ignore source
            continue
        for id in exclude_clause[path]:
            qty = id[-1]
            if qty in ('?', '^', '!'):
                id = id[:-1]
            else:
                qty = '!'  # default is must not be present
            pq = (path, qty)
            if id not in exclude_ids:
                exclude_ids[id] = [pq,]
            else:
                exclude_ids[id].append(pq)
    tbl.save_exclude_ids(exclude_ids)

def get_link_spec(df):
    if 'link' not in df:
        return None
    link_df = df['link']
    target_type = get_element(link_df, 'target_type')
    allow_subclasses = get_element(link_df, 'allow_subclasses', False)
    link_spec = {'target_type': target_type, 'allow_subclasses': allow_subclasses}
    return link_spec
    

def add_attributes(f, id_info, tbl, level):
    """add any attributes for data set or group"""
    df = id_info['df']
    attrs = get_element(df, 'attributes', None)
    if not attrs:
        return
    mstats_attrs = (id_info['created'][0].attributes if 'created' in id_info
        and id_info['created'] else None)
    indent = ".&nbsp;" * level
    # import pdb; pdb.set_trace()
    for aid in sorted(attrs.keys()):
#         if aid == "orcid_id":
#             import pdb; pdb.set_trace()
        # adf = mstats_attrs[aid] if mstats_attrs else attrs[aid]
        adf = attrs[aid]
        madf = mstats_attrs[aid] if mstats_attrs else {}
        qty = f.retrieve_qty(adf, "!")
        if 'description' in adf:
            description = get_description(adf, in_group=True)
        else:
            description = None
        # source = adf['source'] if 'source' in adf else None
        source = madf['source'] if 'source' in madf else adf['source'] if 'source' in adf else None
        source_ns = source[-1].rpartition(':')[0] if source else f.default_ns
        aqid = "%s:%s" % (source_ns, aid) if source_ns != f.default_ns else aid
        data_type = get_element(adf, 'data_type', '*unknown*')
        dimensions = get_element(adf, 'dimensions')
        value = get_element(adf, 'value')
        const = get_element(adf, 'const')
        optional = get_element(adf, 'optional', False)
        required = make_required_from_qty(qty)
        desc = []
        if description:
            desc.append(description)
        elif value:
            if isinstance(value, str):
                vmsg = "Value is the string \"%s\"."
            elif isinstance(value, (int, float)):
                vmsg = "Value is the number \"%s\""
            else:
                vmsg = "Value is %s"
            vi = vmsg % cgi.escape(str(value))
            desc.append(vi)
            if const:
                desc.append("(const)")
        desc = " ".join(desc)
        dim_str = " array; dims: %s" % dimensions if dimensions else ""
        dt = data_type + dim_str
        id_str = "<i>%s%s (attr)</i>" % (indent, cgi.escape(aqid))
        override = source and len(source) > 1
        tbl.add(aid, id_str, dt, desc, required, source_ns, override)
        if dimensions:
            add_dimensions(f, adf, tbl)
#         te = "<tr><td>%s%s</td><td>%s</td><td>%s</td><td style=\"text-align:center\">%s</td></tr>" % (
#             indent, cgi.escape(aid) + " (attr)", dt, cgi.escape(desc), required)
#         html.append(te)
            

def get_description(df, in_group=True, by_include=False):    # more_info=False):
    """ Return part of description needed for current documentation.  in_group True
    if inside a group.  by_include is True if added to a group using an "include"
    (in the specification language).  Logic is:
       if in_group is true:
            if string "MORE_INFO:" is present:
                Return all text before More_info
            else:
                If "COMMENT:" present:
                    Return all text
                else:
                    if by_include:
                        Return only first sentence
                    else:
                        Return entire description
        else:
            if string "MORE_INFO:" is present:
                return text after "MORE_INFO:"
            else:
                return all text
    """
    # in_group = not more_info
    description = get_element(df, '_description', None)
    is_autogen = 'autogen' in df
    if not description:
        description = get_element(df, 'description', '*Not available*')
        if not isinstance(description, str):
            # if not a string, don't return it.  Is probably a dict for a dataset named description
            description = '*Not available*' 
    more_info_str = "MORE_INFO:"
    idx_more_info = description.find(more_info_str)
    comment_str = "COMMENT:"
    idx_comment = description.find(comment_str)
    autogen_msg = " <em>(Automatically created)</em>"
    if in_group:
        if idx_more_info != -1:
            description = description[0:idx_more_info]
            if is_autogen:
                description += autogen_msg
        else:
            if idx_comment == -1 and by_include:
                # only return first sentence for table
                sentence_list = splitParagraphIntoSentences(description)
                description = sentence_list[0]
            elif is_autogen:
                description += autogen_msg
    elif idx_more_info != -1:
        description = description[idx_more_info + len(more_info_str):]
    # add any css to description
    description = add_css_to_escaped_html(description)
    # description = add_css(description)
    return description

def add_css_to_escaped_html(str):
    """ Escape html entities then add any css tags"""
    return add_css(cgi.escape(str))

def add_css(str):
    """ Add css span tags to text by replacing strings of form:
      ":red:`some text`"  with  "<span class=\"red\">some text</span>"
    """
    css_str = re.sub(r':(\w+):`([^`]+)`', r'<span class="\1">\2</span>', str)
    return css_str
    
# def excape_html(str):
#     """Escape any html entities"""
#     return cgi.escape(str)


# from: http://stackoverflow.com/questions/8465335/a-regex-for-extracting-sentence-from-a-paragraph-in-python
def splitParagraphIntoSentences(paragraph):
    sentenceEnders = re.compile(r"""
        # Split sentences on whitespace between them.
        (?:               # Group for two positive lookbehinds.
          (?<=[.!?])      # Either an end of sentence punct,
        | (?<=[.!?]['"])  # or end of sentence punct and quote.
        )                 # End group of two positive lookbehinds.
        (?<!  Mr\.   )    # Don't end sentence on "Mr."
        (?<!  Mrs\.  )    # Don't end sentence on "Mrs."
        (?<!  Jr\.   )    # Don't end sentence on "Jr."
        (?<!  Dr\.   )    # Don't end sentence on "Dr."
        (?<!  Prof\. )    # Don't end sentence on "Prof."
        (?<!  Sr\.   )    # Don't end sentence on "Sr."
        (?<!  e\.g\.   )    # Don't end sentence on "e.g."
        (?<!  e\.g\.   )    # Don't end sentence on "i.e."
        \s+               # Split on whitespace between sentences.
        """, 
        re.IGNORECASE | re.VERBOSE)
    sentenceList = sentenceEnders.split(paragraph)
    return sentenceList

       

def generate_ids_old(f):
    """ Generate documentation from specification language file"""
    doc = []
    doc.append("generating documentation for: %s" % f.spec_files)
    id_lookups = f.id_lookups
    for ns in id_lookups:
        doc.append("***** Namespace %s" % ns)
        for id in sorted(id_lookups[ns].keys()):
            doc.append(id)
    doc = "\n".join(doc)
    return doc
    
 ########### OLD
 
#  def make_id_doc(f, id, id_info, ids_documented, sdef=None):
#     """ make documentation about id.  Add to ids_documented (dict mapping id
#     to documentation about id (a string).  sdef is structure definition if
#     obtained for id not created (not an absolute path without a variable-id).
#     ids that are created in mstats have a absolute path, definition for
#     them is in the mstats entry; sdef is not used.
#     In any case, sdef only used to find overlapping definitions for variable-id
#     items for merging extensions."""
# #     if "EventWaveform" in id:
# #         import pdb; pdb.set_trace()
#     global merges_found
#     global created_ids
#     # make qualified id (qualified by namespace if not default)
#     ns = id_info['ns']
#     qid = id if ns == f.default_ns else "%s:%s" % (ns, id)
#     qid = remove_trailing_slash(qid)
#     if qid in ids_documented:
#         # already have documented this id
#         return
#     # make entry to ids_documented so do not try to document this id again when processing members
#     ids_documented[qid] = "doc for %s being made" % qid
# #     safe_id = cgi.escape(id)
#     html = []
# #     anchor = "<a name=\"%s\"></a>" % safe_id
# #     html.append(anchor)
# #     header = "<h2>%s</h2>" % safe_id
# #     html.append(header)
#     type = id_info['type']
#     df = id_info['df']
#     qty = id_info['qty']
# #     print "make_id_doc, id=%s ns=%s qty=%s df=" % (id, ns, qty)
# #     pp.pprint(df)
#     if sdef and '<' in sdef['id']:
# #         print "found sdef, id=%s, sdef['id']=%s" % (id, sdef['id'])
#         # found variable id to merge
#         if sdef['id'][0] == '/':
#             # has absolute path, ignore for now
# #             print "%s: found absolute path, sdef[id]= %s" % (id, sdef['id'])
#             pass
#         else:
#             # does not have absolute path, try to find extensions to merge
#             # import pdb; pdb.set_trace()
#             to_merge = f.find_overlapping_structures(sdef, None)
#             if to_merge:
# #                 print "%s: found overlapping structures: %s" % (id, to_merge)
#                 df = dict(df)  # make copy so don't modify original
#                 to_include = []
#                 id_sources = {}
#                 f.process_merge(df, to_merge, to_include, id_sources, ns, qid)
#                 id_info = dict(id_info)  # copy so don't change original
#                 id_info['df'] = df
#                 if to_include:
#                     # not sure what to do with to_include right now
#                     print "Did merge of %s into %s, found to_include=%s" % (
#                         to_merge, qid, to_include)
#                     sys.exit(1)
#                 if id_sources:
#                     # add id_sources to id_info so can display source of extension id's
#                     assert 'id_sources' not in id_info, "id_sources already in id_info: %s" % id_info
#                     id_info['id_sources'] = id_sources
# #                    import pdb; pdb.set_trace()
# #                     print "Did merge of %s into %s, found ns_sources=%s" % (
# #                         to_merge, qid, ns_sources)
#     # description = cgi.escape(get_description(df, more_info=True))
#     description = get_description(df, in_group=False)
#     html.append("<p>%s</p>" % description)
#     if type == 'group':
#         merge = get_element(df, 'merge', None)
#         # include = get_element(df, 'include', None)
#         # required = get_element(df,'_required', None)
#         if merge:
#             ml = []
#             for mqid in merge:
#                 # save merges found for later ordering id's and making table of contents
#                 if id in merges_found:
#                     merges_found[id].append(mqid)
#                 else:
#                     merges_found[id] = [mqid, ]
#                 mlink = make_link(mqid)
# #                 safe_id = cgi.escape(remove_trailing_slash(mqid))
# #                 mlink = "<a href=\"#%s\">%s</a>" % (safe_id.strip("<>"), safe_id)
# #                 import pdb; pdb.set_trace()
#                 ml.append(mlink)
#                 # make sure documentation about this merged id is included
#                 mns, mid = f.parse_qid(mqid, ns)
#                 msdef = f.get_sdef(mid, mns, "referenced in doc_tools, make_id_doc, merge")
#                 mtype = msdef['type']
#                 mdf = msdef['df']
#                 mid_info = { 'ns': mns, 'df': mdf, 'type': mtype, 'qty': '!' }
#                 make_id_doc(f, mid, mid_info, ids_documented, msdef)
#             if len(ml) == 1:
#                 ml = ml[0]
#             html.append("<p><i>%s</i> includes all elements of <i>%s</i> plus "
#                 "the following:</p>" % (cgi.escape(qid), ml))
#     tbl = Table()
# #    table_start = ("<table>\n<tr><th>id</th><th>type</th><th>description</th><th>required</th></tr>")
# #    html.append(table_start)
#     level = 0  # indicate top level members of group or dataset
#     if type == 'group':
#         add_group_doc(f, id, id_info, tbl, level, ids_documented)
#     else:
#         add_dataset_doc(f, id, id_info, tbl, level)
#     # html.append("</table>")
#     html.append(tbl.make_table())
# #     if type == 'group' and merge:
# #         html.append("Merge: %s" % ml)
#     # Uncomment the following two lines to display the definition of each id
# #     ppdf = pp.pformat(df)
# #     html.append("<pre>\n%s\n</pre>" % cgi.escape(ppdf))
#     ids_documented[qid] = Id_doc(qid, html)     # do not know table of contents level
#  