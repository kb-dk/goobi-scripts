#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
from xml.dom import minidom
from errors import DataError

from tools import tools
import os, time

class CreateOJSXML( Step ):

	def setup(self):
		self.name = 'Create OJS XML'
		self.config_main_section = 'ojs_xml'
		self.essential_config_sections = set( ['ojs_xml', 'process_folder_structure', 'process_files'] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_title' : 'string',
			'process_path' : 'folder'
		}

	def step(self):
		try:
			self.getVariables()
			self.createXML()
		except (DataError, IOError) as e:
			self.error_message(e.strerror)
		return None

	def getVariables(self):
		'''
		Ensure we have the variables necessary to execute the script
		Tools will throw an Exception otherwise
		'''
		# we need the path to the xml and the toc
		# TODO: This data shouldn't live in the ojs_xml config section
		# it's being saved here while we're waiting on better config 
		# get methods
		process_path = self.command_line.process_path
		anchor_name = self.getConfigItem('metadata_goobi_anchor_file')
		self.anchor_file = os.path.join(process_path, anchor_name)
		toc_path = self.getConfigItem('toc_path')
		abs_toc_path = os.path.join(process_path, toc_path)
		toc_name = tools.getFirstFileWithExtension(abs_toc_path, '.toc')
		self.toc_file = os.path.join(abs_toc_path, toc_name)
		tools.ensureFilesExist(self.anchor_file, self.toc_file)

		# we also need the required anchor fields
		fields = self.getConfigItem('anchor_required_fields')
		self.anchor_required_fields = fields.split(';')

	def createXML(self):
		'''
		Get the data from the anchor file and the toc
		Use this to construct the OJS XML
		'''
		anchor_data = self.getAnchorFileData()
		toc_data = tools.parseToc(self.toc_file)
		impl = minidom.getDOMImplementation()
		doc = impl.createDocument(None, "issue", None)
		doc = self.createHeadMaterial(doc, anchor_data)
		section = self.createSectionXML(doc, anchor_data)
		date_published = "{0}-01-01".format(anchor_data['PublicationYear'])
				
		for article in toc_data:
			article_xml = self.createArticleXML(doc, article, date_published)
			section.appendChild(article_xml) 
	
		doc.documentElement.appendChild(section)

		print doc.toprettyxml()

	def createSectionXML(self, doc, anchor_data):
		section = doc.createElement('section')
		section_title = "{0} {1} - {2}".format(anchor_data['TitleDocMainShort'], \
			anchor_data['PublicationYear'], anchor_data['Volume'])
		section_title_tag = self.createXMLTextTag(doc, 'title', section_title)
		abbrev_tag = self.createXMLTextTag(doc, 'abbrev', 'ART')
		locale = tools.convertLangToLocale(anchor_data['DocLanguage'])
		abbrev_tag.setAttribute('locale', locale)
		section.appendChild(section_title_tag)
		section.appendChild(abbrev_tag)
		
		return section

		

	def createArticleXML(self, doc, article, date_published):
		'''
		Given an article dict, create the OJS XML
		corresponding to this data
		'''
		article_tag = doc.createElement('article')
		title_tag = self.createXMLTextTag(doc, 'title', article['title'])
		pages_tag = self.createXMLTextTag(doc, 'pages', article['page']) # TODO fix this to use range
		published_tag = self.createXMLTextTag(doc, 'date_published', date_published) 
		author_tag = self.createAuthorXML(doc, article['author'])
		

		article_tag.appendChild(title_tag)
		article_tag.appendChild(pages_tag)
		article_tag.appendChild(author_tag)

		return article_tag

	def createAuthorXML(self, doc, name_str):
		''' 
		Create OJS Author tag based on name string
		Firstname is first word in string
		Lastname is last word in string 
		Middlename is anything in between or CDATA
		'''

		author_tag = doc.createElement('author')
		name = name_str.split(' ')
	
		firstname_tag = self.createXMLTextTag(doc, 'firstname', name[0])
		lastname_tag = self.createXMLTextTag(doc, 'lastname', name[-1])
		
		if len(name[1:-1]) > 0:
			middlename = ' '.join(name[1:-1])
		else:
			middlename = '<![CDATA[ ]]>'
		
		middlename_tag = self.createXMLTextTag(doc, 'middlename', middlename)
		email_tag = self.createXMLTextTag(doc, 'email', '<![CDATA[ ]]>')

		author_tag.appendChild(firstname_tag)
		author_tag.appendChild(middlename_tag)
		author_tag.appendChild(lastname_tag)
		author_tag.appendChild(email_tag)

		return author_tag


	def createHeadMaterial(self, doc, anchor_data):
		'''
		Create and append all the OJS XML Header data
		to XML Document doc based on the data in anchor_data
		'''
		top = doc.documentElement

		top.setAttribute('current', 'false')
		top.setAttribute('published', 'true')
		title_tag = self.createXMLTextTag(doc, 'title', anchor_data['TitleDocMainShort'])
		year_tag = self.createXMLTextTag(doc, 'year', anchor_data['PublicationYear'])
		volume_tag = self.createXMLTextTag(doc, 'volume', anchor_data['Volume'])
		access_tag = self.createXMLTextTag(doc, 'access_date', time.strftime("%Y-%m-%d"))
		
		# we just say that it's the first of the year - we don't know the real date
		date_published = "{0}-01-01".format(anchor_data['PublicationYear'])
		date_tag = self.createXMLTextTag(doc, 'date_published', date_published)

		top.appendChild(title_tag)
		top.appendChild(year_tag)
		top.appendChild(volume_tag)
		top.appendChild(access_tag)
		top.appendChild(date_tag)



		return doc


	def createXMLTextTag(self, doc, tag_name, tag_val):
		'''
		Convenience function to return xml text tag
		with simple form <tag_name>tag_val</tag_name>
		Note - this function does not append the tag to your
		doc - you will need to this this with Element.appendChild(tag) 
		'''
		tag = doc.createElement(tag_name)
		text = doc.createTextNode(tag_val)
		tag.appendChild(text)
		return tag


	def getAnchorFileData(self):
		'''
		Get the required data from the meta_anchor.xml
		file - raise an error if any required data is missing
		'''
		anchor = minidom.parse(self.anchor_file)
		metadata = anchor.getElementsByTagName('goobi:metadata')
		data = dict()
		for elem in metadata:
			name = elem.getAttribute('name')
			if name in self.anchor_required_fields:
				data[name] = elem.firstChild.nodeValue
		
		for item in self.anchor_required_fields:
			if item not in data: 
				raise DataError("{0} missing value {1}".format(self.anchor_file, item))

		return data
	
if __name__ == '__main__':
	
	CreateOJSXML( ).begin()
