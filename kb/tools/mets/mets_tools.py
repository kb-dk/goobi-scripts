'''
Created on 19/08/2014

@author: jeel
'''
from xml.dom import minidom
import phys_struct_map_tools
import fs_tools
import file_sec_tools
import log_struct_map_tools
import dmd_sec_tools
import struct_link_tools
import pprint
import sys

#===============================================================================
# Function to a add new doc struct to dict_tree - wrapper
#===============================================================================

def docTypeExists(dict_tree,doc_type):
    return dmd_sec_tools.docTypeExists(dict_tree, doc_type)

def articleExists(dict_tree, title, start_page, end_page):
    '''
    Returns true if an article exists in dict_tree.
    
    The test is done by checking title, start page and end page
    :param dict_tree:
    :param title:
    :param start_page:
    :param end_page:
    '''
    def getPages(ps,i):
        r = []
        t = sorted([int(p[0]) for p in pages if p[0].isdigit()])
        if t: r.append(t[i])
        t = sorted([int(p[1]) for p in pages if p[1].isdigit()])
        if t: r.append(t[i])
        return r
    
    named_articles = dmd_sec_tools.getDmdsWithContent(dict_tree,
                                                      'Article', 
                                                      'TitleDocMain',
                                                      title)
    for a in named_articles:
        #=======================================================================
        # If there are article in dict_tree with same name as the one being 
        # added, compare start and end pages.
        #=======================================================================
        phys_pages = struct_link_tools.getPhysListByLogIds(dict_tree, [a])
        physical_struct_map = phys_struct_map_tools.get(dict_tree)
        pages = phys_struct_map_tools.getSelectedPages(physical_struct_map, phys_pages)
        # pages: a list of (str,str) tuples, where first elem is ORDER and 
        # second elem is ORDERLBEL
        # 1: Find first page in pages (both ORDER and ORDERLABEL) and see if
        # it is equal to start_page.
        # We need to check both because possible offset difference
        start_pages = getPages(pages,0)
        same_start_page = (start_page in start_pages) 
        # 2: Same with end_page
        end_pages = getPages(pages,-1)
        same_end_page = (end_page in end_pages)
        if (same_start_page and same_end_page):
            return True
    return False
    

def addNewDocStruct(dict_tree,doc_struct_info,parrent_attrib=None):
    '''
    Returns a dict tree with a (new) doc struct inserted. 
    
    {'doc_type': 'Article',
     'content':
            [{'name': 'Abstract', 'data' : 'From the Roman Empire...' }, 
             {'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
             {'name' : 'Author', 'type' : 'person', 'fields' :
                 [{'tag' : 'goobi:firstName', 'data' : 'Peter'},
                  {'tag' : 'goobi:lastName', 'data' : 'Turchin'}]
            }],
     'start_page':5,
     'end_page':10'
    }
    
    :param dict_tree: dictionary tree to insert
    :param doc_struct_info: dictionary with the information to add
    '''
    # Get available DMDLOG and LOG in logical struct map
    log_strct_map = log_struct_map_tools.getLogicalStructMap(dict_tree)
    log_id = log_struct_map_tools.getAvailableStructMapLogId(log_strct_map)
    dmd_log_id = log_struct_map_tools.getAvailableStructMapDmdLogId(log_strct_map) 
    # Insert these in logical struct map
    dict_tree = log_struct_map_tools.addSectionToLogicalStructMap(dict_tree=dict_tree,
                                                                  sec_id = log_id,
                                                                  sec_type = doc_struct_info['doc_type'],
                                                                  parent_attrib=parrent_attrib,
                                                                  sec_dmdid=dmd_log_id)
    # Insert the relevant pages linked to LOG in struct link
    if 'start_page' in doc_struct_info: # Only add pages if start_page exist
        dict_tree = struct_link_tools.addStructLinks(dict_tree, log_id, doc_struct_info)
    # Create and insert dmdSec
    dict_tree = dmd_sec_tools.addDmdSec(dict_tree,dmd_log_id,doc_struct_info['content'])
    return dict_tree

#===============================================================================
# Methods to add information about the images in a folder to the dict tree 
#===============================================================================

def containsImages(dict_tree):
    
    empty_file_sec = file_sec_tools.isEmpty(file_sec_tools.get(dict_tree))
    empty_phys_struct_map = phys_struct_map_tools.isEmpty(phys_struct_map_tools.get(dict_tree))
    # Both file_sec_tools and physical struct map must be non empty 
    return (not empty_file_sec and not empty_phys_struct_map)

def addImages(dict_tree,image_src):
    '''
    Returns a dict_tree where all the images from image_src has been inserted
    into the physical struct map and file section
    
    :param dict_tree: dict tree to insert images
    :param image_src: folder in which the images exist
    '''
    dict_tree = dmd_sec_tools.fixPathimagefiles(dict_tree, image_src)
    images = fs_tools.getImages(image_src)
    ## Handle Physical Stuct Map
    # Get physical struct map
    physical_struct_map = phys_struct_map_tools.get(dict_tree)
    # Check the struct map exists
    if physical_struct_map is None:
        raise ValueError('physical_struct_map is missing from dict_tree')
    if (phys_struct_map_tools.isEmpty(physical_struct_map) or
        not phys_struct_map_tools.isValid(physical_struct_map, image_src)):
        # Clear existing physical struct map
        physical_struct_map = phys_struct_map_tools.clear(physical_struct_map)
        # Add pages to empty physical struct map
        physical_struct_map = phys_struct_map_tools.create(physical_struct_map,
                                                     len(images))
    file_section = file_sec_tools.get(dict_tree)
    file_section = file_sec_tools.create(file_section,images)
    dict_tree = file_sec_tools.insert(dict_tree, file_section)
    return dict_tree

def addOffsetToPhysicalStructMap(dict_tree, page_offset):
    if page_offset is not None:
        physical_struct_map = phys_struct_map_tools.get(dict_tree)
        # Check if offset is already set for book and skip if it is
        if phys_struct_map_tools.offsetExists(physical_struct_map): return
        phys_struct_map_tools.addOffset(physical_struct_map, page_offset)

#===============================================================================
# Methods to add pages from children to parent, if parent has no pages
#===============================================================================

def expandPagesFromChildrenToParent(dict_tree):
    div_key = '{http://www.loc.gov/METS/}div'
    logical_struct_map = log_struct_map_tools.getLogicalStructMap(dict_tree)
    temp_dict_tree = addPagesOnLevel(logical_struct_map[div_key], dict_tree)
    if temp_dict_tree: # If temp_dict_tree is None, root already has pages
        return  addAllPagesToRoot(logical_struct_map[div_key], dict_tree)
    return dict_tree

def addAllPagesToRoot(logical_struct_map,dict_tree):
    if isinstance(logical_struct_map, dict):
        root_id = logical_struct_map['@ID']
        physical_struct_map = phys_struct_map_tools.get(dict_tree)
        all_pages = phys_struct_map_tools.getPages(physical_struct_map,details=True)
        # Add all pages (phys_list) to root
        dict_tree = struct_link_tools.addLinks(dict_tree, root_id, all_pages)
        #pprint.pprint(struct_link)
    else:
        err = 'Multiple root detected - not allowed'
        raise ValueError(err)
    return dict_tree

def addPagesOnLevel(logical_struct_map,dict_tree):
    div_key = '{http://www.loc.gov/METS/}div'
    if isinstance(logical_struct_map, dict): # Only one root
        parent_id = logical_struct_map['@ID']
        if struct_link_tools.exists(dict_tree, parent_id):
            # Current element already has pages
            return
        children_ids = log_struct_map_tools.getChildrenLogIds(logical_struct_map)
        if not children_ids: # No children - dammit
            return
        if div_key in logical_struct_map:
            # Recursively handle subtree before adding pages to this element
            addPagesOnLevel(logical_struct_map[div_key],dict_tree)
        phys_list = struct_link_tools.getPhysListByLogIds(dict_tree, children_ids)
        # Add children pages (phys_list) to parent (parent_id)
        dict_tree = struct_link_tools.addLinks(dict_tree, parent_id, phys_list)
        #pprint.pprint(struct_link)
    elif isinstance(logical_struct_map, list): # Multiple branches
        for branch in logical_struct_map:
            addPagesOnLevel(branch,dict_tree)
    return dict_tree

#===============================================================================
# Methods for extracting information from mets file. Used for creating OJS-files
# and splitting pdf-files
#===============================================================================

def getIssueData(data):
    '''
    Get the required data from the meta.xml
    file - raise an error if any required data is missing
    '''
    mets_ns = 'http://www.loc.gov/METS/'
    #=======================================================================
    # Dig in and get DMDID for periodical and periodical volume
    #=======================================================================
    structMap = getElemByNsNameType(data, mets_ns, 'structMap', 'LOGICAL')
    dmd_ids = []
    for div in structMap.getElementsByTagNameNS(mets_ns,'div'):
        struct_map_type = div.getAttribute('TYPE')
        if struct_map_type == 'Periodical' or struct_map_type == 'PeriodicalVolume':
            dmd_ids.append(div.getAttribute('DMDID'))
    #=======================================================================
    # Dig in and get metadata from periodical and periodical volume
    #=======================================================================
    dmd_secs = data.getElementsByTagNameNS(mets_ns,'dmdSec')
    issue_data = dict()
    for dmd_sec in dmd_secs:
        dmd_id = dmd_sec.getAttribute('ID')
        if dmd_id in dmd_ids:
            issue_data.update(getDmdMetadata(dmd_sec,dmd_id))
    return issue_data

def getArticleData(data,sections):
    ret_sections = {s: [] for s in sections}
    mets_ns = 'http://www.loc.gov/METS/'
    #=======================================================================
    # Dig in and get DMDID for elements in sections front matter, articles
    # and back matter 
    #=======================================================================
    structMap = getElemByNsNameType(data, mets_ns, 'structMap', 'LOGICAL')
    section_dmd_ids = {s: [] for s in sections}
    log_ids = dict() # mapping log_id -> dmd_id, for pages
    for div in structMap.getElementsByTagNameNS(mets_ns,'div'):
        section_type = div.getAttribute('TYPE')
        if section_type in sections:
            for sdiv in div.getElementsByTagNameNS(mets_ns,'div'):
                dmd_id = sdiv.getAttribute('DMDID')
                section_dmd_ids[section_type].append(dmd_id)
                log_ids[sdiv.getAttribute('ID')] = dmd_id
    #=======================================================================
    # Dig in and get metadata from articles under sections front matter,
    # articles and back matter
    #=======================================================================
    dmd_secs = data.getElementsByTagNameNS(mets_ns,'dmdSec')
    for dmd_sec in dmd_secs:
        dmd_id = dmd_sec.getAttribute('ID')
        for section_type,dmd_ids in section_dmd_ids.items():
            if dmd_id in dmd_ids:
                ret_sections[section_type].append(getDmdMetadata(dmd_sec,dmd_id))
    #=======================================================================
    # Add start and end page to articles
    #=======================================================================
    pages = getPages(data) # Pages is a dict: log_id->list of pages/order
    for log_id,dmd_id in log_ids.items():
        if log_id in pages:
            temp_pages = map(lambda x: int(x), pages[log_id]) # Convert to integers
            start_page = temp_pages[0]
            end_page = temp_pages[-1]
            ret_sections = addPagesToArticle(dmd_id,start_page,end_page,ret_sections)
    #=======================================================================
    # Sort articles by pages
    #=======================================================================
    for section_type, articles in ret_sections.items():
        ret_sections[section_type] = sorted(articles,
                                            key=lambda k: k['start_page']) 
    return ret_sections
            
def addPagesToArticle(dmd_id, start_page, end_page,section_data):
    for section_type,articles in section_data.items():
        for article in articles:
            if article['dmd_id'] == dmd_id:
                temp_article = article
                temp_article['start_page'] = start_page
                temp_article['end_page'] = end_page
                section_data[section_type].remove(article)
                section_data[section_type].append(temp_article)
                return section_data

def getPages(data):
    '''
    Returns a dictionary with a mapping log_id -> list of order.
    This makes it possible to see which pages are linked to which log_ids
    Log_ids are linked to dmd_ids..
    
    :param data:
    '''
    mets_ns = 'http://www.loc.gov/METS/'
    ret_pages = {}
    phys_pages = getElemByNsNameType(data, mets_ns, 'structMap', 'PHYSICAL')
    phys_pages = phys_pages.getElementsByTagNameNS(mets_ns, 'div')
    pages = dict()
    for phys_page in phys_pages:
        phys_id = phys_page.getAttribute('ID')
        order = phys_page.getAttribute('ORDER')
        pages[phys_id] = order
    links = data.getElementsByTagNameNS(mets_ns, 'smLink')
    xlink_ns = 'http://www.w3.org/1999/xlink'
    for link in links:
        from_log_id = link.getAttributeNS(xlink_ns,'from')
        to_phys_page = link.getAttributeNS(xlink_ns,'to')
        if to_phys_page in pages:
            if from_log_id in ret_pages: # add to list
                ret_pages[from_log_id].append(pages[to_phys_page])
            else: # create new list for log_id
                ret_pages[from_log_id] = [pages[to_phys_page]]
    return ret_pages
    
def getDmdMetadata(dmd_sec,dmd_id):
    metadata = dict()
    goobi_ns = 'http://meta.goobi.org/v1.5.1/'
    for elem in dmd_sec.getElementsByTagNameNS(goobi_ns,'metadata'):
        name = elem.getAttribute('name')
        if name == 'Author':
            firstName = elem.getElementsByTagNameNS(goobi_ns,'firstName')[0].firstChild.nodeValue
            lastName = elem.getElementsByTagNameNS(goobi_ns,'lastName')[0].firstChild.nodeValue
            author = {'firstName':firstName,
                      'lastName':lastName}
            if 'Author' in metadata:
                metadata['Author'].append(author)
            else:
                metadata['Author'] = [author]
        elif elem.firstChild:
            content = elem.firstChild.nodeValue
            if name in metadata:
                if isinstance(metadata[name],list):
                    metadata[name].append(content)
                else:
                    metadata[name] = [metadata[name],content]
            else:
                metadata[name] = content
    if metadata: metadata['dmd_id']= dmd_id # Only add id if data has been added
    return metadata

def getElemByNsNameType(data,ns,name,elem_type):
    '''
    Returns first element in data with ns and name and where attribute
    'TYPE' is equal elem_type
    :param data:
    :param ns:
    :param name:
    :param elem_type:
    '''
    
    elems = data.getElementsByTagNameNS(ns,name)
    for elem in elems:
        if elem.getAttribute('TYPE') == elem_type: return elem

def hasMetadataField(data,metadata_key='TitleDocMainShort'):
    # Get all goobi:metadata for dmd_secs. Metadata is a list of dictionaries 
    metadata = dmd_sec_tools.getAllMetadata(data)
    # Return True if metadata_key is in metadata and has content
    for field in metadata:
        if ('@name' in field and # field has a name
            field['@name'] == metadata_key and # field name is same as metadata_key
            '#text' in field and # there is a content field
            field['#text'] # Has text
            ):
            return True
    return False

def addFieldToDocType(data,doc_type,field_name,field_content):
    '''
    Add field_name with content field_content to a random dmd_sec with doc_type.
    
    NB! This method should be used for dmd sec with the invariant that only one
    may occur.
    
    :param data: a dict tree
    :param doc_type: which kind of dmd_sec to add field to
    :param field_name: name of the field to add
    :param field_content: content of the field to add
    '''
    
    dmdlog_id = log_struct_map_tools.getFirstDmdLogByDocType(data,doc_type)
    if not dmdlog_id:
        err = 'No doc struct with type "{0}" found in mets-file.'
        raise KeyError(err.format(doc_type))
    return dmd_sec_tools.addMetadataToDmdSec(data, dmdlog_id,
                                             field_name,field_content)
