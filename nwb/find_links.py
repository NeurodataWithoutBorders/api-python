 
# program to find hdf5 links

import re
import sys
import h5py
import copy
import numpy as np
import operator

import pprint
pp = pprint.PrettyPrinter(indent=4)
    
# def get_group_info(f, h5_node):
#     """ Return information about h5_node"""
#     paths = h5py.h5i.h5_node.name
#     gi = f.get(path, getlink=True)
# #     import pdb; pdb.set_trace()
# #     gi2 = h5py.h5g.get_objinfo(h5_group, follow_link=False)
#     gi = str(gi)
#     while True:
#         match = re.match(r'^<h5py\._hl\.group\.HardLink object at (0x[0-9a-f]+)>$', gi)
#         if match:
#             loc = match.group(1)
#             info = {'type':'hard', 'loc':loc}
#             break
#         match = re.match(r'^<SoftLink to "([^"]+)">$', gi)
#         if match:
#             loc = match.group(1)
#             info = {'type':'soft', 'loc':loc}
#             break;
#         print "Unable to determine link type: gi='%s'" % gi
#         sys.exit(1)
#     return info
    
    
def show_links(links):
    """ Display different structures in links"""
    print "********* Link groups **************"
    lg = links['lg']
    for type in lg:
        print "****** %s links:" % type
        num_locations = len(lg[type].keys())
        print "%i locations with %s link" % (num_locations, type)
        if num_locations == 0:
            continue
        multi_locs = {}
        # find locations with more than one:
        for loc in lg[type]:
            paths = lg[type][loc]
            if len(paths) > 1 or type == "soft": # soft links always have more than one since target is also
                multi_locs[loc] = paths
        if multi_locs:
            print "%i have multiple paths:" % len(multi_locs)
            pp.pprint(multi_locs)
        else:
            print "none have multiple paths"
    # soft links
    sl = links['sl_from_to']
    print "***** %i soft links.  (from -> to) below:" % len(sl)
    pp.pprint(sl)
    
def add_item(dict, key, val):
    """ Append value to list at dict[key].  (dict is a dictionary).  Created
    dict[key] first if it does not exist"""
    if key not in dict:
        dict[key] = []
    dict[key].append(val)
    

def save_info(objtype, objno, path, target, links):
    """ Save information in links structure"""
    if objtype in ('group', 'dataset'):
        links['count'][objtype] += 1
        type = 'hard'
        loc = str(objno)
        add_item(links['lg'][type], loc, path)
    elif objtype == "link":
        type = "soft"
        add_item(links['lg'][type], target, path)
        # save soft link from and to
        links['sl_from_to'][path] = target
    elif objtype == "type":
        # ignore hdf5 type type
        pass
    elif objtype == 'ext_link':
        type = 'ext'
        add_item(links['lg'][type], target, path)
    else:
        print "Unknown object type: '%s'" % objtype
        sys.exit(1)


h5_ntypes = {    # hdf5 node types, from: http://api.h5py.org/h5g.html
    h5py.h5g.LINK: 'link',
    h5py.h5g.GROUP: 'group',
    h5py.h5g.DATASET: 'dataset',
    h5py.h5g.TYPE: 'type',
    4: 'ext_link'  # a guess
}

def find_links(fp, links):
    """ Find links in hdf5 file.  fp is the pointer to a h5py file. links is structure to
    store results.  Builds links['lg'], ("lg stands for "location group), which maps
    each location to all the paths associated with that location.  Structure is:
    { 'type1' : {'loc_1': ['path1', 'path2', ...], 'loc_2': ['path3', 'path4', ...]
      'type2' : { ... }
    where type is type of link, "hard", "soft", "ext" (for external),
        loc is location, either hex address if hard, target path if soft,
        path are paths to nodes that have the same location.
    Also makes a dictionary in links, links['sl_from_to'] (sl stands for 'soft link').
    This stores the source and target for each soft link.  It is used
    in function merge_soft_links to merge soft link groups that point
    to the same target through a chain of soft links."""
    global h5_ntypes
    fid = fp.id
    root = h5py.h5g.open(fid, '/')
    np = (root, '/')  # np - node & path, h5 object and path
    # groups_to_visit = [ f["/"],]
    groups_to_visit = [ np,]
    while groups_to_visit:
        np = groups_to_visit.pop(0)
        h5g, path = np
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
            elif mtype == 'ext_link':
                # target of external link
                target = "\n".join(h5g.links.get_val(mname))
            else:
                target = None   
            if path == "/":
                full_path = "/" + mname
            else:
                full_path = path + "/" + mname
            save_info(mtype, objno, full_path, target, links)
            if mtype == 'group':
                mh5g = h5py.h5g.open(h5g, mname)
                mnp = (mh5g, full_path)
                groups_to_visit.append(mnp)
    
#   This was used in compute_autogen, but no longer needed since link_info can be used
# to determine if there is an external link.
# def get_h5_node_info(f, path):
#     """Get type, and if applicable, target for node at path path.
#     This requires finding the object with the name, then getting the type.  The h5py
#     low-level interface is used for this.  parent is the h5py.Group parent
#     """
#     global h5_ntypes
#     # get h5py low level object for parent group
#     parent_path, name = f.get_name_from_full_path(path)
#     parent_group = f.file_pointer[parent_path]
#     h5g = parent_group.id
#     for i in range(h5g.get_num_objs()):
#         mname = h5g.get_objname_by_idx(i)
#         if mname == name:
#             mtype = h5_ntypes[h5g.get_objtype_by_idx(i)]
#             # minfo = h5py.h5g.get_objinfo(h5g, mname)
#             if mtype == 'link':
#                 # target of symbolic link
#                 target = h5g.get_linkval(mname)
#             elif mtype == 'ext_link':
#                 # target of external link
#                 target = "\n".join(h5g.links.get_val(mname))
#             else:
#                 target = None
#             return (mtype, target)
#     print "%s: get_h5_node_info, did not find '%s'" % (parent.name, name)
#     sys.exit(1)
    
    
    

def merge_soft_links(links):
    """ Merge any soft link location groups that refer to the same location due
    to a chains of soft links."""
    sg = links['lg']['soft']
    to_remove = []
    # source_group1 -> target1
    # source_group2 -> target2
    # if target1 (through a chain of symbolic links) goes to target2
    # need to put source_group1 into source_group2
    # and remove source_group1 -> target1
    for target1 in sg.keys():
        target2 = target1
        count = 0
        limit = 100
        while target2 in links['sl_from_to']:
            target2 = links['sl_from_to'][target2]
            count = count+1
            if count > limit:
                sys.exit("Apparent loop in symbolic links (target='%s').  Aborting" % target2)
        if target1 != target2:
            # found new location (target2)
            source_group1 = sg[target1]
            source_group2 = sg[target2]
            source_group2.extend(source_group1)
            to_remove.append(target1)
    # remove groups that have been merged
    for t in to_remove:
        del sg[t]


def test_links():
    """ For testing merge soft links"""
    links = { 
        "lg": {
            "soft": {
                "e": ["a", "b", "c"],
                "b": ["d",],
                "d": ["f",]}
        },
        "sl_from_to": {
            "a": "e",
            "b": "e",
            "c": "e",
            "d": "b",
            "f": "d"}}
    return links;
                

def make_path2loc(lgrps):
    """ Set path2loc to map each path in lgrps (location groups) to
    the id of the location group associated with that path.  Input is:
    lgrps = { 'loc1': [ 'path1', 'path2', ...]; 'loc2': ['path3', ...], ...}
    Return is a dictionary of form:
    { 'path1': 'loc1', 'path2': 'loc1', 'path3': loc2', ... }"""
    path2loc = {}
    for loc in lgrps:
        for path in lgrps[loc]:
            path2loc[path] = loc
    return path2loc   
    

def prune_hard_links(links):
    """ Hard links that are made at a node above a leaf node in the tree
    create hard links for all nodes below to the leafs.  These hard links
    are not useful for deducing where links were made when reading a file.
    This function removes them to reduce the number of hard link locations
    stored (reducing memory required) and to make the read process
    more efficient."""
    hl = links['lg']['hard']
    # Step 0. Remove any hard link locations that have only one path
    # (These are not part of an added hard link)
    for loc in hl.keys():
        if len(hl[loc]) == 1:
            del hl[loc]
    # Step 1. Make path2loc which maps paths to the location identifier
    # This is just the reverse of the "location group" dictionaries mapping
    # locations to paths at the location
    path2loc = make_path2loc(hl)
    # Step 2. Get list of parent location(s) for each location as dictionary:
    # loc_parents = { 'loc1': [parent1, parent2, ..], 'loc2': [] ... }.  This is
    # done by stripping off suffix to path and finding any parent locations that
    # use the prefix.  All paths in the same location should have the same
    # suffix if they descend from the same parent group.  First check for that.
    loc_parents = {}
#     print "before pruning, hard link groups are:"
#     pp.pprint(shorten_dict(hl))
    for loc in hl:
        suffix = get_common_basename(hl[loc])
        if not suffix:
            # suffixes do not match, this group is not from the same parent group.  Don't save
            continue
        # suffixes match, now build list of parent group locations
        parent_paths = trim_common_basename(hl[loc], suffix)
        pl_list = []
        for parent_path in parent_paths:
            parent_loc = path2loc[parent_path] if parent_path in path2loc else None
            if parent_loc not in pl_list:
                pl_list.append(parent_loc)
        loc_parents[loc] = pl_list
#     print "parent locations ="
#     pp.pprint(loc_parents)
    # Step 3. Prune any location groups that have only one parent group.  These are
    # are the location groups that can be ignored.
    pruned={}
    for loc in loc_parents:
        if len(loc_parents[loc]) == 1:
            # this location has only one parent location, and all paths have the same suffix
            # prune this location group if it has not already been removed
            if loc in hl:
                pruned[loc] = hl[loc]
                del hl[loc]
#     print "pruned %i hard link location(s):" % len(pruned)
#     pp.pprint(shorten_dict(pruned))
#     print "After pruning, hard link groups are:"
#     pp.pprint(shorten_dict(hl))

def merge_soft_and_hard_links(links):
    """Merge any link groups that are from soft links and hard links which are actually
    part of the same group.  Example, if link group "h" contains a set of paths that refer
    to the same hdf5 node because they are all linked by hard links; and link-group "s" is
    a set of nodes that refer to the same target location via soft links; and if the target
    of 's' is a member of 'h', then these two groups are the same.  Treat the resulting group
    as a 'soft' link-group with the same target as the original soft link-group."""
    # get paths to locations for all paths in hard links link-groups
    hpath2loc = make_path2loc(links['lg']['hard'])
    # See if any targets of soft links are in a hard link link-group
    sl = links['lg']['soft']  # soft link-groups
    hl = links['lg']['hard']  # hard link-groups
    merged = []
    for target in sl:
        if target in hpath2loc:
            # found target in hard link link-group
            hloc = hpath2loc[target]
            # include members of hard link-group in soft link-group and delete hard link-group
            sl[target].extend(hl[hloc])
            del hl[hloc]
            merged.append(hloc)
    # print "hard-link groups merged with softlink goups:", merged

    
    
def make_path2lg(links):
    """ Creates path2lg (path to link group) information used by main h5gate when reading a file.
    This is stored in dictionary within 'links' using the following structure:
    'path2lg': { 'hard': <paths_to_hard_lgs>, 'soft': <paths_to_soft_lgs>, 'ext': <paths_to_ext_lgs> }
    where each <path_to_hard_lgs> is a dictionary mapping each path in a hard link-group to the
    location associated with the hard link-group it is in.  e.g. form is:
    {'path1': 'hard_lg1', 'path2': 'hard_lg1', 'path3': 'hard_lg28', ... }
    A similar structure is used for <path_to_soft_lgs> and ext (external) except that soft
    (or external) link-groups are referenced."""
    links['path2lg'] = {}
    for type in ('hard','soft','ext'):
        lg = links['lg'][type]  # link-group
        links['path2lg'][type] = make_path2loc(lg)    
        
#     hl = links['lg']['hard']   # hard link-groups
#     sl = links['lg']['soft']   # soft link-groups
#     el = links['lg']  
# 
#     links['path2lg']['hard'] = make_path2loc(hl)
#     links['path2lg']['soft'] = make_path2loc(sl)



def shorten_list(l, max_length=15):
    """ If list longer than max_length, returned shortened version"""
    length = len(l)
    if length > max_length:
        sl = l[0:max_length]
        sl.append("...%i total" % length)
    else:
        sl = l
    return sl

def shorten_dict(d, max_length=20):
    """ shorten dictionary to make easier to see"""
    sd = {}
    for key in d.keys()[0:max_length]:
        value = d[key]
        if isinstance(value, (list, tuple)):
            new_value = shorten_list(value)
        elif isinstance(value, dict):
            new_value = shorten_dict(value, max_length)
        else:
            new_value = value
        sd[key] = new_value
    if len(d) > max_length:
        sd["..."]="(%i total)" % len(d)
    return sd


def show_stats(links):
    """ Display length of various items"""
    hlg = len(links['lg']['hard'])
    slg = len(links['lg']['soft'])
    hp = len(links['path2lg']['hard'])
    sp = len(links['path2lg']['soft'])
    ft = len(links['sl_from_to'])
    print "Num groups: %i hard, %i soft" % (hlg, slg)
    print "path2lg: %i hard, %i soft" % (hp, sp)
    print "Soft link from-to: %i" % ft
    slinks = shorten_dict(links)
    print "links is:"
    pp.pprint(slinks)
    
   
def initialize():
    """ Initialized empty links structure.  See function "find" for description."""
    links = {
        'lg'      : {'hard': {}, 'soft': {}, 'ext': {}},
         'path2lg': {'hard': {}, 'soft': {}, 'ext': {}},
         'sl_from_to': {},
         'targets_created': {'hard': {}, 'soft': {}},
         'missing_links': {'hard': {}, 'soft': {}},
         'count': {'group': 0, 'dataset': 0}
         }
    return links  


def find(fp, links):
    """ Find all links in hdf5 file (both hard and soft).  Parameter fp is the
    pointer to a h5py File object.  links is a dictionary that will contain
    the link information.  It must have been setup by a call to initialize().
    Returns links dictionary with the following:
    { 'lg': { 'hard': <hard_link_groups>, 'soft': <soft_link_groups> },
      'path2lg' { 'hard': <paths_to_hard_lgs>, 'soft': <paths_to_soft_lgs>},
      'sl_from_to': { 'souce1': 'target1', 'source2': 'target2', ... },
      'targets_created': { 
          'hard': {'loc1': 'target1', 'loc2': 'target2', ...}
          'soft': {'loc3': 'target3', ... }}
      'missing_links': {
          'hard': {'loc1': ('from1', 'from2', ...), 'loc2': ('from3', 'from4', ...) }
          'soft': {'loc4': ('from6', 'from7', ...), 'loc5': ('from8', 'from9', ...) }
      'count': {'group': <number_groups>, 'dataset': <number_datasets> }
    }
    Where:
    'lg': contains the hard and soft "link groups".  Structure is:
        { 'type1' : {'loc_1': ['path1', 'path2', ...], 'loc_2': ['path3', 'path4', ...]
          'type2' : { ... }
        where type is type of link, "hard", "soft", "ext" (for external),
        loc is location, either a string consisting of two numbers in parentheses if
        a hard link, or a target path if a soft link.
        path are paths to nodes that have the same location.
    'sl_from_to': (sl stands for 'soft link') stores the source and target for each
        soft link.  This is used in function merge_soft_links to merge soft link
        groups that point to the same target through a chain of soft links.
    'path2lg': maps paths to the hard or soft link group corresponding to the path.
        <paths_to_hard_lgs> is a dictionary mapping each path in a hard link-group to the
        location associated with the hard link-group it is in.  e.g. form is:
        {'path1': 'hard_lg1_loc', 'path2': 'hard_lg1_loc', 'path3': 'hard_lg28_loc', ... }
        A similar structure is used for <path_to_soft_lgs> except that soft link-groups
        locations are referenced.
    'targets_created': provides h5gate node created which is the
        target for hard and soft link groups.  This is filled in when reading a
        file to record when the targets are made.
    'missing_links': lists of links that need to be created when reading a file.  Each
        loc is a location associated with a link group.  They are mapped to an array of
        paths of nodes that have links to that location, but the links are not created yet
        (i.e. are missing).  (The 'from' entries are paths.  The 'from' paths are added
        if a link is detected when reading a file but the target node has not been created
        yet.  The list is processed by function "fill_missing_links" 
        """
    find_links(fp, links)
    build_links_dicts(links)
    
#     merge_soft_links(links)
# #     print "Before pruning:"
# #     show_stats(links)    
#     prune_hard_links(links)
# #     print "After pruning:"
# #     show_stats(links)
#     merge_soft_and_hard_links(links)
#     make_path2lg(links)
    
    
def build_links_dicts(links):
    """ Constructs structures (dictionaries) described in function "find" in variable
    links using information about links that was stored using calls to function
    save_info.  This function is called in two situations: 1. When reading a file,
    before the nodes in the file are read to interpret them (i.e. figure out which
    nodes map to which structures in the specification), the file is first read to
    determine all the links.  This is done by function "find".  Function find then
    calls this function to build the link information structures that are needed
    to interpret nodes when reading.  2. When writing a file, each time
    a new link is made by a call to the api (make_group or set dataset) from code
    that is creating or modifying a file, the constructer for the Node class calls
    function "save_link_info" which calls function "save_info" if the information
    about that link has not yet been saved.  Then function h5gate.close, calls
    this function to build (or update) the link information structures which are
    needed to calculate values for the autogen specifications.
    """
    merge_soft_links(links)
    # print "Before pruning:"
    # show_stats(links)    
    prune_hard_links(links)
    # print "After pruning:"
    # show_stats(links)
    merge_soft_and_hard_links(links)
    make_path2lg(links)
    # return links

    
    
        
def deduce_link_info(f, full_path, type, sdef):
    """ ** This function only called when reading a file **
    Determine if hdf5 node is associated with a link (as either a source
    or destination) and if so save information needed to create the link.  (See
    routine "find" in file "find_links.py" for description of "f.links" structures
    used for this).  Return "link_info" structure if this node is a link (source).  Also
    saves information about link if it's a destination (and returns "None").
    Inputs: f - file object from h5gate, full_path - full path to node, type - type
    of node ('group' or 'dataset'), sdef - contains structure definition of node.
    Three cases:
    1. If node is not in a "link group" or is not the location of a soft link-group (i.e.
       the target) it is not part of a link (either source or 
       destination).  Save no information.  Return link_info = None.
    2. Node is the source of a link.  Two cases:
       2-a.  The target of the link (node in node_tree) has already been created. (i.e.
             is in "f.links.targets_created". Return link_info = { Node: <target_node> }
       2-b.  The target of the link has not been created.  Save path to node and loc of
             link-group in "f.links.missing_links" so can be filled in later after
             the target is created.  Return link_info = { Node: None } 
    3. Node is the destination of a link.  Save path to node and link-group location
    ---
    To determine if node is a source or destination of a link (needed for steps 2 & 3 above):
    (D1) If the node is in a soft-link group, the target path is already known.  (It's the
      location key for the soft_link group).  If the path to this node is the location
      for a soft link-group, then this node is the link destination; otherwise it is a link
      source.
    - If the node is in a hard-link group:  (note: group here does not refer to h5gate group or
        hdf5 group.  It referes to the list of nodes that share the same location, a link-group).
        -(D2) and if the target of the hard-link group has already been created; then this
          node should not match the path of that target (if it does something is wrong;
          system error). and thus this node will be a source.
        -(D3) if the target of the hard-link group has not already been created; then, given
          no other information, it's impossible to determine if this is the source or not.
          However, fortunately we do have additional information: the definition of the
          node in the specification.  If the definition of the node includes a "link"
          specification, then:
             -(D4) If the node is a group, and the link specification includes "must_be_link"
               set to True.  This this node must be a link source.  Otherwise, assume
               that this link is the target.
             -(D5) If the node is a dataset, and the link specification is included, and the
               "data_type" specification is not included, then this node must be a link
               source (i.e. a link).  Otherwise assume it is a target.
    """
    link_inf = get_link_inf(f, full_path)
    if not link_inf:
        # path is not in a hard or soft link-group, so is not part of a link (case 1 above)
        return None
    link_type = link_inf['link_type']
    if link_type == "ext":
        # external link
        file, path = link_inf['loc'].split('\n')
        link_info = {"extlink": (file, path)}
        return link_info
    loc = link_inf['loc']
    # Now determine if node is source or target. (Steps "D1" to "D5" above).
    if link_type == 'soft':
        is_source = link_inf['is_source']  # D1 above
    else:
           
#     link_type = 'hard' if full_path in f.links['path2lg']['hard'] else (
#         'soft' if (full_path in f.links['path2lg']['soft'] 
#                    or full_path in f.links['lg']['soft']) else None)
#     if link_type is None:
#         # node is not in a hard or soft link-group, so is not part of a link. (Case 1 above).
#         return None
#     # Now determine if node is source or target. (Steps "D1" to "D5" above).
#     if link_type == 'soft':
#         # soft link.  This is the target if it is the location for a soft link group (D1 above)
#         is_source = not full_path in f.links['lg']['soft']
#         loc = f.links['path2lg']['soft'][full_path] if is_source else full_path
#     else:
#         # link_type is hard
#         loc = f.links['path2lg']['hard'][full_path]  # location (key) of link-group
        if loc in f.links['targets_created']['hard']:
            # target exists (D2 above)
            target = f.links['targets_created']['hard'][loc]
            assert full_path != target, "Unexpected match between full_path and target: '%s'" %target
            is_source = True
        else:
            # target does not exist (D3 above).  Must look at definition to determine if source or target.
            link_spec = sdef['df']['link'] if 'link' in sdef['df'] else None
            # assume is source if there is a link spec
            is_source = True if link_spec is not None else False
#             if type == 'group':
#                 # node type is group (D4 above)
#                 is_source = (link_spec and 'must_be_link' in link_spec and link_spec['must_be_link'])
#             else:
#                 # node type is dataset (D5 above)
#                 is_source = link_spec and 'data_type' not in sdef['df']
    # now know if node is source or target of link.  Also have loc of link group. proceed to case 2 above.
    if is_source:
        if loc in f.links['targets_created'][link_type]:
            # target has been created (2-a above)
            target = f.links['targets_created'][link_type][loc]
            target_node = f.path2node[target]
            link_info = { 'node': target_node }
        else:
             # target has not been created (2-b above)
             # save this node in missing links
             add_item(f.links['missing_links'][link_type], loc, full_path)
             link_info = {'node': None}
        return link_info
    else:
        # node is destination of a link.  Save in targets_created (3 above)
        f.links['targets_created'][link_type][loc] = full_path
        # return None so this node will be created (not a link).
        return None
     
def get_link_inf(f, path):
    """Given a path to a node, returns information about
    the link, or None, if the path is not part of a link.  Returned link_inf has keys:
        link_type - type of link, either 'hard' or 'soft'
        loc  - location (key) of link group associated with link.  i.e. in links['lg'][link_type]
        is_source - For link_type "soft" returns True if is a link source (not the target
            of the link-group).  For link type 'hard' this is not returned.
    Note: This routine called 'get_link_inf' (not 'get_link_info") because the returned
    dictionary is different than what is stored in the node class, "link_info" dict.
    """
    link_type = (
        'hard' if path in f.links['path2lg']['hard']
               else 'soft' if path in f.links['path2lg']['soft'] 
                                       or path in f.links['lg']['soft']  # this in case path is the target
                            else 'ext' if path in f.links['path2lg']['ext'] else None)
    if link_type is None:
        # node is not in a hard, soft or ext link-group, so is not part of a link
        return None
    if link_type == 'soft':
        # soft link.  This is the target if it is the location for a soft link group
        is_source = not path in f.links['lg']['soft']
        loc = f.links['path2lg']['soft'][path] if is_source else path
        link_inf = {'link_type': link_type, 'loc': loc, 'is_source': is_source}
    else:
        # must be hard or external.  loc for hard is a tuple, for ext is file\npath
        loc = f.links['path2lg'][link_type][path]
        link_inf = {'link_type': link_type, 'loc': loc}
    return link_inf
        
    
def get_common_links(f, path):
    """Return list of links (paths) that share a link with path.  The list
    includes "path", but must also contain multiple paths. If there are no
    links that share it (or only one), return None.  The case of one link
    can occur is the link is an external link and there are no other
    external links to the same target."""
    link_inf = get_link_inf(f, path)
    if not link_inf:
        # path is not in a hard or soft link-group, so is not part of a link
        return None
    link_type = link_inf['link_type']
    loc = link_inf['loc']
    paths = f.links['lg'][link_type][loc]
    if link_type == "hard":
        links = paths
    else:
        # link type is 'soft', need to include target (link group location)
        # Note: don't use "append", because that will change the original list
        links = paths + [loc]
    # Remove any nodes that do not exist.  This required because hard links
    # may create some paths that are not actually in node tree.
    links = [x for x in links if x in f.path2node]
    if len(links) == 1:
        # there is only one link, don't return it since there must be more than one
        return None
    return sorted(links)
    
    
    
#     link_type = 'hard' if path in f.links['path2lg']['hard'] else (
#         'soft' if (path in f.links['path2lg']['soft'] 
#         or path in f.links['lg']['soft']) else None)
#     if link_type is None:
#         # node is not in a hard or soft link-group, so is not part of a link
#         return None
#     if link_type == 'soft':
#         # soft link.  This is the target if it is the location for a soft link group
#         is_source = not path in f.links['lg']['soft']
#         loc = f.links['path2lg']['soft'][path] if is_source else path
#     else:
#         loc = f.links['path2lg'][link_type][path]
#     links = copy.copy(f.links['lg'][link_type][loc])
#     if link_type == 'soft':
#         # need to include target (link group location) in with list of soft groups
#         links.append(loc)
#     return links


def get_nodes_from_path_template(starting_node, path_template):
    """ Given a "path template" return all nodes that have path matching
    the template, within the starting_node.   The path template is a relative path,
    which allows variable named nodes to be included in the path.  (Variable-named nodes
    are those that have the id enclosed in angle brackets, <> in the
    structures specification."""
    path_parts = path_template.strip('/').split('/')
    nodes = gnfpt(starting_node, path_parts)
    return nodes
    
def gnfpt(node, path_parts):
    """ Recursive function to get all nodes from template in path_parts
    This used for autogen"""
    if not path_parts:
        # no path parts, must be at leaf (end of recursion)
        return [node,]
    pp = path_parts[0]  # path part
    if pp == "<*>":
        # include all nodes
        found_nodes = []
        for id in node.mstats:
            for mnode in node.mstats[id]['created']:
                found_nodes = found_nodes + gnfpt(mnode, path_parts[1:])
    else:
        # not a wild card
        # need to check for both id without a slash (dataset) and idwith slash (group)
        ppg = pp + "/"  # groups have trailing slash
        id = pp if pp in node.mstats else (ppg if ppg in node.mstats else None)
        if not id:
            print ("Unable to find member id %s in autogen at: %s\n"
                " available members are: %s") % (pp, node.full_path, node.mstats.keys())
            # import pdb; pdb.set_trace()
            sys.exit(1)
        # found member in mstats.  Get nodes
        found_nodes = []
        for mnode in node.mstats[id]['created']:
            found_nodes = found_nodes + gnfpt(mnode, path_parts[1:])
    return found_nodes

def filter_autogen_targets(nodes, tsig):
    """ Return list of nodes that match the autogen target signature tsig."""
    if not tsig:
        return nodes
    matching_nodes = []
    for node in nodes:
        if node_matches_tsig(node, tsig):
            matching_nodes.append(node)
    return matching_nodes
    
def node_matches_tsig(node, tsig):
    """ Return true if node matches autogen signature 'tsig'.  tsig structure is:
    {type group or dataset  # if not present, either group or dataset match
      # list of attributes that must match
     """
    if 'type' in tsig:
        if node.sdef['type'] != tsig['type']:
            return False
    # types match (if tsig type specified).  Now check attributes
    na = node.attributes
    if 'attrs' in tsig:
        for aid in tsig['attrs']:
            if aid in na:
                value = na[aid]['nv'] if 'nv' in na[aid] else (
                    na[aid]['value'] if 'value' in na[aid] else None)
                if not value or not values_match(value, tsig['attrs'][aid]):
                    return False
    # everything matches
    return True




def fill_missing_links(f):
    """ Fill in any links that were missing targets at time link source was read in"""
    missing_targets = {'hard': [], 'soft': []}
    for link_type in ('hard', 'soft'):
        for loc in f.links['missing_links'][link_type]:
            from_paths = f.links['missing_links'][link_type][loc]
            if loc not in f.links['targets_created'][link_type]:
                missing_targets[link_type].append(loc)
            else:
                target_path = f.links['targets_created'][link_type][loc]
                target_node = f.path2node[target_path]
                for from_path in from_paths:
                    from_node = f.path2node[from_path]
                    assert from_node.link_info['node'] is None, "Link already set in %s" %target_path
                    from_node.link_info['node'] = target_node
                    validate_link(f, from_node, target_node)
                    # save information about link in links structure for later use in autogen
                    # save_info(objtype, objno, path, target, links):
                    ### Actually, don't save link info.  It's already saved when reading
                    # save_info("link", None, from_node.full_path, target_node.full_path, f.links)
    if missing_targets['hard'] or missing_targets['soft']:
        print "*** Link targets were missing when reading file:"
        for link_type in ('hard', 'soft'):
            for loc in missing_targets[link_type]:
                from_paths = f.links['missing_links'][link_type][loc]
                print "loc '%s', from paths:" % loc
                pp.pprint(from_paths)
        sys.exit(1)

def validate_link(f, source, target):
    """ Check that a link being made from node "source" to node "target"
    is valid (i.e. is consistent with the specification definition of
    both source and target"""
    error = f.error
    warning = f.warning
    link_spec = source.sdef['df']['link'] if 'link' in source.sdef['df'] else None
    target_type = f.make_qid(target.sdef['id'], target.sdef['ns'])  # add namespace for match
    if link_spec:
        expected_target_type = link_spec['target_type'] if 'target_type' in link_spec else None
        if expected_target_type:
            # add in namespace to expected target_type
            expected_target_type = f.make_qid(expected_target_type, source.sdef['ns'])
            if expected_target_type == target_type:
                # perfect match
                pass
            elif (source.sdef['type'] == 'group' and 'allow_subclasses' in link_spec and
                link_spec['allow_subclasses']):
                # see if match to a subclass
                subclasses = target.merged if hasattr(target, 'merged') else []
                if expected_target_type not in subclasses:
                    error.append("%s - link target_type (%s) does not match target type (%s) or subclasses (%s) at: %s" %
                        (source.full_path, expected_target_type, target_type, subclasses, target.full_path))
                else:
                    # is OK, matches subclass
                    pass
            else:
                inc_path = source.get_include_path()
                error.append("%s - link target_type (%s)%s does not match target type (%s) at: %s" %
                    (source.full_path, expected_target_type, inc_path, target_type, target.full_path))
        else:
            warning.append("%s - target type of link not specified.  Linking to type '%s' at: %s" %
                (source.full_path, target_type, target.full_path))
    else:
        # no link spec see if type of items match
        source_type = f.make_qid(source.sdef['id'], source.sdef['ns'])
        if source_type != target_type:
            warning.append("%s - type (%s) is linked to a different type (%s) at: %s" %
                (source.full_path, source_type, target_type, target.full_path))
            # import pdb; pdb.set_trace()
        else:
            # perfect match
            pass

# def initialize_autogen():
#     """ Setup structure for storing autogen information.  Looks like:
#     { 'found': [ a1, a2, ... ],
#       'ds2mk': [ d1, d2, ... ] }
#     each "a" is a dictionary containing information about an autogen
#     found in an *existing* (i.e. already created) node.  Each d1 is
#     information about an autogen in a dataset that may not exist.  Such
#     datasets will be created automatically before processing the autogen
#     directives they contain."""
#     ag = { 'found': [], 'ds2mk': [] }
#     return ag
    

def check_for_autogen(dict, aid, path, ctype, f):
    """ Check for autogen specification in either an attribute or dataset
    properties list.  If in an attribute, aid is the attribute id, otherwise
    None.  "path" is the path to the hg5gate object which contains dict.
    ctype is the type of object, either "group" or "dataset".
    If autogen is found and is syntactically correct, save it.  Returns True if
    autogen is found (whether valid or not).  Otherwise returns False.
    f  - h5gate file object.  Needed to allow accessing f.autogen array.
    This routine just saves the information so it can later be processed by:
    routines: compute_autogen, validate_autogen, update_autogen.
    """
#     print "check for autogen, aid=%s" % aid
#     if aid == "missing_fields":
#         import pdb; pdb.set_trace()
    if 'autogen' not in dict:
        return False
    agspec = dict['autogen']
    type = get_param(agspec, 'type', None)
    target = get_param(agspec, 'target', None)
    trim = get_param(agspec, 'trim', False)
    sort = get_param(agspec, 'sort', True)
    qty = get_param(agspec, 'qty', "*")
    tsig = get_param(agspec, 'tsig', {})
    include_empty = get_param(agspec, 'include_empty', False)
    format = get_param(agspec, 'format', "$t")
    # dimensions used to determine if result is an array or a single string
    # if dimensions present, then array, otherwise a single string
    dimensions = dict['dimensions'] if 'dimensions' in dict else None
    # exclude = get_param(agspec, 'exclude', None)
    error = []
    ag_types = ('links', 'link_path', "names", "values", "length", "create", "missing", "extern")
    if type not in ag_types:
        error.append("Invalid autogen specification. (%s). Type must be one of: %s" % (agspec, ag_types)) 
    if target is None and type not in ('create', 'missing', "extern"):
        error.append("Invalid 'autogen' specification.  'target' must be specified: %s" % agspec)
    if trim not in (True, False):
        error.apped("Invalid 'autogen' specification.  'trim' must be True or False: %s" % agspec)
    if sort not in (True, False):
        error.apped("Invalid 'autogen' specification.  'sort' must be True or False: %s" % agspec)
    if qty not in ("!", "*"):
        error.apped("Invalid 'autogen' specification.  'qty' must be '!' or '*': %s" % agspec)
    if error:
        f.error.append(error)
    else:
        a = {'node_path':path, 'aid': aid, 'agtarget':target, 'agtype':type, 'format':format,
        'trim':trim, 'sort':sort, 'qty':qty, 'tsig':tsig, 'include_empty':include_empty,
        'ctype':ctype, 'dimensions': dimensions}
        f.autogen.append(a)
    return True
    

# def save_autogen(f, node, aid, agtype, agtarget, trim, qty, tsig):
# # (f, node, aid, agtarget, agtype, params):
#     """ Save information about an "autogen" specification.  Parameters are:
# 
#     """
#     a = {'node':node, 'aid': aid, 'agtarget':agtarget, 'agtype':agtype,
#         'trim': trim, 'qty': qty, 'tsig': tsig}
#     f.autogen.append(a)
    
def show_autogen(f):
    """ Displays stored autogen, for testing"""
    print "found autogens:"
    for a in f.autogen:
        attr = "attribute (%s)" % a['aid']
        print a['ctype'], a['agtype'], a['node_path'], attr,  a['agtarget'], a['aid']
  

# def create_autogen_datasets(f):
#     """ Create any data sets that were found in the mstats of a group, and have the
#     autogen specification, but which were not created yet.  This is so the autogen
#     in these datasets can be processed by 'check_for_autogen' (to extract and save
#     the autogen information).  The information is then used by comompute_autogen
#     to fill in the values for the dataset."""
#     import pdb; pdb.set_trace()
#     for ds2mk in f.autogen['ds2mk']:
#         grp, id = ds2mk
#         if grp.mstats[id]['created']:
#             # dataset already created.  Autogen would have been found already
#             continue
#         # pretend to be a client program creating the data set
#         # that will save the autogen information as though a client program made it.
#         # print "*** The magic starts, creating %s: %s" %(grp.full_path, id)
#         grp.set_dataset(id, "autogen")

def process_autogen(f):
    """ Main routine for computing and updating autogens.  This called by h5gate after
    the close() call is made to update / create  autogen fields before validation.
    The autogen type "missing" checks for missing fields.  All of them must be
    executed after all the other augogens, so the missing autogen won't detect
    something as missing which is actually made by a subsequent autogen.
    All autogens are processed in two steps: 1. compute - which computes the values
    and 2. - update which updates them in the hdf5 file if writing or updating
    the file (not read-only mode).
    """
    # this processes all autogens that are not type missing (first loop),
    # then all that are (second loop) 
    for op in (operator.ne, operator.eq):
        compute_autogens(f, op, "missing")
        if f.options['mode'] in ['w', 'r+']:
            # only update hdf5 file if in write mode
            update_autogens (f, op, "missing")

def compute_autogens(f, op, ftype):
    """ Compute all autogens that have type (equal or not equeal) to ftype.
    op is an operator, either ne or eq"""
    # use index to go though so new ones can be added within the loop
    i = 0
    while i < len(f.autogen):
        a = f.autogen[i]
        i = i + 1
        if op(a['agtype'], ftype):
            compute_autogen(f, a)  # singular, not plural

    
def update_autogens(f, op, ftype):
    """ Update all autogens that have type (equal or not equeal) to ftype.
    op is an operator, either ne or eq"""
    # use index to go though so new ones can be added within the loop
    i = 0
    while i < len(f.autogen):
        a = f.autogen[i]
        i = i + 1
        if op(a['agtype'], ftype):
            update_autogen(f, a)   # singular, not plural

    

# def compute_autogen(f):
#     """ Computes values for each autogen saved in f.autogen.  f is the hfgate File
#     object.  Stores the computed values in array autogen[a]['agvalue']."""
#     # first, create any datasets that have autogen, but were not created
# #    create_autogen_datasets(f)
#     # now process all found autogens
#     # first put all type "missing" at the end so these are
#     # run after all the others.  Otherwise, they may flag as missing values filled in
#     # by other autogen's
#     ag_all = []
#     ag_last = []
#     for ag in f.autogen:
#         if ag['agtype'] == 'missing':
#             ag_last.append(ag)
#         else:
#             ag_all.append(ag)
#     # store back in f.autogen because more may be added when running the autogens
#     f.autogen = ag_all + ag_last
#     # use index to go though so new ones can be added within the loop
#     # for a in f.autogen:  # old method
#     show_autogen(f)
#     print "starting to compute autogen, num augogens = %i" % len(f.autogen)
#     import pdb; pdb.set_trace()
#     i = 0
#     while i < len(f.autogen):
#         a = f.autogen[i]
#         compute_autogen_1(f, a)
#         i = i + 1     


def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]
    
def get_constant_suffix(path):
    # return last component of path if is a constant (not enclosed in <>)
    # and if there is a variable part of path earlier.  Otherwise return None
    match = re.match(r'[^>]+>(/[^<>]+)$', path)
    if match:
        suffix = match.group(1)
    else:
        suffix = None
    return suffix
    
def remove_suffix(text, suffix):
    # remove suffix from text if present
    if suffix and text.endswith(suffix):
        text = text[0:-len(suffix)]
    return text

def check_if_all_str(vals):
    """return true if all elements of list are string"""
    if len(vals) == 0:
        return False
    for val in vals:
        if not (isinstance(val, str) and re.match(r'^[0-9]+$', val)):
            return False
    return True
    
def natural_sort(vals):
    """return sorted numerically if all integers, otherwise, sorted alphabetically"""
    all_str = all(isinstance(x, (str, unicode)) for x in vals)
    sv = sorted(vals, key=sortkey_natural) if all_str else sorted(vals)
    return sv
    
    
# function used for natural sort ke
# from: http://stackoverflow.com/questions/2545532/python-analog-of-natsort-function-sort-a-list-using-a-natural-order-algorithm
def sortkey_natural(s):
    return tuple(int(part) if re.match(r'[0-9]+$', part) else part
                for part in re.split(r'([0-9]+)', s))  
    
def get_parent_path(full_path):
    """ Return parent path for full_path"""
    parent_path, node_name = full_path.rstrip('/').rsplit('/',1)  # rstrip in case is group (ending with '/')
    if parent_path == "":
        parent_path = "/"
    return parent_path

def compute_autogen(f, a):
    """ computes values for one autogen.  Stores in updated autogen entry "a"."""
    # compute agtarget path
    # figure out enclosing path
    # if attribute of a group, then enclosing path is just the node_path, otherwise the parent
    if a['aid'] and a['ctype'] == 'group':
        enclosing_path = a['node_path']
    else:
        enclosing_path = get_parent_path(a['node_path'])
    assert enclosing_path in f.path2node, "Enclosing group for autogen does not exist: %s" % enclosing_path
    enclosing_node = f.path2node[enclosing_path]
    # store value in case there is an error, plus to ignore type "create" in ag_validate , ag_update
    a['agvalue'] = None
    if a['agtype'] == "create":
        # type create is special, compute it separately
        process_ag_create(f, a, enclosing_node)
        return
    if a['agtype'] == "missing":
        # type missing is also special, compute it separately
        process_ag_missing(f, a, enclosing_node)
        return
    if a['agtype'] == "extern":
        # type extern is also special, compute it separately
        process_ag_extern(f, a, enclosing_node)
        return
    agtarget_nodes = get_nodes_from_path_template(enclosing_node, a['agtarget'])
    agtarget_nodes = filter_autogen_targets(agtarget_nodes, a['tsig'])
    if not agtarget_nodes:
        if a['qty'] == "!":
            msg = ("Unable to find target for required autogen, enclosing group='%s', type='%s'\n"
                "node_path='%s', attribute [%s], target='%s'") % ( enclosing_path,
                enclosing_node.sdef['id'], a['node_path'], a['aid'], a['agtarget'])
            f.error.append(msg)
        elif a['include_empty']:
            # return empty list
            # return numpy type so h5py will create empty list of strings
            # rather than empty float array, if option 'include_empty' is True
            a['agvalue'] = np.empty([0,], dtype=np.string_)
            # a['agvalue'] = []
        else:
            # since it's not required (qty != '!') and not including empty, just ignore
            # for nwb format, ignoring removes warming messages for unable to find data or timestamps
            # target when making data_links or timestamps_links.
            pass
            # msg = ("Unable to find autogen target, enclosing group='%s', type='%s'\n"
            #     "node_path='%s', attribute [%s], target='%s'") % ( enclosing_path,
            #    enclosing_node.sdef['id'], a['node_path'], a['aid'], a['agtarget'])
            # f.warning.append(msg)
        return
    if a['qty'] == '!' and len(agtarget_nodes) > 1:
        f.error.append(("%s: one and only one (!) specified, but more than one autogen"
            " target found for path: %s") % (a['node_path'], a['agtarget']))
        return
    # at least one target node found
    if a['agtype'] == 'links' and len(agtarget_nodes) > 1:
        f.error.append("%s: multiple target nodes for autogen 'links' not supported, %i matches found"
            % (a['node_path'], len(agtarget_nodes)))
        return
    # now, process each of the different autogen types
    if a['agtype'] == 'links':
        # Get all links sharing agtarget
        agtarget_path = agtarget_nodes[0].full_path
        a['agvalue'] = get_common_links(f, agtarget_path)
        if a['agvalue'] and a['trim']:
            basename = get_common_basename(a['agvalue'])
            if basename:
                a['agvalue'] = trim_common_basename(a['agvalue'], basename)
#         if a['exclude'] and a['agvalue']:
#             # import pdb; pdb.set_trace()
#             # remove nodes with path starting with string in 'exclude'
#             a['agvalue'] = [x for x in a['agvalue'] if not x.startswith(a['exclude'])]
            a['agvalue'] = sorted(a['agvalue'])
    elif a['agtype'] == 'link_path':
        lpaths = {}
        # make prefix in case using trim
        # can use encode to remove unicode prefix, but maybe it's better to leave it in
        # prefix =  enclosing_node.full_path.encode('ascii', 'ignore') + '/'
        prefix =  enclosing_node.full_path + '/'
        # get suffix if constant for trimming right side of source path
        suffix = get_constant_suffix(a['agtarget'])
        for node in agtarget_nodes:
            # if not hasattr(node, 'link_info'):
            if not node.link_info or node.link_info['node'] is None:
                f.error.append("%s: referenced in 'link_path' autogen, but is not a link" % node.full_path)
                return
            else:
                fpath = node.full_path  # .encode('ascii', 'ignore')
                tpath = node.link_info['node'].full_path  # .encode('ascii', 'ignore')
                if a['trim']:
                    # trim prefix and any suffix on fpath
                    fpath = remove_prefix(fpath, prefix)
                    fpath = remove_suffix(fpath, suffix)
                lpaths[fpath] = tpath
        if False and a['qty'] == "!":  # skip this, try using just formatting
            agv = lpaths[lpaths.keys()[0]]
        else:
            agv = []
            for fpath in sorted(lpaths.keys()):
                tpath = lpaths[fpath]
                strt = a['format']
                strt = strt.replace("$s", fpath)
                strt = strt.replace("$t", tpath)
                agv.append(str(strt))  #  "\"'%s' is '%s'\"" % (fpath, tpath))
            if a['dimensions'] is None:
                # no dimensions specified, save as a single string
                # TODO, add in a "join_str" option rather than assume newline
                agv = "\n".join(agv)
        a['agvalue'] = agv
    elif a['agtype'] == 'names':
        # Get all names matching agtarget
        names = []
        for node in agtarget_nodes:
            name = node.name
            # encoding unicode now done in h5gate create_dataset
            # if isinstance(name, unicode):
            #      name = name.encode('utf8')
            names.append(name)
        names =  natural_sort(names)
        a['agvalue'] = names
    elif a['agtype'] == 'values':
        # Get set of values that are in names matching agtarget
        values = set()
        for node in agtarget_nodes:
            path = node.full_path
            nv = f.file_pointer[path].value
            if not isinstance(nv, (list, tuple, np.ndarray)):
                f.error.append("%s: autogen values must be list.  Found type: "
                    "%s at target:\n%s\nvalue found:%s" % (a['node_path'], type(nv), 
                    path, nv))
                return
            snv = set(nv)
            values = values.union(snv)
        lvalues = list(values)
        lvalues = natural_sort(lvalues)
        a['agvalue'] = lvalues
    elif a['agtype'] == 'length':
        # get length of target
        path = agtarget_nodes[0].full_path
        try:
            val = f.file_pointer[path].value
        except KeyError:
            # unable to get value.  See if this is an external link
            # if hasattr(agtarget_nodes[0], 'link_info') and 'extlink' in agtarget_nodes[0].link_info:
            if agtarget_nodes[0].link_info and 'extlink' in agtarget_nodes[0].link_info:
#             ntype, target = get_h5_node_info(f, path)
#             if ntype == "ext_link":
                tfile, tpath = agtarget_nodes[0].link_info['extlink']
                msg = ("%s: autogen unable to determine length of '%s' because hdf5 external "
                    "link missing: file='%s', path='%s'") % (
                    a['node_path'], path, tfile, tpath)
                f.warning.append(msg)
                # set length to 0 to indicate do not have valid value
                # length = 0
                # leave value undetermined.  Require user set it.
                return
            else:
                print "Unexpected node type in autogen length, type=%s, target=%s" % (ntype, target)
                # import pdb; pdb.set_trace()
                sys.exit(1)
        else:
            try:
                length = len(val)
            except TypeError, e:
                msg = "%s: autogen unable to determine length of '%s' error is: '%s'" % (
                    a['node_path'], path, e)
                f.warning.append(msg)
                # leave value unspecified
                return
        a['agvalue'] = length
    else:
        sys.exit("invalid autogen specification type: %s" % a['agtype'])
    # if the computed value is an empty list, replace it by numpy type so h5py will create
    # empty list of strings rather than empty float array, if option 'include_empty' is True
    if isinstance(a['agvalue'], list) and len(a['agvalue']) == 0:
        a['agvalue'] = np.empty([0,], dtype=np.string_)

def process_ag_create(f, a, enclosing_node):
    """ process autogen "create" type.  This creates group members
    that are specified to be created which are required and do not exist.
    Everything for the autogen create type is performed in this routine.
    There is nothing to do for the autogen validate or update for the
    create type.
    """
    # only process (create required groups) if write mode
    if not f.options['mode'] in ['w', 'r+']:
        return
    mid = remove_prefix(a['node_path'], enclosing_node.full_path).lstrip('/')
    mstats = enclosing_node.mstats
    assert mid in mstats, "%s: autogen create unable to find member id (%s) in mstats" % (
        enclosing_node.full_path, mid)
    minfo = mstats[mid]
    if minfo['created'] or minfo['qty'] not in ("!", "+"):
        # member was already created or is not required
        return
    type = minfo['type']
    assert type == 'group', "%s: autogen create referencing dataset (%s).  This is not allowed." %(
                enclosing_node.full_path, mid)
    gid = mid.rstrip('/')
    # create the group
    enclosing_node.make_group(gid)


def process_ag_missing(f, a, enclosing_node):
    """ process autogen "missing" type.  This returns a list datasets
    that are specified as required and do not exist.
    """
    missing = []
    for mid in enclosing_node.mstats:
        minfo = enclosing_node.mstats[mid]
        if minfo['qty'] in ('!', '^', '+') and not minfo['created']:
            # member was required but does not exists
            missing.append(mid)
    if missing:
        a['agvalue'] = sorted(missing)

def process_ag_extern(f, a, enclosing_node):
    """ Process autogen "extern" type.  This returns a list of
    groups or datasets that are set to hdf5 external links"""
    extern = []
    for mid in enclosing_node.mstats:
        minfo = enclosing_node.mstats[mid]
        if minfo['created']:
            for node in minfo['created']:
                if node.link_info and 'extlink' in node.link_info:
#                     if 'image_stack' == node.sdef['id'].rstrip('/'):
#                         import pdb; pdb.set_trace()
                    extern.append(node.sdef['id'].rstrip('/'))
    if extern:
        a['agvalue'] = sorted(extern)
    

def get_common_basename(paths):
    """ Return common "basename" (or "suffix"; is the last component of path)
    in list "paths".  Or return None if all elements in paths do not share a common last
    component.  Generate an error if any path ends with a slash."""
    if len(paths) == 0:
        return None
    # get suffix  of first element:
    first_path = paths[0]
    first_suffix  = first_path.rsplit('/', 1)[-1]
    assert first_suffix !='', "Invalid path, has trailing slash: %s" % first_path
    match = True
    for path in paths:
        prefix, suffix  = path.rsplit('/', 1)
        assert suffix !='', "Invalid path, has trailing slash: %s" % path        
        if suffix != first_suffix:
            match = False
            break
    if not match:
        # suffixes do not match
        return None
    # suffixes match
    return first_suffix
    
def trim_common_basename(paths, basename):
    """ Trim the common last component (given by "basename") from each path in
    list "paths".  Return new list."""
    new_list = []
    for path in paths:
        prefix, suffix = path.rsplit('/',1)
        assert suffix == basename, "Path '%s' does not have common suffix '%s'" % (path, basename)
        new_list.append(prefix)
    return new_list
    
def values_match(x, y):
    """ Compare x and y.  This needed because the types are unpredictable and sometimes
    a ValueError is thrown when trying to compare.
    """
    if x is y:
        return True
    # explicit checks for None used to prevent warnings like:
    # FutureWarning: comparison to `None` will result in an elementwise object comparison in the future.
    # eq = x==y

    if x is None:
        if y is None:
            return True
        else:
            return False
    if y is None:
        return False
    try:
        eq = x==y
    except ValueError:
        # ValueError: shape mismatch: objects cannot be broadcast to a single shape
        return False
    if isinstance(eq, bool):
        return eq
    return eq.all()
  
#     if x is y:
#         return True
#         return x==y
#     if (isinstance(x, (list, tuple, np.ndarray))
#         and isinstance(y, (list, tuple, np.ndarray))):
#         eq = x==y
#         if isinstance(eq, bool):
#             return eq
#         return eq.all()
#     if isinstance(x, basestring) and isinstance(y, basestring):
#         return x == y
#     # don't have same shape or type
#     return False
    

# def validate_autogen_old(f):
#     """ Validates that autogen fields have correct values.  i.e. match what was
#     generated by "ag_compute".  f is the h5gate file object"""
#     for a in f.autogen:
#         if a['agvalue'] is None:
#             # skip those that have no value
#             continue
#         if a['aid']:
#             # value is stored in attribute
#             aid = a['aid']
#             node = f.path2node[a['node_path']]
#             ats = node.attributes[aid]
#             value = ats['nv'] if 'nv' in ats else (
#                 ats['value'] if 'value' in ats else None)
#             if not values_match(value, a['agvalue']):
#                 f.error.append(("'%s' autogen attribute [%s] values incorrect.\n"
#                     "expected:%s (type %s)\nfound:%s (type %s)") % (a['node_path'], aid, 
#                     a['agvalue'], type(a['agvalue']), value, type(value)))
#             elif value is None and a['qty'] == '!':
#                 f.error.append(("%s autogen attribute [%s] value required "
#                     "but is empty") % (a['node_path'], aid))
#         else:
#             # value is stored in value of a dataset
#             # TODO: change to buffer value in node so can work with MATLAB
#             if a['node_path'] in f.file_pointer:
#             # data set exists
#                 ds = f.file_pointer[a['node_path']]
#                 value = ds.value
#                 if not values_match(value, a['agvalue']):
#                     f.warning.append(("'%s' autogen dataset values possibly wrong.\n"
#                         "expected:%s (type %s)\nfound:%s (type %s)") % (a['node_path'], 
#                         a['agvalue'], type(a['agvalue']), value, type(value)))
#                 elif value is None and a['qty'] == '!':
#                     f.error.append(("%s autogen dataset '%s' value required "
#                         "but is empty") % (a['node_path']))
#             else:
#                 # data set does not exist
#                 # if validating this is an error (since dataset should exist)
#                 # Otherwise it's ok because autogen will make it.
#                 if f.reading_file:
#                     f.error.append("%s: autogen dataset not found." %  a['node_path'])

def validate_autogen(f):
    """ Validates that autogen fields have correct values.  i.e. match what was
    generated by "ag_compute".  f is the h5gate file object"""
    for a in f.autogen:
        if a['agvalue'] is None:
            # skip those that have no value
            continue
        if a['aid']:
            # value is stored in attribute
            aid = a['aid']
            node = f.path2node[a['node_path']]
            ats = node.attributes[aid]
            value = ats['nv'] if 'nv' in ats else (
                ats['value'] if 'value' in ats else None)
            compare_autogen_values(f, a, value)
#             if not values_match(value, a['agvalue']):
#                 f.error.append(("'%s' autogen attribute [%s] values incorrect.\n"
#                     "expected:%s (type %s)\nfound:%s (type %s)") % (a['node_path'], aid, 
#                     a['agvalue'], type(a['agvalue']), value, type(value)))
#             elif value is None and a['qty'] == '!':
#                 f.error.append(("%s autogen attribute [%s] value required "
#                     "but is empty") % (a['node_path'], aid))
        else:
            # value is stored in value of a dataset
            # TODO: change to buffer value in node so can work with MATLAB
            if a['node_path'] in f.file_pointer:
            # data set exists
                ds = f.file_pointer[a['node_path']]
                value = ds.value
                compare_autogen_values(f, a, value)
#                 if not values_match(value, a['agvalue']):
#                     f.warning.append(("'%s' autogen dataset values possibly wrong.\n"
#                         "expected:%s (type %s)\nfound:%s (type %s)") % (a['node_path'], 
#                         a['agvalue'], type(a['agvalue']), value, type(value)))
#                 elif value is None and a['qty'] == '!':
#                     f.error.append(("%s autogen dataset '%s' value required "
#                         "but is empty") % (a['node_path']))
            else:
                # data set does not exist
                # if validating this is an error (since dataset should exist)
                # Otherwise it's ok because autogen will make it.
                if f.reading_file:
                    f.error.append("%s: autogen dataset not found." %  a['node_path'])

def compare_autogen_values(f, a, value):
    """ Compare value in hdf5 file to expected value computed by autogen.  Save error
    or warning message if the expected value does not match the value found.
    f - h5gate file object
    a - row of f.autogen
    value - value in (or being stored in) hdf5 file for autogen field
    """
    if values_match(value, a['agvalue']):
        # value match, check for value required but missing
        if value is None and a['qty'] == '!':
            msg = "value required but is empty."
            report_autogen_problem(f, a, msg)
        return
    # values do not match, check if match when values are sorted
    if isinstance(value, (list, np.ndarray)):
        sorted_value = natural_sort(value)
        if values_match(sorted_value, a['agvalue']):
            # sorted values match
            if a['sort']:
                msg = "values are correct, but not sorted."
                report_autogen_problem(f, a, msg)
            return
    # neither original or sorted values match
    msg = ("values incorrect.\nexpected:%s (type %s)\n"
        "found:%s (type %s)") % (a['agvalue'], type(a['agvalue']), value, type(value))
    report_autogen_problem(f, a, msg)
    
    
def report_autogen_problem(f, a, msg):
    if a['aid']:
        # value stored in attribute
        aid = a['aid']
        f.error.append("'%s': autogen attribute [%s] %s" % (a['node_path'], aid, msg))
    else:
        # value stored in dataset
        output_msg = "'%s': autogen dataset %s" % (a['node_path'], msg)
        if a['agtype'] == 'length':
            # display warnings for lengths different than expected (this is
            # done for NWB format, since length only used in one place, e.g.
            # timeseries num_samples.  Should modify specification language
            # to allow specifying either a warning or an error in autogen
            f.warning.append(output_msg)
        else:
            f.error.append(output_msg)


def update_autogen(f, a):
    """Update values that are stored in autogen fields.  This processes one
    autogen."""
    if a['agvalue'] is None:
        # skip those that have no value
        return
    if a['aid']:
        # value is stored in attribute
        aid = a['aid']
        node = f.path2node[a['node_path']]
        ats = node.attributes[aid]
        value = ats['nv'] if 'nv' in ats else (
            ats['value'] if 'value' in ats else None)
        if not values_match(value, a['agvalue']):
            # values do not match, update them
            ats['nv'] = a['agvalue']
            f.set_attribute(a['node_path'], aid, a['agvalue'])
    else:
        if a['node_path'] in f.path2node:
        # dataset exists
            ds = f.file_pointer[a['node_path']]
            value = ds.value
            if not values_match(value, a['agvalue']):
                f.error.append(("%s autogen dataset values do not match.  Unable to update.\n"
                    "  expected:%s\nfound:%s") % (a['node_path'], 
                    str(a['agvalue']), str(value)))
        else:
            # data set does not exist.  Create it using autogen value
            enclosing_path, name = a['node_path'].rsplit('/',1)
            grp = f.path2node[enclosing_path]
            # pretend to be a client program creating the data set with the desired value
            grp.set_dataset(name, a['agvalue'])


# def update_autogen_old(f):
#     """Update values that are stored in autogen fields.  This should be
#     called before closing a file that was opened in write (or read/write)
#     mode to update the autogen values before validating and saving the file."""
#     for a in f.autogen:
#         if a['agvalue'] is None:
#             # skip those that have no value
#             continue
#         if a['aid']:
#             # value is stored in attribute
#             aid = a['aid']
#             node = f.path2node[a['node_path']]
#             ats = node.attributes[aid]
#             value = ats['nv'] if 'nv' in ats else (
#                 ats['value'] if 'value' in ats else None)
#             if not values_match(value, a['agvalue']):
#                 # values do not match, update them
#                 ats['nv'] = a['agvalue']
#                 f.set_attribute(a['node_path'], aid, a['agvalue'])
#         else:
#             if a['node_path'] in f.path2node:
#             # dataset exists
#                 ds = f.file_pointer[a['node_path']]
#                 value = ds.value
#                 if not values_match(value, a['agvalue']):
#                     f.error.append(("%s autogen dataset values do not match.  Unable to update.\n"
#                         "  expected:%s\nfound:%s") % (a['node_path'], 
#                         str(a['agvalue']), str(value)))
#             else:
#                 # data set does not exist.  Create it using autogen value
#                 enclosing_path, name = a['node_path'].rsplit('/',1)
#                 grp = f.path2node[enclosing_path]
#                 # pretend to be a client program creating the data set with the desired value
#                 grp.set_dataset(name, a['agvalue'])

                           
def get_param(dict, key, default):
    """ Return value from dictionary if key present, otherwise return default value"""
    val = dict[key] if key in dict else default
    return val
    
                

    
    
#     error = None
#     params = None
#     if not isinstance(agspec, (list, tuple)):
#         error = "Invalid 'autogen' specification.  Must be array: %s" % agspec
#     else:
#         if agspec[0] == 'links':
#             if len(agspec) == 3:
#                 if agspec[2] != 'trim':
#                     error = ("Invalid 'links' autogen specification.  If present, "
#                         "third parameter must be keyword 'trim': %s") % agspec
#                 else:
#                     params = {'trim':True}
#             elif len(agspec) == 2:
#                 params = {'trim':False}  # default is False
#             else:
#                 error = ("Invalid 'links' autogen specification.  Must have either"
#                     " two or three elments: %s") % agspec
#         elif agspec[0] == 'link_path':
#             if len(agspec) != 2:
#                 error = ("Invalid 'link_path' autogen specification.  Must have"
#                     " two elments: %s") % agspec
#         else:
#             error = "Invalid autogen specification.  Must be 'links' or 'link_path': %s" % agspec 
#         # done checking for errors
#         if error:
#             f.error.append(error)
#             return None
#         # Seems ok.  Save it.
#         # save_autogen(f, node, aid, agtarget, agtype,    params)
#         a = save_autogen(f, node, aid, agspec[1], agspec[0], params)
#         return a


    

        
#         for type in ('hard', 'soft'):
#             path2lg = self.links['path2lg'][type]
#             if full_path in path2lg:
#                 # this node is part of a link group
#                 loc = path2lg[full_path]
#                 # see if target already created and identified
#                 if loc in self.links['targets_created']:
#                     target_node = self.links['targets_created'][loc]
#                     link_info = {'node': target_node}
#                     return
#                 # Target not already created and identified
#                 # See if soft-link.  If so, the target is the link group location, see
#                 # if it's been created.
#                 if type == 'soft':
#                     target_path = loc
#                     if target_path in self.path2node
#                         target_node = self.path2node[target_path]
#                         # save target_node in links 'targets_created'
#                         self.links['targets_created'] = target_node
#                         link_info =  = {'node': target_node}
#                         return link_info
#                     # target node not yet created.
#                     link_info = {'node': None}
#                     return link_info            
#         hp = self.links['path2lg']['hard']



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "format is:"
        print "pyhton %s <hdf5_file_name>" % sys.argv[0]
        sys.exit(0)
    fname = sys.argv[1]
    try:
        fp = h5py.File(fname, "r")
        # f = h5py.h5f.open(fname, h5py.h5f.ACC_RDONLY)
    except IOError:
        print "Unable to open file '%s'" % fname
        sys.exit(1)
    links = initialize()
    find(fp, links)
    fp.close()
#     print "found links are:"
#     pp.pprint(links)
    # pp.ppshow_links(links)
    show_stats(links)
    
    

# main
# 
# # test_ginfo(f)
# links = find_links(f)
# # links = test_links()
# print "Before anything:"
# show_links(links)
# merge_soft_links(links);
# prune_hard_links(links)
# print "After merge, and prune, before merge_soft_and_hard_lgs"
# show_links(links)
# merge_soft_and_hard_lgs(links)
# print "After merge_soft_and_hard_lgs:"
# show_links(links)
# f.close()
