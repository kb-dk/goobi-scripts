#!/usr/bin/python
# -*- encoding: utf-8 -*-

from xml.dom import minidom
import pprint
import sys
import os

lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../../')
sys.path.append(lib_path)
from tools.errors import DataError

from tools.xml_tools import dict_tools, xml_tools

from tools.mets import mets_tools

def getAnchorFileData(anchor_file, required_fields):
    '''
    Get the required data from the meta_anchor.xml
    file - raise an error if any required data is missing
    '''
    anchor = minidom.parse(anchor_file)
    metadata = anchor.getElementsByTagName('goobi:metadata')
    data = dict()
    for elem in metadata:
        name = elem.getAttribute('name')
        if name in required_fields:
            data[name] = elem.firstChild.nodeValue
    for item in required_fields:
        if item not in data: 
            raise DataError("{0} missing value {1}".format(anchor_file, item))
    return data

if __name__ == '__main__':
    image_src = '/opt/digiverso/goobi/metadata/201/images/master_orig'
    src = '/opt/digiverso/goobi/metadata/201/meta.xml'
    #src = '/opt/digiverso/goobi/metadata/194/meta - complete data.xml'
    dest = os.path.join(os.path.dirname(src),'meta_new.xml')
    dict_tree,ns  = dict_tools.parseXmlToDict(src)
    
    # Add images - i.e. create phys struct map, file sec and set pathimages
    if not mets_tools.containsImages(dict_tree):
        dict_tree = mets_tools.addImages(dict_tree,image_src) 
    
    content = [{'name': 'Abstract', 'data' : 'From the Roman Empire...' }, 
               {'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
               {'name' : 'Author', 'type' : 'person', 'fields' :
                    [{'tag' : 'displayName', 'data' : 'Turchin, Peter'},
                     {'tag' : 'firstName', 'data' : 'Peter'},
                     {'tag' : 'lastName', 'data' : 'Turchin'}]
                }]
    new_doc_struct = {'content':content,
                      'doc_type':'Article',
                      'start_page':5,
                      'end_page':10}
    new_doc_struct = dict_tools.decodeDictTree(new_doc_struct)
    dict_tree = mets_tools.addNewDocStruct(dict_tree,new_doc_struct)
    
    xml = xml_tools.writeDictTreeToFile(dict_tree,dest)