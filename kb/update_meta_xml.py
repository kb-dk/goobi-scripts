from goobi.goobi_step import Step
import os, codecs
from tools import tools as tools
from tools.toc import TOC
from tools.marcxml import MarcXml 
from tools.goobi.meta_xml import MetaXml
import xml.dom.minidom as minidom


class UpdateMetaXml( Step ):

	def setup(self):
		self.name = 'Update meta xml'
		self.config_main_section = 'dbc'
		self.essential_config_sections = set( ['process_folder_structure', 'process_files'] )
		self.essential_commandlines = {
			'process_path' : 'folder'
		}

	def step(self):
		try:
			self.getVariables()
			self.buildXml()
			self.writeXml()
		except ValueError as e:
			return e
		except IOError as e:
			return e.strerror


	def getVariables(self):
		'''
		This method pulls in all the variables
		from the command line and the config file 
		that are necessary for its running.
		We need a path to our toc file, our meta.xml
		and a link to our DBC data service (eXist API).
		Errors in variables will lead to an 
		Exception being thrown.
		'''
		toc_dir = os.path.join(
			self.command_line.process_path, 
			self.getConfigItem('metadata_toc_path', section='process_folder_structure')
		)
		toc_name = tools.getFirstFileWithExtension(toc_dir, '.toc')
		self.toc_data = TOC(os.path.join(toc_dir, toc_name))
		
		self.service_url = self.getConfigItem('dbc_service')
		self.meta_file = os.path.join(
			self.command_line.process_path, 
			self.getConfigItem('metadata_goobi_file', section='process_files')
		)
		self.meta_data = minidom.parse(self.meta_file)

	def getDBCData(self, article_id):
		url = self.service_url.format(article_id)
		return MarcXml.initFromWeb(url)


	def writeXml(self):
		'''
		Write the xml generated back to file
		'''
		writer = codecs.open(self.meta_file, 'r+', 'utf-8')
		self.meta_data.writexml(writer)
		writer.close()


	def buildXml(self):
		'''
		Given a toc object consisting of articles with dbc ids
		use the DBC service to 	generate data for each article.
		When all data is created, append this to the exising
		meta.xml data
		'''
		for index, article in enumerate(self.toc_data.allArticles()):
			data = self.createMetadataStruct(article)
			if data:
				local_id = "%04d" % (index + 1 )
				xml = MetaXml.generateArticleXml(local_id, data)
				self.addToMetaXml(xml.firstChild.firstChild)
				
	def addToMetaXml(self, article_xml):
		'''
		Given an XML node representing an article
		add it to the correct place in the meta xml
		file that represents this process.
		'''
		self.meta_data.firstChild.appendChild(article_xml)			
		
	def createMetadataStruct(self, article):
		'''
		Create a metadata structure that can be 
		consumed by the Meta XML builder class.
		This takes the form of a list of dictionaries,
		with each dictionary representing a field or set of fields.
		For example: [{'name': 'Abstract', 'data' : 'From the Roman Empire...' }, 
			{'name' : 'TitleDocMain', 'data' : 'Return of the oppressed'},
			{'name' : 'Author', 'type' : 'person', 'fields' : [
				{'tag' : 'goobi:firstName', 'data' : 'Peter'},
				{'tag' : 'goobi:lastName', 'data' : 'Turchin'}
			]}
		]
		See the MetaXml class for more details.
		'''
		dataStruct = list()
		if article.article_id: 
			dbc_marc = self.getDBCData(article.article_id)
			title = dict()
			title['name'] = 'TitleDocMain'
			title['data'] = dbc_marc.data['title']
			dataStruct.append(title)
			
			# create an element for the first author
			given_name = dbc_marc.data['author_given_name'] if 'author_given_name' in dbc_marc.data else ""
			family_name = dbc_marc.data['author_family_name'] if 'author_family_name' in dbc_marc.data else ""
			author_element = self.__createAuthorElement(given_name, family_name)
			if author_element: 	dataStruct.append(author)
			# create elements for any other authors
			for a in dbc_marc.data['other_authors']:
				author_element = dict()
				author_element = self.__createAuthorElement(a['given_name'], 
					a['family_name'])
				if author_element: dataStruct.append(author_element)
			
			return dataStruct

			

	def __createAuthorElement(self, firstname, lastname):
		'''
		Given a firstname and a lastname, create 
		a list of dictionaries representing a single author
		in the following form:
		[{'tag' : 'goobi:firstName', 'data' : 'Peter'},
		{'tag' : 'goobi:lastName', 'data' : 'Turchin'}]
		If firstname and lastName are empty, it will return
		an empty hash
		'''
		author = dict()
		author['name'] = 'Author'
		author['type'] = 'person'
		author_fields = list()
		if firstname:
			firstname_elem = dict()
			firstname_elem['tag'] = 'goobi:firstName'
			firstname_elem['data'] = firstname
			author_fields.append(firstname_elem)
		if lastname:
			lastname_elem = dict()
			lastname_elem['tag'] = 'goobi:lastName'
			lastname_elem['data'] = lastname
			author_fields.append(lastname_elem)

		# build the best display name we can, given the 
		# data available to us
		display_name = dict()
		display_name['tag'] = 'goobi:displayName'
		if firstname and lastname:
			display_name['data'] = u"{0}, {1}".format(lastname, firstname)
			author_fields.append(display_name)
		elif lastname:
			display_name['data'] = lastname
			author_fields.append(display_name)
		elif firstname:
			display_name['data'] = firstname
			author_fields.append(display_name)

		if author_fields:
			author['fields'] = author_fields
			return author
		else:
			return None


if __name__ == '__main__':
	
	UpdateMetaXml( ).begin()
