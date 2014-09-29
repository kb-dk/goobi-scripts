import os
from goobi.goobi_step import Step
from tools.xml_tools import dict_tools, xml_tools
from tools.mets import mets_tools


class CreateMetsFile( Step ):

	def setup(self):
		self.config_main_section = 'create_mets_file'
		self.essential_config_sections = set( ['process_folder_structure', 'process_files'] )
		self.essential_commandlines = {
			'process_path' : 'folder'
		}

	def step(self):
		error = None
		try:
			self.getVariables()
			self.checkPaths()
			self.createMetsFile()
		except ValueError as e:
			error =  e
		except IOError as e:
			error =  e.strerror
		except OSError as e:
			error =  e
		return error


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
		self.meta_file = os.path.join(
			self.command_line.process_path, 
			self.getConfigItem('metadata_goobi_file', section='process_files')
		)
		self.img_src = os.path.join(
			self.command_line.process_path, 
			self.getConfigItem('img_master_path', section='process_folder_structure')
		)
		
	
	def checkPaths(self):
		'''
		Check if the file meta.xml exist and check if there are files in 
		master_orig folder.
		'''
		if not os.path.exists(self.meta_file):
			err = '{0} does not exist.'.format(self.meta_file)
			raise OSError(err)
		if not len(os.listdir(self.img_src)):
			err = '{0} is empty and must contain files.'.format(self.img_src)
			raise OSError(err)
			

	def createMetsFile(self):
		'''
		Given a toc object consisting of articles with dbc ids
		use the DBC service to 	generate data for each article.
		When all data is created, append this to the exising
		meta.xml data
		'''
		
		dt,_ = dict_tools.parseXmlToDict(self.meta_file)
		if not mets_tools.containsImages(dt):
			dt = mets_tools.addImages(dt,self.img_src)
			xml_tools.writeDictTreeToFile(dt,self.meta_file)

if __name__ == '__main__':
	
	CreateMetsFile( ).begin()
