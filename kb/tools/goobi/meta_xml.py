#!/usr/bin/env python
# -*- coding: utf-8


import xml.dom.minidom

class MetaXml(object):
	'''
	This class contains functions used for working
	with Goobi's meta.xml file
	'''

	@staticmethod
	def generateArticleXml(article_id, article_metadata):
		'''
		Given an id and a dictionary of data, create 
		an XML node in the article format
		Metadata should follow this format:
		[
			{'name': 'Abstract', 'data' : 'From the Roman Empire...' }, 
			{'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
			{'name' : 'Author', 'type' : 'person', 'fields' : [
				{'tag' : 'goobi:firstName', 'data' : 'Peter'},
				{'tag' : 'goobi:lastName', 'data' : 'Turchin'}
			]}
		]
		i.e. an array of dictionaries with each dictionary representing a discrete
		data element. This is transformed into the following XML:
		<goobi:metadata name="Abstract">From the Roman Empire...</goobi:metadata>
		<goobi:metadata name="TitleDocMain">Return of the oppressed</goobi:metadata>
		<goobi:metadata name="Author" type="person">
			<goobi:firstName>Peter</goobi:firstName>
			<goobi:lastName>Turchin</goobi:lastName>
		</goobi:metadata>
		Dictionary tuples are transformed to attributes on the element, except for the 
		data tuple which is transformed into a text node.
		Note the special case of the Author field, which is in fact a parent node containing
		firstName and lastName data fields. If the dictionary contains a 'fields' item, this
		method will attempt to create a hierarchical node structure in the manner shown here.
		'''
		doc = xml.dom.minidom.Document()
	
		articleData = MetaXml.createGoobiMetadata(doc, article_metadata)

		modsExtTag = doc.createElement('mods:extension')
		modsExtTag.appendChild(articleData)

		modsTag = doc.createElement('mods:mods')
		modsTag.setAttributeNS('mods', 'xmlns:mods', 'http://www.loc.gov/mods/v3')
		modsTag.appendChild(modsExtTag)

		dataTag = doc.createElement('mets:xmlData')
		dataTag.appendChild(modsTag)

		mdTag = doc.createElement('mets:mdWrap')
		mdTag.setAttribute('MDTYPE', 'MODS')
		mdTag.appendChild(dataTag)

		dmdTag = doc.createElement('dmd:sec')
		dmdTag.setAttribute('ID', article_id)
		dmdTag.appendChild(mdTag)

		ns = doc.createElementNS('http://www.loc.gov/METS/', 'mets:mets')
		ns.setAttribute('xmlns:mets', 'http://www.loc.gov/METS/')
		ns.appendChild(dmdTag)
		
		doc.appendChild(ns)
		return doc

	@staticmethod
	def createGoobiMetadata(doc, metadata):
		'''
		This method focuses specifically on the goobi:metadata
		fields. See above for a full description of its workings
		'''
		goobiTag = doc.createElement('goobi:goobi')
		goobiTag.setAttributeNS('goobi', 'xmlns:goobi', 'http://meta.goobi.org/v1.5.1/')
		for element_data in metadata:
			metadataTag = MetaXml.createGoobiMetadataTag(doc, element_data)
			goobiTag.appendChild(metadataTag)
		return goobiTag

	@staticmethod
	def createGoobiMetadataTag(doc, element_data):
		'''
		Create tag for a specific element based on a dictionary object e.g. 
		<goobi:metadata name="Abstract">From the Roman Empire...</goobi:metadata>
		Note the special handling of multidimensional nodes such as Author
		discussed above.
		'''
		metadataTag = doc.createElement('goobi:metadata')
		for key,val in element_data.items():
			if key == 'data':
				text = doc.createTextNode(val)
				metadataTag.appendChild(text)
			elif key == 'fields':
				for field in val:
					tag = doc.createElement(field['tag'])
					text = u"{0}".format(field['data'])
					text_tag = doc.createTextNode(text)
					tag.appendChild(text_tag)
					metadataTag.appendChild(tag)
			else:
				metadataTag.setAttribute(key,val)
		return metadataTag