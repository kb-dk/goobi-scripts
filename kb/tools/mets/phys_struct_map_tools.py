#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import os
import pprint

lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../')
sys.path.append(lib_path)

from tools.xml_tools import xml_tools
from tools.mets import fs_tools

def isEmpty(physical_struct_map):
    div_key = '{http://www.loc.gov/METS/}div'
    return (div_key not in physical_struct_map[div_key])

def isValid(physical_struct_map,image_src):
    images = fs_tools.getImages(image_src)
    pages = getPages(physical_struct_map)
    return(len(images) == len(pages))

def createPages(physical_struct_map,start_page,end_page):
    '''
    Checks that the pange range from start_page to end_page exist in  
    physical_struct_map.
    
    Returns a list of PHYS_XXXX-ids that can be added as links in structLink.
    
    :param physical_struct_map: the physical struct map to createPages pages for
    :param start_page: 
    :param end_page:
    '''

    struct_map_pages = getPages(physical_struct_map)
    # Get page range for start to end pages
    pages = range(start_page,end_page+1)
    # Verify that pages are in struct_map_pages
    add_pages = []
    for page in pages:
        if not page in struct_map_pages:
            return []
        else:
            add_pages.append('PHYS_'+str(page).zfill(4))
    return add_pages

def create(physical_struct_map, page_num):
    '''
    
    :param physical_struct_map:
    :param pages: 
    
    An empty physical struct map from Goobi looks like this:
    
    <mets:structMap TYPE="PHYSICAL">
        <mets:div DMDID="DMDPHYS_0000" ID="PHYS_0000" TYPE="BoundBook"/>
    </mets:structMap>
    or as a dict tree:
    {'@TYPE': 'PHYSICAL',
     '{http://www.loc.gov/METS/}div': 
         {'@DMDID': 'DMDPHYS_0000',
          '@ID': 'PHYS_0000',
          '@TYPE': 'BoundBook'}}
                                       
    insertToPhysicalStructMap(physical_struct_map, 2) will result in
    {'@TYPE': 'PHYSICAL',
     '{http://www.loc.gov/METS/}div': 
         {'@DMDID': 'DMDPHYS_0000',
          '@ID': 'PHYS_0000',
          '@TYPE': 'BoundBook'
          '{http://www.loc.gov/METS/}div': 
              [{'@ID': 'PHYS_0001',
                '@ORDER': '1',
                '@ORDERLABEL': 'uncounted',
                '@TYPE': 'page',
                '{http://www.loc.gov/METS/}fptr': {'@FILEID': 'FILE_0000'}},
               {'@ID': 'PHYS_0002',
                '@ORDER': '2',
                '@ORDERLABEL': 'uncounted',
                '@TYPE': 'page',
                '{http://www.loc.gov/METS/}fptr': {'@FILEID': 'FILE_0001'}}
               ]
          }}
    
    
    '''
    div_elem = '{http://www.loc.gov/METS/}div'
    pages = []
    for order in range(1,page_num+1):
        id_key = '@ID'
        id_val = 'PHYS_'+str(order).zfill(4) # file id starts from 1
        
        order_key = '@ORDER'
        order_val = str(order)
        
        orderlabel_key = '@ORDERLABEL'
        orderlabel_val = 'uncounted'
        
        type_key = '@TYPE'
        type_val = 'page'
        
        file_id_key = '@FILEID'
        file_id_val = 'FILE_'+str(order-1).zfill(4) # file id starts from 0
        
        file_pointer_key = '{http://www.loc.gov/METS/}fptr' 
        file_pointer_val = {file_id_key: file_id_val}
        
        page = {id_key: id_val,
                order_key : order_val,
                orderlabel_key: orderlabel_val,
                type_key: type_val,
                file_pointer_key: file_pointer_val
                }
        pages.append(page)
    physical_struct_map[div_elem][div_elem] = pages
    return physical_struct_map

def clear(physical_struct_map):
    '''
    Returns an empty physical_struct_map
    
    {'@TYPE': 'PHYSICAL',
     '{http://www.loc.gov/METS/}div': 
         {'@DMDID': 'DMDPHYS_0000',
          '@ID': 'PHYS_0000',
          '@TYPE': 'BoundBook'}}
    
    :param physical_struct_map:
    '''
    div_elem = '{http://www.loc.gov/METS/}div'
    if div_elem in physical_struct_map[div_elem]:
        physical_struct_map[div_elem].pop(div_elem)
    return physical_struct_map

def getPages(physical_struct_map,details=False):
    '''
    Returns the existing pages from a physical struct map
    
    :param physical_struct_map: the physical struct map as a dict tree
    
    METS (Goobi) has four ways in the metadata file to identify page numbers:
        ID,ORDER,ORDERLABEL and FILEID
        ->ID is used to link between physical pages and dmd section in structLink
        ->ORDER is the index order starting from 1
        ->ORDERLABEL is the logical page label in the book (uncounted, arabic, roman etc)
        ->FILEID links the physical page to file, i.e. one physical page can be covered by one or several files
    '''
    # TODO: insert checks and raise errors
    div_key = '{http://www.loc.gov/METS/}div'
    if not div_key in physical_struct_map[div_key]:
        return []
    if details:
        struct_map_pages =  map(lambda x: x['@ID'],
                                physical_struct_map[div_key][div_key])
    else:
        # Get list of physical pages converted to integers: 'PHYS_0001' -> 1, etc
        struct_map_pages =  map(lambda x: int(x['@ID'].split('_')[-1]),
                                physical_struct_map[div_key][div_key])
    return struct_map_pages

def getSelectedPages(physical_struct_map,selected_pages):
    '''
    Returns a list of (string,string) tuples for a list of 
    IDs extracted from a physical struct map, where first is ORDER and second
    is ORDERLABEL
    
    :param physical_struct_map: the physical struct map as a dict tree
    :param selected_pages: a list of IDs, e.g ['PHYS_0001','PHYS_0002']
    '''
    div_key = '{http://www.loc.gov/METS/}div'
    if not div_key in physical_struct_map[div_key]:
        return []
    if isinstance(physical_struct_map[div_key][div_key],list):
        page_elems = physical_struct_map[div_key][div_key]
    else:
        page_elems = [physical_struct_map[div_key][div_key]]
    pages = [(p['@ORDER'],p['@ORDERLABEL']) for p in page_elems 
             if p['@ID'] in selected_pages]
    return pages

def offsetExists(physical_struct_map):
    '''
    Checks whether offset for pages in mets file is set. This is done by
    checking if "order" and "orderlabel" are different at some point.
    :param physical_struct_map:
    '''
    div_key = '{http://www.loc.gov/METS/}div'
    if not div_key in physical_struct_map[div_key]:
        return []
    for page in physical_struct_map[div_key][div_key]:
        order = int(page['@ORDER']) if ('@ORDER' in page and page['@ORDER'].isdigit()) else None
        orderlabel = int(page['@ORDERLABEL']) if ('@ORDERLABEL' in page and page['@ORDERLABEL'].isdigit()) else None
        if (order and orderlabel) and not order == orderlabel: return True
    return False

def addOffset(physical_struct_map,offset):
    '''
    Returns a physical struct map where all the page numbers has been corrected
    in regards of given offset.
    
    E.g. if page number 1 starts is equal to image number 3, i.e. image 1 and 2 
    are uncounted as front page or other uncounted frontmatter, ORDERLABEL will 
    be set to 1 for page with ORDER = 3. ORDER=4->ORDERLABEL=2 etc. In this 
    case offset will be 2.
    
    :param physical_struct_map:
    :param offset:
    
    Documentation from http://www.loc.gov/standards/mets/mets.xsd (2014-08-28)
    
    ORDERLABEL (string/O): A representation of the div's order among 
    its siblings (e.g., “xii”), or of any non-integer native numbering 
    system. It is presumed that this value will still be machine 
    actionable (e.g., it would support ‘go to page ___’ function), 
    and it should not be used as a replacement/substitute for the 
    LABEL attribute. To understand the differences between ORDER, 
    ORDERLABEL and LABEL, imagine a text with 10 roman numbered 
    pages followed by 10 arabic numbered pages. Page iii would 
    have an ORDER of “3”, an ORDERLABEL of “iii” and a LABEL 
    of “Page iii”, while page 3 would have an ORDER of “13”, 
    an ORDERLABEL of “3” and a LABEL of “Page 3”.
    '''
    
    div_key = '{http://www.loc.gov/METS/}div'
    if not div_key in physical_struct_map[div_key]:
        return []
    for page in physical_struct_map[div_key][div_key]:
        if ('@ORDER' in page and page['@ORDER'].isdigit() and
            int(page['@ORDER']) < offset):
            page['@ORDERLABEL'] = str(int(page['@ORDER']) + offset)
    return physical_struct_map

def get(dict_tree,ns=None):
    '''
    Returns the physical struct map from dict tree
    :param dict_tree:
    :param ns:
    '''
    
    if ns is None:
        ns = '{http://www.loc.gov/METS/}'
    else:
        ns = ns['mets']
    phys_struct_map_dict = xml_tools.getSubTree(dict_tree=dict_tree,
                                                ns=ns,
                                                elem_name='structMap',
                                                elem_attrib_key='TYPE',
                                                elem_attrib_val='PHYSICAL')
    return phys_struct_map_dict



