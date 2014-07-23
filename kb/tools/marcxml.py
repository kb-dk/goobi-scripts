import urllib2
from xml.dom import minidom

class marcXml(object):
	'''
	This class is responsible for handling of MarcXML files.
	Given a string containing a MARC XML record, it converts to
	a sensible format and presents accessor methods for useful attributes
	We access the initialiser through static methods to enable initialisation 
	from different sources (path, string, file etc.)
	'''
	danmarcMappings = {
		'given_name': '700h',
		'family_name': '700a'
	} 

	@staticmethod
	def initFromWeb(url):
		'''
		Given a web address, initialise a class instance
		based on the content at this address
		'''
		content = urllib2.urlopen(url).read()
		return marcXml(content)
		

	def __init__(self,content):
		'''
		Given a string representing content, initialise
		a class instance with relevant variables, accessors etc.
		Generally this method should not be called directly, but instead
		via a static method such as initFromWeb
		'''
		self.dom = minidom.parseString(content)
		#print self.dom.toprettyxml()
		self.__mapData()

	def __mapData(self):
		'''
		Given a mappings dictionary (e.g. danmarcMappings)
		create a data dictionary based on the keys in the mappings 
		dictionary and the relevant values in the MARC file
		'''
		dataFields = self.__getDataFields(self.dom) 
		for key, val in self.danmarcMappings.iteritems():
			field_num = val[0:3]
			subfield = val[3] 
			for field in dataFields:
				if field.getAttribute('tag') == field_num:
					print self.__getSubFieldData(field, subfield)
					break

	def __getDataFields(self, dom):
		return dom.getElementsByTagName('marcx:datafield')

	def __getSubFieldData(self, node, subfield_code):
		subfields = node.getElementsByTagName('marcx:subfield')
		for field in subfields:
			if field.getAttribute('code') == subfield_code:
				for node in field.childNodes:
					if node.nodeType == node.TEXT_NODE:
						return node.data


