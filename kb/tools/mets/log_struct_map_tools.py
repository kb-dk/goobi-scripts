'''
Created on 19/08/2014

@author: jeel
'''

import os,sys
import pprint

lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../')
sys.path.append(lib_path)

from xml_tools import dict_tools, xml_tools

#===============================================================================
# Add dmdSection to logical struct map with applied rules for types in hierarchy
#===============================================================================

def addSectionToLogicalStructMap(dict_tree, sec_id,sec_type,parent_attrib=None,
                                 sec_dmdid=None):
    '''
    Adds a section to a logical struct map within a dict tree and returns the
    resulting dict tree
     
    :param dict_tree: the dict_tree with a logical struct map to insert the
    section to
    :param sec_id: the id of the section 
    :param sec_type: the type of the section
    :param parent_attrib: the attribute of the a section within the dict_tree to
    insert the new section under  
    :param sec_dmdid: the dmd id of the section
    
    Structure of xml_tools:
    <mets:structMap TYPE="LOGICAL">
        <mets:div ID="LOG_0000" TYPE="Periodical">
            <mets:div DMDID="DMDLOG_0000" ID="LOG_0001" TYPE="PeriodicalVolume">
    '''
    # TODO add this to config or extract from ruleset
    allowed_types = [{'Periodical':[{'PeriodicalVolume':[{'FrontMatter': ['Article'],
                                                          'Articles': ['Article'],
                                                          'BackMatter': ['Article']
                                                          }
                                                       ]}
                                   ]
                     }]
    mets_elem = '{http://www.loc.gov/METS/}mets'
    struct_map_elem = '{http://www.loc.gov/METS/}structMap'
    std_elem = '{http://www.loc.gov/METS/}div'
    logical_struct_map_type_key = '@TYPE'
    logical_struct_map_type_val = 'LOGICAL'
    
    # Create new logical element to be added
    new_elem = {'@ID':sec_id,'@TYPE':sec_type}
    new_elem_type = sec_type
    if sec_dmdid is not None:
        new_elem['@DMDID'] = sec_dmdid
    # Get list of struct maps
    struct_maps = dict_tree[mets_elem][struct_map_elem]
    # Get the logical struct map from list of struct maps
    log_struct_map = [x for x in struct_maps
                      if (logical_struct_map_type_key in x and 
                          x[logical_struct_map_type_key] == logical_struct_map_type_val)]
    # Only one logical struct map allowed
    if not len(log_struct_map) == 1:
        err = ('Only one logical struct allowed in in dict_tree. '
               '{0} found.'.format(len(log_struct_map)))
        raise ValueError(err)
    # Update logical struct map - is located with a div-elem
    log_struct_map = log_struct_map[0][std_elem]
    log_struct_map = insertByTypeToHierarchy(log_struct_map,
                                             new_elem_type,
                                             new_elem,std_elem,
                                             type_hierarchy=allowed_types,
                                             parent_attrib=parent_attrib)
    # Replace the old logical struct map with the updated in dict_tree 
    # Remove the old one
    for struct_map in struct_maps:
        if (logical_struct_map_type_key in struct_map and
            struct_map[logical_struct_map_type_key] == logical_struct_map_type_val):
            struct_maps.remove(struct_map)
    # Insert the new one - remember too add as dictionary with key std_elem
    # and attributes.
    # Logical must come before physical=>Insert in the beginning of struct_map
    log_struct_map = {std_elem:log_struct_map,
                      logical_struct_map_type_key:logical_struct_map_type_val}
    struct_maps.insert(0,log_struct_map)
    #Replace in dictg tree
    dict_tree[mets_elem][struct_map_elem] = struct_maps
    # Return updated dict_tree 
    return dict_tree

def inElemDict(elem,attrib):
    '''
    Returns true if elem contains attrib
    
    :param elem: a list of attributes tuples
    :param attrib: an attribute tuple 
    '''
    return '@'+attrib[0] in elem and elem['@'+attrib[0]] == attrib[1]

def inElemsList(elems,attrib):
    '''
    Returns true if attrib is in a list of elems
    
    :param elems: a list of elems
    :param attrib: a attribute tuple to look for
    '''
    if type(elems) is dict:
        return inElemDict(elems,attrib)
    elif type(elems) is list:
        for elem in elems:
            if type(elems) is dict: 
                if inElemDict(elem,attrib): return True

def getAllowedTypesOnCurrentLevel(tree):
    '''
    Return a list of keys of the top level of "tree"
    
    :param tree: a string, a dict or list of strings.
    '''
    types = []
    if type(tree) is str:
        types = [tree]
    elif type(tree) is list:
        for ht in tree: # Look at this level in the type type_hierarki
            if (type(ht) is dict):
                types.extend(ht.keys())
            elif (type(ht) is str):
                types.append(ht)
    elif type(tree) is dict:
        types = tree.keys()
    else:
        types = types# TODO raise error
    return types

def insertElemToElemTree(elem_tree,new_elem):
    '''
    Inserts an element to an element tree
    
    :param elem_tree:
    :param new_elem:
    '''
    result_tree = None
    if elem_tree is None:
        # New element to be added to parent
        result_tree = new_elem
    elif type(elem_tree) is dict:
        # From one to multiple elements => dict to list of dicts 
        result_tree = [elem_tree].append(new_elem)
    elif type(elem_tree) is list:
        # Data is a list of elements, add to this list
        result_tree = elem_tree.append(new_elem)
    return result_tree

def getListOfSubTrees(dict_tree,sub_elem_key=None):
    '''
    Returns a list of all the sub trees in dict_tree. Can be narrowed down
    by selecting a key to traverse by
    
    :param dict_tree: the dict tree to traverse
    :param sub_elem_key: the key of a sub element to traverse by
    '''
    
    sub_trees = []
    if type(dict_tree) is list:
        if len(dict_tree) == 1:
            # Only one branch, traverse into this
            sub_trees = getListOfSubTrees(dict_tree[0],sub_elem_key)
        else:
            # Traverse through multiple branches
            for sub_dict_tree in dict_tree:
                sub_trees.append(sub_dict_tree)
    elif type(dict_tree) is dict:
        if sub_elem_key is not None:
            # Get subelement by sub_elem_key
            if sub_elem_key in dict_tree:
                if type(dict_tree[sub_elem_key]) is list:
                    sub_trees = dict_tree[sub_elem_key]
                else:
                    sub_trees.append(dict_tree[sub_elem_key])
        else:
            for value in dict_tree.values():
                if type(value) is dict:
                    sub_trees.append(value)
                elif type(value) is list:
                    sub_trees.extend(value) 
    return sub_trees
    

def insertByTypeToHierarchy(dict_tree,new_elem_type,new_elem,std_elem,
                           type_hierarchy,parent_attrib=None,is_root=True):
    '''
    Inserts a new element into a dict_tree with the location defined by the 
    type hierarchy. The function works recursively on the dict_tree
    
    :param dict_tree:
    :param new_elem_type: the type of the element to insert
    :param new_elem: a dict of attrib name->values
    :param std_elem: the standard element to insert under
    :param type_hierarchy: the hierarchy of types defining where to insert 
    element
    :param parent_attrib: if specified this must be a tuple of an attribe name 
    and value which defines under which element the new element must be added.
    E.g. ('TYPE','PeriodicalVolume')
    :param is_root: used internal to define whether the dict_tree is the root 

    TODO: change to breadth first instead of depth first
    '''

    types = getAllowedTypesOnCurrentLevel(type_hierarchy)
    updated_tree = None
    if new_elem_type in types:
        updated_tree = insertElemToElemTree(dict_tree,new_elem)
    if not updated_tree is None:
        return updated_tree
    if updated_tree is None and dict_tree is None:
        # An element needs a parent element to be added, there do not traverse
        return None
    # Not valid level. Traverse the type type_hierarchy
    # Add None as the first element to create new element on level
    sub_elem_trees =[None]# makes it possible to add elem under a branch in elem tree
    sub_elem_trees.extend(getListOfSubTrees(dict_tree,std_elem)) 
    this_type_hierarchy_level = getListOfSubTrees(type_hierarchy)
    for sub_hierarchy in this_type_hierarchy_level:
        for sub_elem_tree in sub_elem_trees:
            updated_sub_elem_tree = insertByTypeToHierarchy(sub_elem_tree,
                                                           new_elem_type,
                                                           new_elem,std_elem,
                                                           sub_hierarchy,
                                                           parent_attrib,
                                                           is_root=False)
            if updated_sub_elem_tree is not None: # The tree with inserted element
                # Check 
                #    - if parent_attrib is set,
                #    - if the current updated_sub_elem_tree
                #    - if the tree in which the new elem has been added and then check
                #    - if the parrent is correct --> i.e. if this place is the allowed place
                #      to add the element in the dict tree according to parent_attrib
                if ((parent_attrib) and
                    ('@TYPE' in updated_sub_elem_tree) and 
                    (new_elem_type == updated_sub_elem_tree['@TYPE'])):
                    if not inElemsList(dict_tree,parent_attrib):
                        return None
                    #else: the element is placed at the correct place
                if dict_tree is None:# At the bottom of the tree - sub_elem_trees will always be [None]
                    return updated_sub_elem_tree
                else:
                    sub_elem_trees.remove(None) # Remove None in sub_elem_trees
                    if sub_elem_tree is not None: # replace updated tree with sub tree
                        sub_elem_trees.remove(sub_elem_tree)
                    if len(sub_elem_trees) == 0: # Insert into dict_tree as dic - bottom of orig tree
                        sub_elem_trees = updated_sub_elem_tree
                    else:
                        sub_elem_trees.append(updated_sub_elem_tree)
                    dict_tree[std_elem] = sub_elem_trees 
                return dict_tree
    if is_root:
        err = ('Error: no valid elements to contain new element '
               'with type {0}. A new parent element to new element '
               'might needs to be added.')
        err = err.format(new_elem_type)
        raise ValueError(err)

def getAvailableStructMapLogId(log_struct_map):
    '''
    Returns the first available ID in a logical struct map 
    :param log_struct_map:
    '''
    log_ids = sorted(dict_tools.getAttribValuesByName(log_struct_map,'@ID'))
    # The StructMapLogs has the form 'LOG_0001'
    last_log_id = log_ids[-1].split('_')[-1]
    next_log_id = 'LOG_'+str(int(last_log_id)+1).zfill(4)
    return next_log_id

def getAvailableStructMapDmdLogId(log_struct_map):
    '''
    Returns the first available DMDID in a logical struct map 
    :param log_struct_map:
    '''
    log_ids = sorted(dict_tools.getAttribValuesByName(log_struct_map,'@DMDID'))
    # The StructMapLogs has the form 'LOG_0001'
    last_log_id = log_ids[-1].split('_')[-1]
    next_log_id = 'DMDLOG_'+str(int(last_log_id)+1).zfill(4)
    return next_log_id

def getChildrenLogIds(parent):
    div_key = '{http://www.loc.gov/METS/}div'
    log_ids = []
    if parent is None: return log_ids
    no_children = (not isinstance(parent, dict) or 
                   (isinstance(parent, dict) and div_key not in parent))
    if no_children: return log_ids
    if isinstance(parent[div_key],dict) and '@ID' in parent[div_key]:
        log_ids.append(parent[div_key]['@ID'])
    elif isinstance(parent[div_key],list):
        for child in parent[div_key]:
            if isinstance(child, dict) and '@ID' in child:
                    log_ids.append(child['@ID'])
    return log_ids

def getLogicalStructMap(dict_tree,ns=None):
    '''
    Returns the logical structMap sub tree from dict_tree
    :param dict_tree:
    :param ns:
    '''
    if ns is None:
        ns = '{http://www.loc.gov/METS/}'
    else:
        ns = ns['mets']
    log_struct_map_dict = xml_tools.getSubTree(dict_tree=dict_tree,
                                               ns=ns,
                                               elem_name='structMap',
                                               elem_attrib_key='TYPE',
                                               elem_attrib_val='LOGICAL')
    return log_struct_map_dict

def getFirstDmdLogByDocType(dict_tree,doc_type):
    log_doc_struct = getLogicalStructMap(dict_tree)
    ns = '{http://www.loc.gov/METS/}'
    dmdlog_id_key = '@DMDID'
    doc_type_trees = xml_tools.getSubTree(log_doc_struct,
                                          ns=ns,
                                          elem_name='div',
                                          elem_attrib_key='TYPE',
                                          elem_attrib_val = doc_type)
    if isinstance(doc_type_trees,list):
        if len(doc_type_trees) > 1:
            for dmd in doc_type_trees:
                if isinstance(dmd,dict) and dmdlog_id_key in dmd:
                    return dmd[dmdlog_id_key]
    elif isinstance(doc_type_trees,dict):
        if dmdlog_id_key in doc_type_trees: return doc_type_trees[dmdlog_id_key]
    else:
        return None