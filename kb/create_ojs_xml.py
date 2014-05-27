#!/usr/bin/python
# -*- coding: utf-8
from goobi.goobi_step import Step
from xml.dom import minidom
from tools.errors import DataError, InputError

from tools import tools
from tools.toc import TOC
import os, time

class CreateOJSXML( Step ):

	def setup(self):
		self.name = 'Create OJS XML'
		self.config_main_section = 'ojs'
		self.essential_config_sections = set( ['ojs', 'process_folder_structure', 'process_files'] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_title' : 'string',
			'process_path' : 'folder',
			'overlapping_articles' : 'string',
			'auto_report_problem' : 'string',
			'step_id' : 'number'
		}

	def step(self):
		try:
			self.getVariables()
			self.createXML()
		except OSError as e:
			return e.strerror + " " + e.filename
		except (DataError, IOError, InputError) as e:
			self.debug_message(str(e))
			return e.strerror
		except Exception as e:
			self.debug_message(str(e))
			raise e
		# if we got here everything is fine
		return None

	def getVariables(self):
		'''
		Ensure we have the variables necessary to execute the script
		Tools will throw an Exception otherwise
		'''
		process_path = self.command_line.process_path
		anchor_name = self.getConfigItem('metadata_goobi_anchor_file', None, 'process_files')
		self.anchor_file = os.path.join(process_path, anchor_name)
		toc_path = self.getConfigItem('metadata_toc_path', None, 'process_folder_structure')
		abs_toc_path = os.path.join(process_path, toc_path)
		toc_name = tools.getFirstFileWithExtension(abs_toc_path, '.toc')
		self.toc_file = os.path.join(abs_toc_path, toc_name)
		self.ojs_root = self.getConfigItem('ojs_root')
		ojs_metadata_dir = self.getConfigItem('metadata_ojs_path', None, 'process_folder_structure')
		self.ojs_metadata_dir = os.path.join(process_path, ojs_metadata_dir)

		pdf_path = self.getConfigItem('doc_limbpdf_path', None, 'process_folder_structure')
		abs_pdf_path = os.path.join(process_path, pdf_path)
		self.pdf_name = tools.getFirstFileWithExtension(abs_pdf_path, '.pdf')
		self.pdf_file = os.path.join(abs_pdf_path, self.pdf_name)
		# TODO: check files in 'doc_pdf_path' instead of 'doc_limbpdf_path'
		# 'doc_limbpdf_path' contains the splitted pdf-files
		tools.ensureFilesExist(self.anchor_file, self.toc_file, self.pdf_file)
		tools.ensureDirsExist(self.ojs_metadata_dir)

		# parse boolean from command line
		if self.command_line.overlapping_articles.lower() == 'true':
			self.overlapping_articles = True
		elif self.command_line.overlapping_articles.lower() == 'false':
			self.overlapping_articles = False
		else:
			raise InputError("overlapping_articles parameter was not a valid boolean")

		# we also need the required anchor fields
		req_fields = self.getConfigItem('anchor_required_fields')
		self.anchor_required_fields = req_fields.split(';')
		opt_fields = self.getConfigItem('anchor_optional_fields')
		self.anchor_optional_fields = opt_fields.split(';')

	def createXML(self):
		'''
		Get the data from the anchor file and the toc
		Use this to construct the OJS XML
		'''
		anchor_data = self.getAnchorFileData()

		# this is the dir where files will be uploaded to
		
		journal_title_path = tools.parseTitle(anchor_data['TitleDocMainShort'])
		self.ojs_dir = os.path.join(self.ojs_root,journal_title_path, self.command_line.process_title)
		
		pdfinfo = tools.pdfinfo(self.pdf_file)
		toc_data = TOC(self.toc_file)
		toc_data.addEndPageInfo(pdfinfo, self.overlapping_articles)
		
		impl = minidom.getDOMImplementation()
		doc = impl.createDocument(None, "issue", None)
		doc = self.createHeadMaterial(doc, anchor_data)
		
		front_section = self.createFrontSectionXML(doc, anchor_data)
		article_section = self.createArticleSectionXML(doc, anchor_data)
		back_section = self.createBackSectionXML(doc, anchor_data)
		date_published = "{0}-01-01".format(anchor_data['PublicationYear'])


		front_section = self.createArticlesForSection(\
			toc_data.getFrontSection().articles, front_section, doc, date_published)

		doc.documentElement.appendChild(front_section)
		
		article_section = self.createArticlesForSection(\
			toc_data.getBodySection().articles, article_section, doc, date_published)

		doc.documentElement.appendChild(article_section)
		
		back_section = self.createArticlesForSection(\
			toc_data.getBackSection().articles, article_section, doc, date_published)

		doc.documentElement.appendChild(back_section)

		# save the xml content to the correct file
		output_name = os.path.join(self.ojs_metadata_dir, self.command_line.process_title + '.xml')
		output = open(output_name, 'w')

		output.write(doc.toxml('utf-8'))
	
	def createArticlesForSection(self, articles, section_tag, doc, date):
		for art in articles:
			art = self.__translateArticleTitles(art)
			article = self.createArticleXML(doc, art, date, art.number)
			section_tag.appendChild(article)
		return section_tag	

	def createSectionXML(self, doc, anchor_data, title, abbrev):
		section = doc.createElement('section')
		section_title_tag = self.createXMLTextTag(doc, 'title', title)
		abbrev_tag = self.createXMLTextTag(doc, 'abbrev', abbrev)
		locale = tools.convertLangToLocale(anchor_data['DocLanguage'])
		abbrev_tag.setAttribute('locale', locale)
		section.appendChild(section_title_tag)
		section.appendChild(abbrev_tag)
		
		return section

	def createFrontSectionXML(self, doc, anchor_data):
		return self.createSectionXML(doc, anchor_data, 'Indledning', 'IND')
		

	def createArticleSectionXML(self, doc, anchor_data):
		return self.createSectionXML(doc, anchor_data, 'Artikler', 'ART')

	def createBackSectionXML(self, doc, anchor_data):
		return self.createSectionXML(doc, anchor_data, 'Diverse', 'DIV')		
		
	def createArticleXML(self, doc, article, date_published, index):
		'''
		Given an article dict, create the OJS XML
		corresponding to this data
		'''
		article_tag = doc.createElement('article')
		title_tag = self.createXMLTextTag(doc, 'title', article.title)
		page_range = "{0}-{1}".format(article.start_page, article.end_page)
		pages_tag = self.createXMLTextTag(doc, 'pages', page_range) # TODO fix this to use range
		published_tag = self.createXMLTextTag(doc, 'date_published', date_published) 
		galley_tag = self.createGalleyXML(doc, index)
		
		article_tag.appendChild(published_tag)
		article_tag.appendChild(title_tag)
		article_tag.appendChild(pages_tag)

		# don't add an author tag if we don't have one (e.g. Front Matter)
		if article.author: 
			author_tag = self.createAuthorXML(doc, article.author)
			article_tag.appendChild(author_tag)

		article_tag.appendChild(galley_tag)

		return article_tag

	def createGalleyXML(self, doc, index):
		galley_tag = doc.createElement('galley')
		label_tag = self.createXMLTextTag(doc, 'label', 'PDF')
		file_tag = doc.createElement('file')
		link_tag = doc.createElement('href')
		link_tag.setAttribute('mime_type', 'application/pdf')
		article_name = tools.getArticleName(self.pdf_name, index)
		article_link = os.path.join(self.ojs_dir, article_name)
		link_tag.setAttribute('src', article_link)

		galley_tag.appendChild(label_tag)
		file_tag.appendChild(link_tag)
		galley_tag.appendChild(file_tag)

		return galley_tag


	def createAuthorXML(self, doc, name_str):
		''' 
		Create OJS Author tag based on name string
		Firstname is first word in string
		Lastname is last word in string 
		Middlename is anything in between or CDATA
		'''

		author_tag = doc.createElement('author')
		name = name_str.split(' ')
	
		# only create a firstname if there's more than one name
		if len(name) > 1:
			firstname_tag = self.createXMLTextTag(doc, 'firstname', name[0])
		else:
			firstname_tag = self.createEmptyElement(doc, 'firstname')
		
		# middlename is anything between the first and last names, or an empty element 
		if len(name[1:-1]) > 0:
			middlename = ' '.join(name[1:-1])
			middlename_tag = self.createXMLTextTag(doc, 'middlename', middlename)
		else:
			middlename_tag = self.createEmptyElement(doc, 'middlename')
		
		lastname_tag = self.createXMLTextTag(doc, 'lastname', name[-1])
		email_tag = self.createEmptyElement(doc, 'email')
		
		
		author_tag.appendChild(firstname_tag)
		author_tag.appendChild(middlename_tag)
		author_tag.appendChild(lastname_tag)
		author_tag.appendChild(email_tag)

		return author_tag


	def createEmptyElement(self, doc, name):
		tag = doc.createElement(name)
		cdata = doc.createCDATASection(' ')
		tag.appendChild(cdata)

		return tag

	def createHeadMaterial(self, doc, anchor_data):
		'''
		Create and append all the OJS XML Header data
		to XML Document doc based on the data in anchor_data
		'''
		top = doc.documentElement

		top.setAttribute('current', 'false')
		top.setAttribute('published', 'true')
		
		top.setAttribute('identification', 'num_vol_year')
		
		
		title_tag = self.createXMLTextTag(doc, 'title', anchor_data['TitleDocMainShort'])
		top.appendChild(title_tag)
		
		year_tag = self.createXMLTextTag(doc, 'year', anchor_data['PublicationYear'])
		top.appendChild(year_tag)
		
		volume_tag = self.createXMLTextTag(doc, 'volume', anchor_data['VolumeNumber'])
		top.appendChild(volume_tag)

		number_tag = self.createXMLTextTag(doc, 'number', anchor_data['IssueNumber'])
		top.appendChild(number_tag)

		access_tag = self.createXMLTextTag(doc, 'access_date', time.strftime("%Y-%m-%d"))
		top.appendChild(access_tag)

		# we just say that it's the first of the year - we don't know the real date
		date_published = "{0}-01-01".format(anchor_data['PublicationYear'])
		date_tag = self.createXMLTextTag(doc, 'date_published', date_published)
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
			if name in self.anchor_required_fields or name in self.anchor_optional_fields:
				data[name] = elem.firstChild.nodeValue
		
		for item in self.anchor_required_fields:
			if item not in data: 
				raise DataError("{0} missing value {1}".format(self.anchor_file, item))

		return data
	
	def __translateArticleTitles(self, article):
		if article.title == 'Front Matter': article.title = 'Indledning'
		elif article.title == 'Back Matter': article.title = 'Diverse'

		return article

if __name__ == '__main__':
	
	CreateOJSXML( ).begin()
