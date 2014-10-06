import urllib2
from xml.dom import minidom
from types import MethodType

class MarcXml(object):
    '''
    This class is responsible for handling of MarcXML files.
    It initialises via static methods to enable initialisation 
    from different sources (path, string, file etc.)
    It then uses the mappings dictionary given to create a data 
    dictionary where the keys are the field names and the values
    are the relevant data from the parsed MARC record.
    E.g. based on a mapping 'given_name' : {'field' : '700', 'subfields' : ['h'] } 
    it will create a  dictionary with the values {'given_name': 'Anders'} where 'Anders'
    is  the value of the 700h field in the record. 
    
    See e.g. http://www.kat-format.dk/danMARC2/felter03.htm
    
    http://www.loc.gov/marc/marc2dc.html
    
    '''

    danmarcMappings = {
        'title' : {'field' : '245', 'subfields' : ['a', 'b']},
        'update_time' : {'field' : '001', 'subfields' : ['c']},
        'pages' : {'field' : '300', 'subfields' : ['a'] },
        'author_given_name'  : {'field' : '100', 'subfields' : ['h']},
        'author_family_name' : {'field' : '100', 'subfields' : ['a']},
        'other_authors' : {'multiple' : True, 'data': {
            'given_name'  : {'field' : '700', 'subfields' : ['h'] }, 
            'family_name' : {'field' : '700', 'subfields' : ['a'] }}},
        'subjects' : {'multiple' : True, 'data': {
            'subject' : [{'field' : '630', 'subfields' : ['f']},
                         {'field' : '930', 'subfields' : ['f']},
                         {'field' : '930', 'subfields' : ['w']},
                         {'field' : '666', 'subfields' : ['f']},
                         {'field' : '631', 'subfields' : ['f']},
                         {'field' : '645', 'subfields' : ['a']},
                         {'field' : '645', 'subfields' : ['b']},
                         {'field' : '645', 'subfields' : ['c']},
                         {'field' : '652', 'subfields' : ['h','a']},
                         {'field' : '086', 'subfields' : ['a']},
                        ]}},
        'language' : {'field' : '008', 'subfields' : ['l'] },
        'description' : {'field' : '504', 'subfields' : ['a'] },
        'sub_title' : {'field' : '245', 'subfields' : ['c']},
        'issn' : {'field' : '557', 'subfields' : ['z']},
    }
    data = {} 

    @staticmethod
    def initFromWeb(url):
        '''
        Given a web address, initialise a class instance
        based on the content at this address
        '''
        content = urllib2.urlopen(url).read()
        return MarcXml(content)

    @staticmethod
    def initFromFile(path):
        '''
        Given a file path, initialise a class instance
        based on the file content
        '''
        data = ""
        with open(path, 'r') as myfile:
            data = myfile.read()
        return MarcXml(data)

    def __init__(self,content):
        '''
        Given a string representing content, initialise
        a class instance with relevant variables, accessors etc.
        Generally this method should not be called directly, but instead
        via a static method such as initFromWeb
        '''
        self.dom = minidom.parseString(content)
        self.__mapData()
        

    def prettyPrint(self):
        for k,v in self.data.items():
            print(u"{0}: {1}".format(k,v))

    def __mapData(self):
        '''
        Given a mappings dictionary (e.g. danmarcMappings)
        create a data dictionary based on the keys in the mappings 
        dictionary and the relevant values in the MARC file
        '''
        dataFields = self.__getDataFields(self.dom) 
        for key, val in self.danmarcMappings.items():
            if 'multiple' in val.keys() and val['multiple']: 
                self.__handleMultiValuedAttribute(key, val['data'], dataFields)
            else:
                self.__handleSingleValuedAttribute(key, val, dataFields)


    def __handleMultiValuedAttribute(self, name, subelements, dataFields):
        '''
        Given the set of datafields and a set of elements describing a 
        multivalued attribute, search through the datafields for matching
        data and add it to our data dictionary.
        '''
        self.data[name] = []
        for field in dataFields:
            data_values = dict()
            # run through the submappings within the element
            for key, val in subelements.items():
                if isinstance(val, list):
                    for sub_val in val:# val is a list of dicts
                        # This makes it possible to add several subelements with
                        # the same 'key' to 'name', e.g. subjects from different
                        # fields in marcx 
                        content = self.__getContent(field, sub_val['field'], sub_val['subfields'])
                        if content: self.data[name].append({key: content})
                else: # val is a dict
                    content = self.__getContent(field, val['field'], val['subfields'])
                    if content: data_values[key] = content
            if len(data_values) > 0: 
                self.data[name].append(data_values) 

    def __handleSingleValuedAttribute(self, key, val, dataFields):
        field_num = val['field']
        subfields = val['subfields'] 
        for field in dataFields:
            content = self.__getContent(field, field_num, subfields)
            if content: 
                self.data[key] = content
                break

    def __getDataFields(self, dom):
        return dom.getElementsByTagName('marcx:datafield')

    def __getContent(self,field,field_num,subfields):
        content = ""
        if field.getAttribute('tag') == field_num:
            for subfield in subfields:
                subfield_data = self.__getSubFieldData(field, subfield)
                if subfield_data: content += subfield_data + " "
        return content.strip()

    def __getSubFieldData(self, node, subfield_code):
        '''
        Given a field and subfield code, this method iterates over the childNodes
        until it finds a text node with the correct subfield code
        '''
        subfields = node.getElementsByTagName('marcx:subfield')
        for field in subfields:
            if field.getAttribute('code') == subfield_code:
                for node in field.childNodes:
                    if node.nodeType == node.TEXT_NODE:
                        return node.data

