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
	'''

	danmarcMappings = {
		'title' : {'field' : '245', 'subfields' : ['a', 'b']},
		'pages' : {'field' : '300', 'subfields' : ['a'] },
		'author_given_name' : {'field' : '100', 'subfields' : ['h']},
		'author_family_name' : {'field' : '100', 'subfields' : ['a']},
		'other_authors' : {'multiple' : True, 'data': {
			'given_name' : {'field' : '700', 'subfields' : ['h'] }, 
			'family_name' : {'field' : '700', 'subfields' : ['a'] }
		}}
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
		for k,v in self.data.iteritems():
			print u"{0}: {1}".format(k,v)

	def __mapData(self):
		'''
		Given a mappings dictionary (e.g. danmarcMappings)
		create a data dictionary based on the keys in the mappings 
		dictionary and the relevant values in the MARC file
		'''
		dataFields = self.__getDataFields(self.dom) 
		for key, val in self.danmarcMappings.iteritems():
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
			for key, val in subelements.iteritems():
				if field.getAttribute('tag') == val['field']:
					content = ""
					for subfield in val['subfields']:
						content += self.__getSubFieldData(field, subfield) + " "
					data_values[key] = content.strip()
			if len(data_values) > 0: 
				self.data[name].append(data_values) 

	def __handleSingleValuedAttribute(self, key, val, dataFields):
		field_num = val['field']
		subfields = val['subfields'] 
		for field in dataFields:
			if field.getAttribute('tag') == field_num:
				content = ""
				for subfield in subfields:
					subfield_data = self.__getSubFieldData(field, subfield)
					if subfield_data: content += subfield_data + " "
				self.data[key] = content.strip()
				break


	def __getDataFields(self, dom):
		return dom.getElementsByTagName('marcx:datafield')

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


