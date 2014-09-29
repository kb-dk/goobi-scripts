#!/usr/bin/python
# -*- encoding: utf-8 -*-

'''
Created on 19/08/2014

@author: jeel
'''
import os,sys

lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../')
sys.path.append(lib_path)
from xml_tools import xml_tools


def isEmpty(file_sec):
    '''
    Returns true if file_sec contains a non empty list of file links.
    :param file_sec:
    '''
    file_grp_key = '{http://www.loc.gov/METS/}fileGrp'
    file_key = '{http://www.loc.gov/METS/}file'
    if not file_sec: # is empty if file_sec is not present in dict_tree at all
        return True
    if not file_grp_key in file_sec:
        return True
    if not file_key in file_sec[file_grp_key]:
        return True
    return len(file_sec[file_grp_key][file_key]) == 0

def isValid(file_sec,images):
    '''
    Returns true if the file paths in file_sec corresponds to the files given
    in images
    :param file_sec:
    :param images:
    '''
    if isEmpty(file_sec): return False
    files = getFiles(file_sec)
    if len(images) != len(files): return False
    file_paths = getFilePaths(files)
    for file_path in images.keys(): # keys are file paths in images (se fs.getImages)
        if file_path not in file_paths: return False
    return True 

def getFiles(file_sec):
    '''
    Extract the file section in file_sec
    :param file_sec:
    '''
    if isEmpty(file_sec): return []
    file_grp_key = '{http://www.loc.gov/METS/}fileGrp'
    file_key = '{http://www.loc.gov/METS/}file'
    return file_sec[file_grp_key][file_key]

def getFilePaths(files):
    '''
    Returns the file paths from the file elements in files
    :param files:
    '''
    file_locater_key = '{http://www.loc.gov/METS/}FLocat'
    href_key = '@{http://www.w3.org/1999/xlink}href'
    href_val = 'file://'
    try:
        file_paths = map(lambda x: x[file_locater_key][href_key].replace(href_val,''),
                         files)
    except (IndexError, KeyError):
        file_paths = []
    return file_paths


def get(dict_tree,ns=None):
    '''
    Returns the file section from dict tree
    :param dict_tree:
    :param ns:
    '''
    
    if ns is None:
        ns = '{http://www.loc.gov/METS/}'
    else:
        ns = ns['mets']
    file_sec = xml_tools.getSubTree(dict_tree=dict_tree,
                                    ns=ns,
                                    elem_name='fileSec')
    return file_sec

def insert(dict_tree,file_sec):
    '''
    Inserts (overwrites) a file_sec into a dict_tree
    :param dict_tree:
    :param file_sec:
    '''
    mets_key = '{http://www.loc.gov/METS/}mets'
    file_sec_key = '{http://www.loc.gov/METS/}fileSec'
    dict_tree[mets_key][file_sec_key] = file_sec
    return dict_tree

def clear(file_sec):
    '''
    Returns an empty file section
    :param dict_tree:
    '''
    file_grp_key = '{http://www.loc.gov/METS/}fileGrp'
    file_grp = {file_grp_key:{'@USE': 'LOCAL'}}
    return file_grp

def clear_dict(dict_tree):
    '''
    Replaces a file section in a METs-file with a empty file section or
    inserts an empty one, if no section is present.
    :param dict_tree:
    '''
    mets_key = '{http://www.loc.gov/METS/}mets'
    file_sec_key = '{http://www.loc.gov/METS/}fileSec'
    file_grp_key = '{http://www.loc.gov/METS/}fileGrp'
    file_grp = {file_grp_key:{'@USE': 'LOCAL'}}
    dict_tree[mets_key][file_sec_key] = file_grp
    return dict_tree

def create(file_sec,images):
    '''
    Returns a file_sec with the image information from images added
    :param file_sec: a dict tree with file sec
    :param images: a dictionary with image_path -> {'mimetype'->mimetype}
    '''
    if isValid(file_sec, images):
        # Only create new file section if current isnt valid
        return file_sec
    else:
        file_sec = clear(file_sec)
    file_grp_key = '{http://www.loc.gov/METS/}fileGrp'
    file_key = '{http://www.loc.gov/METS/}file'
    files = []
    i = 0
    for image_path in sorted(images.keys()):
        image = images[image_path]
        
        id_key = '@ID'
        id_val = 'FILE_'+str(i).zfill(4)
        
        mimetype_key = '@MIMETYPE'
        mimetype_val = image['mimetype']
        
        locate_type_key = '@LOCTYPE'
        locate_type_val = 'URL'
        
        href_key = '@{http://www.w3.org/1999/xlink}href'
        href_val = 'file://'+image_path
        
        file_locater_key = '{http://www.loc.gov/METS/}FLocat'
        file_locater_val = {locate_type_key: locate_type_val,
                            href_key: href_val}
        
        file_elem = {id_key: id_val,
                     mimetype_key: mimetype_val,
                     file_locater_key: file_locater_val} 
        
        files.append(file_elem)
        i += 1
    file_sec[file_grp_key][file_key] = files
    return file_sec