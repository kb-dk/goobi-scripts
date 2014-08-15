#!/usr/bin/python
# -*- encoding: utf-8 -*-

from xml.dom import minidom
import pprint
import sys
import os

lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../../')
sys.path.append(lib_path)
from tools.errors import DataError
from tools.xml_tools import xml_tools

def parseXmlToDict(xml_file):
    '''
    Return a dictionary tree from a file path for a xml-file
    :param xml_file: path to xml_file
    '''
    etree,ns = xml_tools.parse_and_get_ns(xml_file)
    dict_tree = xml_tools.etree_to_dict(etree.getroot())
    return dict_tree,ns

def getLogicalStructMap(dict_tree,ns=None):
    '''
    Returns the logical structMap sub tree
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

def getAttribValuesByName(dict_tree,attribute_key):
    '''
    Returns a list of attribute values within a tree where the attribute key
    = "attribute_key". E.g. all the IDs or DMDIDs within the logical struct
    map
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
            
    
def getAvailableStructMapLogId(log_struct_map):
    '''
    Returns the first available ID in a logical struct map 
    :param log_struct_map:
    '''
    log_ids = sorted(getAttribValuesByName(log_struct_map,'@ID'))
    # The StructMapLogs has the form 'LOG_0001'
    last_log_id = log_ids[-1].split('_')[-1]
    next_log_id = 'LOG_'+str(int(last_log_id)+1).zfill(4)
    return next_log_id

def getAvailableStructMapDmdLogId(log_struct_map):
    '''
    Returns the first available DMDID in a logical struct map 
    :param log_struct_map:
    '''
    log_ids = sorted(getAttribValuesByName(log_struct_map,'@DMDID'))
    # The StructMapLogs has the form 'LOG_0001'
    last_log_id = log_ids[-1].split('_')[-1]
    next_log_id = 'DMDLOG_'+str(int(last_log_id)+1).zfill(4)
    return next_log_id


#===============================================================================
# Functions to create a new physical struct map section
#===============================================================================

def createPhysicalStructMap(dict_tree,image_src):
    '''
    
    :param dict_tree:
    :param image_src:
    '''

    # Various checks

    
    
    # Get phsyical struct map
    physical_struct_map = getPhysicalStructMap(dict_tree)
    # Check the struct map exists
    if physical_struct_map is None:
        raise ValueError('physical_struct_map is missing from dict_tree')
    # Get image file names from image_src
    image_file_names = os.listdir(image_src)
    # Get the pages from physical struct map
    struct_map_pages = getPagesFromPhysicalStructMap(physical_struct_map)
    # Check if struct map contains the correct amount of pages
    if len(image_file_names) == len(struct_map_pages):
        return dict_tree
    # Remove existing physical pages from physical_struct_map
    physical_struct_map = clearPhysicalStruct(physical_struct_map)
    # Add pages to physical struct map
    
    #Insert in dict_tree
    
    return dict_tree
    
def clearPhysicalStruct(physical_struct_map):
    # Clear it
    return physical_struct_map

#===============================================================================
# Functions to add struct links to structLink-section
#===============================================================================

def addStructLinks(dict_tree,link_from,doc_struct_info):
    '''
    :param dict_tree: a dictionary tree with complete goobi metadata
    :param link_from: the logical section to link to, e.g. LOG_0001
    :param doc_struct_info: a dictonary with at least start_page and end_page
    
    :return an updated version of dict_tree with links inserted.
    '''
    # Set variables
    mets_elem = '{http://www.loc.gov/METS/}mets'
    struct_link_elem = '{http://www.loc.gov/METS/}structLink'
    # Check dict_tree
    if mets_elem not in dict_tree:
        err = ('dict_tree must contain {0}'.format(mets_elem))
        raise ValueError(err)
    if struct_link_elem not in dict_tree[mets_elem]:
        err = ('dict_tree must contain {0}'.format(struct_link_elem))
        raise ValueError(err)
    start_page_key = 'start_page'
    end_page_key = 'end_page'
    # Check doc_struct_info
    assert start_page_key in doc_struct_info, \
           'doc_struct_info must contain "{0}"'.format(start_page_key)
    assert end_page_key in doc_struct_info, \
           'doc_struct_info must contain "{0}"'.format(end_page_key)
    
    start_page = doc_struct_info[start_page_key]
    end_page = doc_struct_info[end_page_key]
    physical_struct_map = getPhysicalStructMap(dict_tree)
    pages = createPagesForPhysicalStructMap(physical_struct_map,
                                            start_page,end_page)
    # Insert links
    struct_link = dict_tree[mets_elem][struct_link_elem]
    struct_link = addLinksToStructLink(struct_link, link_from, pages)
    # Update tree
    dict_tree[mets_elem][struct_link_elem] = struct_link
    # Return updated tree
    return dict_tree

def addLinksToStructLink(struct_link,link_from,link_to_list):
    '''
    :param struct_link:
    :param link_from:
    :param link_to_list: a list of physical ids to link to, 
        e.g. ['PHYS_0001','PHYS_0002']
    '''

    sm_link_elem = '{http://www.loc.gov/METS/}smLink'
    # Check tree
    if sm_link_elem not in struct_link:
        err = ('struct_link must contain {0}'.format(sm_link_elem))
        raise ValueError(err)
    # Extract the list of struct links
    struct_link_list = struct_link[sm_link_elem]
    # Insert list of new links to struct link list
    struct_link[sm_link_elem] = addToStructLinkList(struct_link_list,
                                                    link_from,link_to_list)
    # return updated list
    return struct_link

def addToStructLinkList(struct_link_list,link_from,link_to_list):
    '''
    TODO: check variables, check that link doesn't already exist
    {'@{http://www.w3.org/1999/xlink}from': 'LOG_0001','@{http://www.w3.org/1999/xlink}to': 'PHYS_0001'}
    linkFrom = 'LOG_0001'
    linkToList = ['PHYS_0001']
    '''
    xlink = '@{http://www.w3.org/1999/xlink}'
    link_from_elem = '{0}{1}'.format(xlink,'from')
    link_to_elem = '{0}{1}'.format(xlink,'to')
    for linkTo in link_to_list:
        link = {link_from_elem:link_from,link_to_elem:linkTo}
        struct_link_list.append(link)
    return struct_link_list

def getPhysicalStructMap(dict_tree,ns=None):
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

def createPagesForPhysicalStructMap(physical_struct_map,start_page,end_page):
    '''
    Checks that the pange range from start_page to end_page exist in  
    physical_struct_map.
    Returns a list of PHYS_XXXX-ids that can be added as links in structLink.
    '''
    struct_map_pages = getPagesFromPhysicalStructMap(physical_struct_map)
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
    
def getPagesFromPhysicalStructMap(physical_struct_map):
    '''
    METS (Goobi) has four ways in the metadata file to identify page numbers:
        ID,ORDER,ORDERLABEL and FILEID
        ->ID is used to link between physical pages and dmd section in structLink
        ->ORDER is the index order starting from 1
        ->ORDERLABEL is the logical page label in the book (uncounted, arabic, roman etc)
        ->FILEID links the physical page to file, i.e. one physical page can be covered by one or several files
    '''

    div_ns = '{http://www.loc.gov/METS/}div'
    physical_struct_map = physical_struct_map[div_ns][div_ns]
    # Get list of physical pages converted to integers: 'PHYS_0001' -> 1, etc
    struct_map_pages =  map(lambda x: int(x['@ID'].split('_')[-1])
                            ,physical_struct_map) 
    return struct_map_pages
    

#===============================================================================
# Add dmdSection to logical struct map with applied rules for types in hierarki
#===============================================================================

def addSectionToLogicalStructMap(dict_tree, sec_id,sec_type,parent_attrib=None,
                                 sec_dmdid=None):
    ''' Structure of xml:
    <mets:structMap TYPE="LOGICAL">
        <mets:div ID="LOG_0000" TYPE="Periodical">
            <mets:div DMDID="DMDLOG_0000" ID="LOG_0001" TYPE="PeriodicalVolume">
    '''
    # TODO add this to config or even better -> extract from ruleset
    allowed_types = [{'Periodical':[{'PeriodicalVolume':['Cover',
                                                       'TitlePage',
                                                       'TableOfContents',
                                                       'Article']},
                                    'PeriodicalIssue'
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
    log_struct_map = insertByTypeToHierarki(log_struct_map,
                                                  new_elem_type,
                                                  new_elem,std_elem,
                                                  type_hierarki=allowed_types,
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
    
    :param elem:
    :param attrib:
    '''
    return attrib[0] in elem and elem[attrib[0]] == attrib[1]

def inElemsList(elems,attrib):
    '''
    
    :param elems:
    :param attrib:
    '''
    if type(elems) is dict: return inElemDict(elems,attrib)
    elif type(elems) is list:
        for elem in elems:
            if type(elems) is dict: 
                if inElemDict(elem,attrib): return True

def getDictTreeTypesForCurrentLevel(dict_tree):
    '''
    
    :param dict_tree:
    '''
    type_key = '@TYPE'
    types = []
    if type(dict_tree) is dict:
        if type_key in dict_tree: types.append(dict_tree[type_key])
    elif type(dict_tree) is list:
        for elem in dict_tree:
            if type_key in elem: types.append(elem[type_key])
    return types

def getAllowedTypesOnCurrentLevel(tree):
    '''
    Return a list of keys of the top level of "tree"
    
    Tree is a string or a list of strings or a dict.
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
    Returns all the sub trees on first below dict_tree. Can be narrowed down
    by selecting a key to traverse by
    
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
    

def insertByTypeToHierarki(dict_tree,new_elem_type,new_elem,std_elem,
                           type_hierarki,parent_attrib=None,is_root=True):
    '''
    TODO: change to breadth first instead of depth first
    
    Recursive function to traverse a xml-tree presented as a list of
    dictionaries, which contains elements or sub-xml-trees.
    
    parent_atrrib: if used this must be a tuple of an attribe name and value
        which defines under which element the new element must be added.
        
    new_elem: is a dict of attrib name->values
    '''

    types = getAllowedTypesOnCurrentLevel(type_hierarki)
    updated_tree = None
    if new_elem_type in types:
        updated_tree = insertElemToElemTree(dict_tree,new_elem)
    if not updated_tree is None:
        return updated_tree
    if updated_tree is None and dict_tree is None:
        # An element needs a parent element to be added, there do not traverse
        return None
    # Not valid level. Traverse the type type_hierarki
    # Add None as the first element to create new element on level
    sub_elem_trees =[None]# makes it possible to add elem under a branch in elem tree
    sub_elem_trees.extend(getListOfSubTrees(dict_tree,std_elem)) 
    this_type_hierarki_level = getListOfSubTrees(type_hierarki)
    for sub_hierarki in this_type_hierarki_level:
        for sub_elem_tree in sub_elem_trees:
            updated_sub_elem_tree = insertByTypeToHierarki(sub_elem_tree,
                                                           new_elem_type,
                                                           new_elem,std_elem,
                                                           sub_hierarki,
                                                           parent_attrib,
                                                           is_root=False)
            if ((updated_sub_elem_tree is not None) and
                (((parent_attrib is not None) and inElemsList(dict_tree,parent_attrib))
                    # The updated_sub_elem_tree must be placed under an element 
                    # that haves parent_attrib in it.
                or  
                    # No requirement to parent elem -> just place here
                (parent_attrib is None))):
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

#===============================================================================
# Function to a add new doc struct to dict_tree - wrapper
#===============================================================================

def addNewDocStruct(dict_tree,doc_struct_info):
    '''
    Inserts a (new) doc struct into dictionary tree. 
    :param dict_tree: dictionary tree to insert
    :param doc_struct_info: dictionary with the information to add
    :param doc_type: type of the doc struct to add
    
    :return An updated dictionary tree
    '''
    # Get available DMDLOG and LOG in logical struct map
    log_struct_map = getLogicalStructMap(dict_tree)
    log_id = getAvailableStructMapLogId(log_struct_map)
    dmd_log_id = getAvailableStructMapDmdLogId(log_struct_map) 
    # Insert these in logical struct map
    dict_tree = addSectionToLogicalStructMap(dict_tree=dict_tree,
                                             sec_id = log_id,
                                             sec_type = doc_struct_info['doc_type'],
                                             parent_attrib=None,
                                             sec_dmdid=dmd_log_id)
    # Insert the relevant pages linked to LOG in struct link
    
    dict_tree = addStructLinks(dict_tree, log_id, doc_struct_info)
    # Create and insert dmdSec
    dict_tree = addDmdSec(dict_tree,dmd_log_id,doc_struct_info['content'])
    return dict_tree


#===============================================================================
# Functions to add a DmdSec to dict_tree
#===============================================================================


def addDmdSec(dict_tree, dmd_log_id, doc_struct_info):
    '''
    Creates and add a dmd section to dict_tree
    :param dict_tree:
    :param dmd_log_id:
    :param doc_struct_info:
    
    '''
    
    mets_elem = '{http://www.loc.gov/METS/}mets'
    dmdsec_elem = '{http://www.loc.gov/METS/}dmdSec'
    dcr = dmdSecCreator(dmd_log_id = dmd_log_id)
    dcr.addContent(doc_struct_info)
    dcr.createDmdSec()
    dmdsec = dcr.getDmdSec()
    if dmdsec_elem not in dict_tree[mets_elem]:
        dict_tree[mets_elem][dmdsec_elem] = dmdsec
    elif type(dict_tree[mets_elem][dmdsec_elem]) is dict:
        tmp_dmdsec = dict_tree[mets_elem][dmdsec_elem]
        dmdsec_list = [tmp_dmdsec,dmdsec]
        dict_tree[mets_elem][dmdsec_elem] = dmdsec_list
    elif type(dict_tree[mets_elem][dmdsec_elem]) is list:
        dict_tree[mets_elem][dmdsec_elem].append(dmdsec)
    return dict_tree

class dmdSecCreator(object):
    '''
    {'{http://meta.goobi.org/v1.5.1/}metadata': [{'#text': 'da',
                                              '@name': 'DocLanguage'},
                                             {'#text': u'K\xf8benhavnske maleres \xf8genavne',
                                              '@name': 'TitleDocMain'},
                                             {'@name': 'Author',
                                              '@type': 'person',
                                              '{http://meta.goobi.org/v1.5.1/}displayName': 'Olsen, Ole',
                                              '{http://meta.goobi.org/v1.5.1/}firstName': 'Ole',
                                              '{http://meta.goobi.org/v1.5.1/}lastName': 'Olsen'},
                                             {'@name': 'Author',
                                              '@type': 'person',
                                              '{http://meta.goobi.org/v1.5.1/}displayName': 'Hansen, Emanuel',
                                              '{http://meta.goobi.org/v1.5.1/}firstName': 'Emanuel',
                                              '{http://meta.goobi.org/v1.5.1/}lastName': 'Hansen'},
                                             {'@name': 'Author',
                                              '@type': 'person',
                                              '{http://meta.goobi.org/v1.5.1/}displayName': 'Novrup, Svend',
                                              '{http://meta.goobi.org/v1.5.1/}firstName': 'Svend',
                                              '{http://meta.goobi.org/v1.5.1/}lastName': 'Novrup'}]}
    
    '''
    
    def __init__(self,
                 dmd_log_id,
                 mods_ns = '{http://www.loc.gov/mods/v3}',
                 mets_ns = '{http://www.loc.gov/METS/}',
                 goobi_ns = '{http://meta.goobi.org/v1.5.1/}'
                 ):
        '''
        
        :param dmd_log_id:
        :param mods_ns:
        :param mets_ns:
        :param goobi_ns:
        '''
        self.dmd_log_id = dmd_log_id
        self.mods_ns = mods_ns
        self.mets_ns = mets_ns
        self.goobi_ns = goobi_ns
        self.metadata_key = goobi_ns+'metadata'
        self.dmd_sec = {} # Wrapper for metadata
        self.goobi_attr = {} # Place all the metadata here
    
    def createDmdSec(self):
        '''
        :return a DmdSec ready to be inserted into dictionary tree
        '''
        # Insert into standard, hard coded tree
        extension_attr =    {self.goobi_ns+'goobi': self.goobi_attr}
        mods_attr =         {self.mods_ns+'extension':extension_attr}
        xml_data_attr =     {self.mods_ns+'mods': mods_attr}
        md_wrap_attr =      {'@MDTYPE':'MODS',
                             self.mets_ns+'xmlData': xml_data_attr}
        dmd_sec_attr =      {'@ID':self.dmd_log_id,
                             self.mets_ns+'mdWrap':md_wrap_attr}
        #self.dmd_sec[self.mets_ns+'dmdSec'] = dmd_sec_attr
        self.dmd_sec = dmd_sec_attr
        
    def addContent(self,content):
        '''
        content = dict -> attr_name:attr_content
            : attr_content->dict(attr_key,attr_val)
                : attr_val => string
                : attr_val => list of (elem_name,string)
         {content:{'DogLanguage':{'#text':'da'},
             'TitleDocMain':{'#text':'text'},
             'Author': {'type':'person',
                        'content':{'displayName':'lastname,firstname',
                                   'lastName':'lastname',
                                   'firstName':'firstname'
                                   }
                        }
             }
        }
        '''
        assert type(content) is dict,'content must be a dictionary'
        elements = []
        for key,val in content.items():
            element = {'@name': key}
            assert type(val) is dict,'content-dictionary must contain a dictionary'
            for e_key,e_val in val.items():
                if isinstance(e_val,basestring):
                    if e_key == '#text':
                        element[e_key] = e_val
                    else:
                        element['@'+e_key] = e_val
                elif type(e_val) is dict:
                    for sub_elem_name,sub_elem_val in e_val.items():
                        element[self.goobi_ns+sub_elem_name] = sub_elem_val
                else:
                    raise ValueError('content->dict->dict must be key->str or dict')
            elements.append(element)
        self.goobi_attr[self.metadata_key] = elements

    def getDmdSec(self):
        return self.dmd_sec


        
#===============================================================================
# MISC FUNCTIONS
#===============================================================================

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
                    print value
                    print type(value)
                    raise e
            elif isinstance(value,dict):
                dict_tree[key] = decodeDictTree(dict_tree[key],encoding)
    return dict_tree

if __name__ == '__main__':
    src = sys.argv[1]
    word = sys.argv[2]
    dest = os.path.join(os.path.dirname(src),'meta_new.xml')
    dest = '/opt/digiverso/goobi/metadata/194/meta.xml'
    content = {'DocLanguage':{'#text':'da'},
               'TitleDocMain':{'#text':word},
               'Author': {'type':'person',
                          'content':{'displayName':'lastname,firstname',
                                     'lastName':'lastname',
                                     'firstName':'firstname'
                                     }
                          }
               }
    new_doc_struct = {'content':content,
                      'doc_type':'Article',
                      'start_page':140,
                      'end_page':160}
    new_doc_struct = decodeDictTree(new_doc_struct)
    dict_tree,ns  = parseXmlToDict(src)
    dict_tree = addNewDocStruct(dict_tree=dict_tree,
                                doc_struct_info = new_doc_struct)
    xml = xml_tools.writeDictTreeToFile(dict_tree,dest)