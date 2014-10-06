#!/usr/bin/env python
'''
Created on 08/07/2014

@author: jeel
'''
from collections import defaultdict
from xml.etree import ElementTree as ET
import sys
import pprint
import codecs

def getSubTree(dict_tree,ns=None, elem_name=None,elem_attrib_key=None,
               elem_attrib_val=None):
    '''
    This is a depth-first search algorithm
    
    Use this to get lists of dicts as output
    
    dict_tree is a dictionary of lists or dictionaries
    ns is the namespace, e.g. {http://www.loc.gov/METS/}
    elem_name is the name of elem the find as parent of the resulting sub dict_tree
    elem_atrrib is a tuple of the key and value of the root in the new sub dict_tree
        second element may be empty
    '''
    if dict_tree is None: return None
    if type(dict_tree) is dict:
        correct_tree = False
        lookup_name = elem_name
        lookup_dict_tree = dict_tree
        if ns is not None:
            if elem_name is None:
                err = ('Element name cannot not be empty if ns is given')
                raise ValueError(err)
            else:
                lookup_name = ns+elem_name
        if lookup_name is not None: # Find lookup_name
            if lookup_name in dict_tree:
                correct_tree = True
                lookup_dict_tree = dict_tree[lookup_name]
        else: # No lookup name -> look at this level and check attribs
            correct_tree = True
        if (elem_attrib_key is not None): # Find attrib key
            # @is added by etree_to_dict to attribs
            if '@'+elem_attrib_key in lookup_dict_tree:
                if elem_attrib_val is not None: # Check attrib val
                    correct_tree = (lookup_dict_tree['@'+elem_attrib_key] == elem_attrib_val)
                else: correct_tree = True
            else: correct_tree = False
        if not correct_tree:
            if len(dict_tree) > 0:
                
                for _,val in dict_tree.items():
                    if type(val) is dict or type(val) is list:
                        subtree = getSubTree(val,ns, elem_name,
                                             elem_attrib_key,elem_attrib_val)
                        if subtree is not None: return subtree
                return None
            return None
        else:
            return lookup_dict_tree
    elif type(dict_tree) is list:
        # loop multiple branches
        for sub_etree in dict_tree:
            # traverse each branch
            subtree =  getSubTree(sub_etree,ns, elem_name,elem_attrib_key,
                                  elem_attrib_val)
            if subtree is not None: return subtree

def getAllSubTrees(dict_tree,ns=None, elem_name=None,elem_attrib_key=None,
                   elem_attrib_val=None):
    '''
    Use this to get lists of dicts as output
    
    dict_tree is a dictionary of lists or dictionaries
    ns is the namespace, e.g. {http://www.loc.gov/METS/}
    elem_name is the name of elem the find as parent of the resulting sub dict_tree
    elem_atrrib is a tuple of the key and value of the root in the new sub dict_tree
        second element may be empty
    
    ns,elem_name and elem_attrib may be None
    '''
    if dict_tree is None or dict_tree is []: return None
    subtrees = []
    lookup_name = elem_name
    if elem_name and ns: lookup_name = ns+elem_name
    if type(dict_tree) is dict:
        #=======================================================================
        # dict_tree is a dictionary
        #=======================================================================
        correct_tree = False # As default dive into branch
        if lookup_name and lookup_name in dict_tree: # Find lookup_name
            lookup_dict_tree = dict_tree[lookup_name]
            correct_tree = True
        else:
            lookup_dict_tree = dict_tree
        if elem_attrib_key: # Check for elem_attribute
            if '@'+elem_attrib_key in lookup_dict_tree: # @is added by etree_to_dict to attribs
                if elem_attrib_val is not None: # Check attrib val
                    correct_tree = lookup_dict_tree['@'+elem_attrib_key] == elem_attrib_val
                else: correct_tree = True
            else: correct_tree = False
        if not correct_tree: # Dive in
            if len(dict_tree.keys()) > 0:
                for _,val in dict_tree.items():
                    if type(val) is dict or type(val) is list:
                        subtree = getAllSubTrees(val,ns, elem_name,
                                                 elem_attrib_key,elem_attrib_val)
                        if subtree: subtrees.extend(subtree)
                return subtrees
            return None
        else:
            return [lookup_dict_tree] if lookup_name else [dict_tree]
    #===========================================================================
    # dict_tree is a list
    #===========================================================================
    elif type(dict_tree) is list:
        # loop multiple branches
        for sub_etree in dict_tree:
            '''# Check if this branch is correct before diving into it
            if (isinstance(sub_etree,dict) and 
                (elem_attrib_key) and '@'+elem_attrib_key in sub_etree):
                if (elem_attrib_val):
                    if lookup_dict_tree['@'+elem_attrib_key] == elem_attrib_val:
                        return[sub_etree]
                else: return[sub_etree]'''
            if lookup_name: sub_etree = {lookup_name:sub_etree}
            # traverse each branch.
            subtree =  getAllSubTrees(sub_etree,ns, elem_name,elem_attrib_key,
                                      elem_attrib_val)
            if subtree: subtrees.extend(subtree)
        return subtrees

def getSingleSection(etree,ns,elem_name,attrib='',attrib_val=''):
    elem_etrees = findAllElements(etree,
                                  ns=ns,
                                  elem_name=elem_name,
                                  attrib=attrib,
                                  attrib_val=attrib_val)
    if len(elem_etrees) > 1:
        err = 'More than one element {0} with attribute {1} = {2} found.'
        err = err.format(elem_name,attrib,attrib_val)
        raise ValueError(err)
    return elem_etrees[0]


def findAllElements(etree,ns='',elem_name='',child_tag='',attrib='',attrib_val=''):
    '''
    Use this to get ETrees as output
    '''
    
    child_tag_str = ''
    if ((attrib is not '') and (child_tag is not '')):
        err = 'Tag and attribute cannot be search for at the same time'
    elif (child_tag is not ''):
        child_tag_str = '[{0}]'.format(child_tag)
    attrib_str = ''
    if ((attrib is not '') and (attrib_val is not '')):
        attrib_str = '[@{0}="{1}"]'
        attrib_str = attrib_str.format(attrib,attrib_val)
    elif (attrib is not ''):
        attrib_str = '[@{0}]'.format(attrib)
    elif ((attrib is '') and (attrib_val is not '')):
        err = 'Attribute name must be defined to search for attribute value'
        raise ValueError(err)
    xpath = './{0}{1}{2}{3}'
    # Notice either tag_str or attrib_str will be = ""
    xpath = xpath.format(ns,elem_name,child_tag_str,attrib_str)
    try:
        etree_elems = etree.findall(xpath)
    except KeyError as e:
        print(xpath)
        raise e
    return etree_elems

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        '''temp_dict = dict()
        for k, v in dd.items():
            if len(v) == 1: temp_dict[k]=v[0]
            else: temp_dict[k]=v
        d = {t.tag:temp_dict}'''
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def writeDictTreeToFile(dict_tree,dest):
    etree = dict_to_etree(dict_tree)
    etree.write(dest)
    
try:
    basestring
except NameError:  # python3
    basestring = str

def dict_to_etree(d):
    #http://stackoverflow.com/a/10076823/3760158
    def _to_etree(d, root):
        if not d:
            pass
        elif isinstance(d, basestring):
            root.text = d
        elif isinstance(d, dict):
            for k,v in d.items():
                assert isinstance(k, basestring)
                if k.startswith('#'):
                    assert k == '#text' and isinstance(v, basestring)
                    root.text = v
                elif k.startswith('@'):
                    assert isinstance(v, basestring)
                    root.set(k[1:], v)
                elif isinstance(v, list):
                    for e in v:
                        _to_etree(e, ET.SubElement(root, k))
                else:
                    _to_etree(v, ET.SubElement(root, k))
        else: assert d == 'invalid type'
    assert isinstance(d, dict), 'Dict tree must be a dictionary but is a '+str(type(d))
    assert len(d) == 1, 'Dict tree must only contain one element, but contains '+str(len(d))
    tag, body = next(iter(d.items()))
    node = ET.Element(tag)
    _to_etree(body, node)
    etree = ET.ElementTree(node)
    return etree

def parse_and_get_ns(file_path):
    events = "start", "start-ns"
    root = None
    ns = {}
    for event, elem in ET.iterparse(file_path, events,parser=ET.XMLParser(encoding='utf-8')):
        if event == "start-ns":
            ns_key = str(elem[0])
            if ns_key in ns and ns[ns_key] != '{'+elem[1]+'}':
                raise KeyError("Duplicate prefix with different URI found. "
                               "NS: {0}. ns[elem[0]]: {1}. elem[1]: {2}"
                               .format(ns,ns[elem[0]],elem[1]))
                # NOTE: It is perfectly valid to have the same prefix refer
                #     to different URI namespaces in different parts of the
                #     document. This exception serves as a reminder that this
                #     solution is not robust.    Use at your own peril.
            ns[ns_key] = "{%s}" % elem[1]
        elif event == "start":
            if root is None:
                root = elem
    return ET.ElementTree(root), ns

if __name__ == '__main__':
    pass
