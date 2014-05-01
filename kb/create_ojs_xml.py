from goobi.goobi_step import Step
from xml.dom import minidom
from errors import DataError

import tools
import os

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

		print toc_data


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
