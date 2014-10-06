#!/usr/bin/env python
# -*- coding: utf-8

'''
Created on 19/08/2014

@author: jeel
'''
from tools.xml_tools import xml_tools

def decodeDictTree(dict_tree,encoding='UTF-8'):
    '''
    Recursively change encoding for all elements to UTF-8 (default) 
    
    '''
    if type(dict_tree) is list:
        if len(dict_tree) == 1:
            # Only one branch, traverse into this
            dict_tree[0] = decodeDictTree(dict_tree[0],encoding)
        else:
            # Traverse through multiple branches
            for sub_dict_tree in dict_tree:
                dict_tree[sub_dict_tree] = decodeDictTree(sub_dict_tree,encoding)
    elif type(dict_tree) is dict:
        for key,value in dict_tree.items():
            if isinstance(value,str):
                try:
                    dict_tree[key] = value.decode(encoding)
                except Exception as e:
                    print(value)
                    print(type(value))
                    raise e
            elif isinstance(value,dict):
                dict_tree[key] = decodeDictTree(dict_tree[key],encoding)
    return dict_tree

def parseXmlToDict(xml_file):
    '''
    Returns a dictionary tree from a XML file
    :param xml_file: path to xml_tools file
    '''
    etree,ns = xml_tools.parse_and_get_ns(xml_file)
    dict_tree = xml_tools.etree_to_dict(etree.getroot())
    return dict_tree,ns

def getAttribValuesByName(dict_tree,attribute_key):
    '''
    Returns a list of attribute values within a tree where the attribute key
    = "attribute_key".
    E.g. all the IDs or DMDIDs within the logical struct map.
    Is used to calculate first available ID for a DMD section.
    :param dict_tree: a dict_tree
    :param attribute_key: name of the attribute to search for.
    '''
    attrib_values = []
    if type(dict_tree) is dict:
        for key,val in dict_tree.items():
            if type(val) is str:
                if attribute_key == key:
                    attrib_values.append(val)
            elif type(val) is dict or type(val) is list:
                attrib_values.extend(getAttribValuesByName(val,attribute_key))
    elif type(dict_tree) is list:
        for dict_sub_tree in dict_tree:
            attrib_values.extend(getAttribValuesByName(dict_sub_tree,attribute_key))
    return attrib_values