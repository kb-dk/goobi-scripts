#!/usr/bin/env python
'''
Created on 19/08/2014

@author: jeel
'''
import sys
import os
import pprint

from tools.mets import log_struct_map_tools, struct_link_tools
lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+os.sep+'../')
sys.path.append(lib_path)

from tools.xml_tools import xml_tools

def addDmdSec(dict_tree, dmd_log_id, doc_struct_info):
    '''
    Returns a dict tree with  a dmd section added.
    
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
    Contains methods to create a dmd section.
    
    {'{http://meta.goobi.org/v1.5.1/}metadata': 
        [
            {'#text': 'da',
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
              '{http://meta.goobi.org/v1.5.1/}lastName': 'Novrup'}
        ]
    }

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
        self.dmd_sec_content = {} # Place all the metadata here
    
    def createDmdSec(self):
        '''
        Inserts content for a created dmd sec to the correct hierarchy.
        '''
        '''
        :return a DmdSec ready to be inserted into dictionary tree
        '''
        # Insert into standard, hard coded tree
        extension_attr =    {self.goobi_ns+'goobi': self.dmd_sec_content}
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
        
        :param content: has the following form
        list->dict of (string->string) or (string->list->dict->(string->string))
        
        [{'name': 'Abstract', 'data' : 'From the Roman Empire...' }, 
         {'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
         {'name' : 'Author', 'type' : 'person', 'fields' :
             [{'tag' : 'firstName', 'data' : 'Peter'},
              {'tag' : 'firstName', 'data' : 'Peter'},
              {'tag' : 'lastName', 'data' : 'Turchin'}]
         }
        ]
        
        '''
        assert type(content) is list,'content must be a list'
        elements = []
        for data in content:
            assert isinstance(data, dict), 'Data within content must be a dictionary'
            element = {}
            for key,val in data.items():
                if key == 'name':
                    element['@name'] = val
                elif key == 'data':
                    element['#text'] = val
                elif key == 'type':
                    element['@type'] = val
                elif key == 'fields':
                    assert isinstance(val, list), 'Content within "fields" in content must be a list.'
                    for field in val:
                        assert isinstance(field, dict), 'The element in a field list within content must be dictionaries.'
                        field_key = field['tag']
                        field_val = field['data']
                        element[self.goobi_ns+field_key] = field_val
                else:
                    err = ('The key {0} with value {1} is not accepted for '
                           'items in metadata content when creating sections '
                           'for mets metadata xml file.')
                    err = err.format(key,val)
            elements.append(element)
        self.dmd_sec_content[self.metadata_key] = elements

    def getDmdSec(self):
        '''
        Returns dmd sec
        '''
        return self.dmd_sec


def getDmdsWithContent(dict_tree, doc_type, metadata_key, content):
    '''
    Get a list of logical IDs (LOG_NNNN) for dmd_secs with TYPE = doc_type and 
    metadata_key = content.
    E.g. a list of all articles where 'TitleDocMain' = content
    :param dict_tree:
    :param doc_type: type of dmd_sec to look in, e.g. 'Article'
    :param metadata_key: metadata key to look in, e.g. 'TitleDocMain'
    :param content: metadata content to check for, e.g. the name of the article
    '''
    ns = '{http://www.loc.gov/METS/}'
    mets = dict_tree[ns+'mets'] if ns+'mets' in dict_tree else {} 
    elem_name = 'div'
    elem_attrib_key = 'TYPE'
    elem_attrib_val = doc_type
    log_struct_maps = xml_tools.getAllSubTrees(mets,
                                               ns,
                                               elem_name,
                                               elem_attrib_key,
                                               elem_attrib_val)
    dmd_sec_ids = dict([(x['@DMDID'],x['@ID']) for x in log_struct_maps if '@DMDID' in x])
    goobi_ns = '{http://meta.goobi.org/v1.5.1/}'
    # Take list of dmd_secs
    dmd_secs = mets[ns+'dmdSec'] if ns+'dmdSec' in mets else []
    named_dmd_secs = []
    for dmd_sec in dmd_secs:
        if '@ID' in dmd_sec and dmd_sec['@ID'] in dmd_sec_ids:
            # This is an article
            dmd_sec_metadata = xml_tools.getAllSubTrees(dmd_sec,goobi_ns,
                                                        'dmdSec','name',
                                                        metadata_key)
            if [a for a in dmd_sec_metadata
                if '#text' in a and a['#text'] == content]:
                # This dmd_sec is a article and has the name "metadata_key"
                # Get LOG-id for dmd, as this is used outsude 
                named_dmd_secs.append(dmd_sec_ids[dmd_sec['@ID']])
                #return True # The article has the title 'article_title'
    return named_dmd_secs
    

def docTypeExists(dict_tree,doc_type):
    log_struct_map = log_struct_map_tools.getLogicalStructMap(dict_tree)
    ns = '{http://www.loc.gov/METS/}'
    elem_name = 'div'
    elem_attrib_key = 'TYPE'
    elem_attrib_val = doc_type
    dmd_sec = xml_tools.getAllSubTrees(log_struct_map,
                                       ns,
                                       elem_name,
                                       elem_attrib_key,
                                       elem_attrib_val)
    #pprint.pprint(dmd_sec)
    return len(dmd_sec) > 0

def fixPathimagefiles(dict_tree,path):
    '''
    Digs into the nested section with the dmd sections where the path to images
    are stored and overwrites this with "path"
    :param dict_tree:
    :param path:
    '''
    path_link = 'file://{0}'.format(path)

    mets_ns = '{http://www.loc.gov/METS/}'
    mods_ns = '{http://www.loc.gov/mods/v3}'
    goobi_ns = '{http://meta.goobi.org/v1.5.1/}'
    
    mets_key = '{0}mets'.format(mets_ns)
    
    dmd_sec_key = '{0}dmdSec'.format(mets_ns)
    dmd_sec_id_key = '@ID'
    dmd_sec_id_val = 'DMDPHYS_0000'
    
    md_wrap_key = '{0}mdWrap'.format(mets_ns)
    xml_data_key = '{0}xmlData'.format(mets_ns)
    mods_key = '{0}mods'.format(mods_ns)
    extension_key = '{0}extension'.format(mods_ns)
    goobi_key = '{0}goobi'.format(goobi_ns)
    metadata_key = '{0}metadata'.format(goobi_ns)
    path_key = '#text'
    
    if dmd_sec_key not in dict_tree[mets_key]:
        err = 'Path to images section ({0}) could not be found in mets-file.'
        err = err.format(dmd_sec_key)
        raise KeyError(err)
    dmd_secs = dict_tree[mets_key][dmd_sec_key]
    if isinstance(dmd_secs,dict):
        try:
            dict_tree[mets_key][dmd_sec_key][md_wrap_key][xml_data_key]\
            [mods_key][extension_key][goobi_key][metadata_key][path_key]\
             = path_link
        except (IndexError,KeyError):
            err = ('Path to "{0}" could not be found within the '
                   'DMD-sections in mets-file.')
            err = err.format('pathimagefiles')
            raise KeyError(err)
    elif isinstance(dmd_secs,list):
        path_inserted = False
        for sec_nr in range(len(dmd_secs)):
            if ((dmd_sec_id_key in dmd_secs[sec_nr]) and 
                dmd_secs[sec_nr][dmd_sec_id_key] == dmd_sec_id_val):
                    try:
                        # Killer path
                        dict_tree[mets_key][dmd_sec_key][sec_nr][md_wrap_key]\
                        [xml_data_key][mods_key][extension_key][goobi_key]\
                        [metadata_key][path_key] = path_link
                        path_inserted = True
                        break
                    except (IndexError,KeyError):
                        err = ('Path to "{0}" could not be found within the '
                               'DMD-sections in mets-file.')
                        err = err.format('pathimagefiles')
                        raise KeyError(err)
        if not path_inserted:
            err = '{0} could not be found within the DMD-sections in mets-file'
            err = err.format(dmd_sec_id_val)
            raise KeyError(err)
    return dict_tree

def getAll(data):
    '''
    Returns all dmd_secs in data
    '''
    mets_ns = '{http://www.loc.gov/METS/}'
    mets_key = 'mets'
    dmd_sec_key = 'dmdSec'
    dmd_secs = []
    if mets_ns+dmd_sec_key in data[mets_ns+mets_key]:
        dmd_secs = data[mets_ns+mets_key][mets_ns+dmd_sec_key]
    return dmd_secs

def getMetadata(dmd_secs):
    '''
    Returns all the metadata from dmd_secs from a list of dmd_secs. If a 
    metadata field exist more than once, only one will be outputted
    :param dmd_secs: a list of dmd_secs
    '''
    metadata = []
    goobi_ns = '{http://meta.goobi.org/v1.5.1/}'
    metadata_key = 'metadata'
    for dmd_sec in dmd_secs:
        temp_metadata = xml_tools.getAllSubTrees(dmd_sec,
                                                 goobi_ns,
                                                 metadata_key)
        if temp_metadata and isinstance(temp_metadata[0],list):
            if len(temp_metadata) > 1: raise ValueError('To many metadata lists')
            metadata.extend(temp_metadata[0])
        else: metadata.extend(temp_metadata)
    return metadata

def getAllMetadata(data):
    '''
    Returns all metadata fields from data
    :param data:
    '''
    return getMetadata(getAll(data))

def addMetadataToDmdSec(data, dmdlog_id, field_name, field_content):
    '''
    Adds the field "field_name" with text "field_content" to the dmd_sec with
    id "dmdlog_id".
    
    Note this method is very error prone. Most data is assumed valid.
    :param data:
    :param dmdlog_id:
    :param field_name:
    :param field_content:
    '''
    mets_ns = '{http://www.loc.gov/METS/}'
    mods_ns = '{http://www.loc.gov/mods/v3}'
    goobi_ns = '{http://meta.goobi.org/v1.5.1/}'
    mets_elem = mets_ns+'mets'
    dmdsec_elem = mets_ns+'dmdSec'
    md_wrap_elem = mets_ns+'mdWrap'
    xml_data_elem = mets_ns+'xmlData'
    mods_elem = mods_ns+'mods'
    extension_elem = mods_ns+'extension'
    goobi_elem = goobi_ns+'goobi'
    metadata_elem = goobi_ns+'metadata'
    
    dmdlog_id_key = '@ID'
    dmd_secs = data[mets_elem][dmdsec_elem]
    assert isinstance(dmd_secs,list), 'METS file must contain several dmdSecs'
    dmd_sec = None
    for t_dmd_sec in dmd_secs: # Find the correct dmd_sec
        if not t_dmd_sec[dmdlog_id_key] == dmdlog_id: continue 
        dmd_sec = t_dmd_sec
        break
    # Correct element - dig in and get list
    try:
        metadata = dmd_sec[md_wrap_elem][xml_data_elem][mods_elem][extension_elem][goobi_elem][metadata_elem]
    except KeyError as e:
        raise e
    for field in metadata:
        if field['@name'] == field_name: return True # Field already exists - return True as if it was inserted
    # field does not exist in metadata
    # Remove element and add one with field added
    dmd_secs.remove(dmd_sec)
    field = dict()
    field['@name'] = field_name
    field['#text'] = field_content
    metadata.append(field)
    dmd_sec[md_wrap_elem][xml_data_elem][mods_elem][extension_elem][goobi_elem][metadata_elem] = metadata
    dmd_secs.append(dmd_sec)
    data[mets_elem][dmdsec_elem] = dmd_secs
    return True

