#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 19/08/2014

@author: jeel
'''
import pprint

from tools.mets import phys_struct_map_tools


def get(dict_tree):
    mets_elem = '{http://www.loc.gov/METS/}mets'
    struct_link_elem = '{http://www.loc.gov/METS/}structLink'
    # Check dict_tree
    if mets_elem not in dict_tree:
        err = ('dict_tree must contain {0}'.format(mets_elem))
        raise ValueError(err)
    if struct_link_elem not in dict_tree[mets_elem]:
        err = ('dict_tree must contain {0}'.format(struct_link_elem))
        raise ValueError(err)
    return dict_tree[mets_elem][struct_link_elem]

def insert(struct_link,dict_tree):
    mets_elem = '{http://www.loc.gov/METS/}mets'
    struct_link_elem = '{http://www.loc.gov/METS/}structLink'
    # Check dict_tree
    if mets_elem not in dict_tree:
        err = ('dict_tree must contain {0}'.format(mets_elem))
        raise ValueError(err)
    if struct_link_elem not in dict_tree[mets_elem]:
        err = ('dict_tree must contain {0}'.format(struct_link_elem))
        raise ValueError(err)
    dict_tree[mets_elem][struct_link_elem] = struct_link
    return dict_tree 

def exists(dict_tree,log_id):
    '''
    Return true if log_id exists in struct_link
    :param log_struct_map:
    :param log_id:
    '''
    struct_link = get(dict_tree)
    if not struct_link: return False
    sm_link_key = '{http://www.loc.gov/METS/}smLink'
    from_key = '@{http://www.w3.org/1999/xlink}from'
    if sm_link_key not in struct_link: return False
    for sm_link in struct_link[sm_link_key]:
        if sm_link[from_key] == log_id: return True
    return False

def getPhysListByLogIds(dict_tree,log_ids):
    '''
    Returns a list of physical pages (PHYS_NNNN) assigned to a list of dmd ids (LOG_NNNN)
    :param dict_tree:
    :param log_ids:
    '''
    sm_link_key = '{http://www.loc.gov/METS/}smLink'
    from_key = '@{http://www.w3.org/1999/xlink}from'
    to_key = '@{http://www.w3.org/1999/xlink}to'
    phys_list = []
    struct_link = get(dict_tree)
    #===========================================================================
    # Simple checks
    #===========================================================================
    no_sm_link = (not struct_link or (struct_link and 
                                      isinstance(struct_link,dict) and
                                      sm_link_key not in struct_link))
    if no_sm_link: return phys_list
    #===========================================================================
    # Retrieve PHYS-ids
    #===========================================================================
    for sm_link in struct_link[sm_link_key]:
        # Add if correct from and not already in phys_list
        if (sm_link[from_key] in log_ids and # Correct LOG-id 
            sm_link[from_key] not in phys_list): # Not already added to list (duplicate)
            phys_list.append(sm_link[to_key])
    return phys_list

def addStructLinks(dict_tree,link_from,doc_struct_info):
    '''
    Adds a struct link to a physical struct map and returns an updated version 
    of dict_tree with links inserted.
    
    :param dict_tree: a dictionary tree with complete goobi metadata
    :param link_from: the logical section to link to, e.g. LOG_0001
    :param doc_struct_info: a dictonary with at least start_page and end_page

    '''
    # Set variables
    struct_link = get(dict_tree)

    start_page_key = 'start_page'
    end_page_key = 'end_page'
    # Check doc_struct_info
    assert start_page_key in doc_struct_info, \
           'doc_struct_info must contain "{0}"'.format(start_page_key)
    assert end_page_key in doc_struct_info, \
           'doc_struct_info must contain "{0}"'.format(end_page_key)
    
    start_page = doc_struct_info[start_page_key]
    end_page = doc_struct_info[end_page_key]
    physical_struct_map = phys_struct_map_tools.get(dict_tree)
    pages = phys_struct_map_tools.createPages(physical_struct_map,start_page,end_page)
    # Insert links
    struct_link = addLinksToStructLink(struct_link, link_from, pages)
    # Update tree
    dict_tree = insert(struct_link,dict_tree)
    # Return updated tree
    return dict_tree

def addLinks(dict_tree,link_from,link_to_list):
    struct_link = get(dict_tree)
    struct_link = addLinksToStructLink(struct_link,link_from,link_to_list)
    dict_tree = insert(struct_link,dict_tree)
    return dict_tree

def addLinksToStructLink(struct_link,link_from,link_to_list):
    '''
    Adds a list of links to a struct link elem
    
    :param struct_link:
    :param link_from: log_id, e.g. LOG_0001
    :param link_to_list: a list of physical ids to link to, 
        e.g. ['PHYS_0001','PHYS_0002']
    '''
    sm_link_key = '{http://www.loc.gov/METS/}smLink'
    # Check tree
    if struct_link is None:
        # Create new list if no one exists
        struct_link_list = []
        struct_link = {sm_link_key: []}
    else:
        # Extract the list of struct links
        struct_link_list = struct_link[sm_link_key]
    # Insert list of new links to struct link list
    xlink = '@{http://www.w3.org/1999/xlink}'
    '''
    linkFrom = 'LOG_0001'
    linkToList = ['PHYS_0001']
    '''
    link_from_elem = '{0}{1}'.format(xlink,'from')
    link_to_elem = '{0}{1}'.format(xlink,'to')
    for linkTo in link_to_list:
        link = {link_from_elem:link_from,link_to_elem:linkTo}
        struct_link_list.append(link)
    struct_link[sm_link_key] = struct_link_list
    # return updated list
    return struct_link
