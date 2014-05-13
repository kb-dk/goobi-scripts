from goobi.goobi_step import Step
import os
import tools.tools as tools
import tools.goobi as goobi_tools
from tools.errors import DataError


class UploadToOJS( Step ):

	def setup(self):
		self.name = 'UploadToOJS'
		self.config_main_section = 'ojs'
		self.essential_config_sections = set( ['ojs', 'process_folder_structure', 'process_files'] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_path' : 'folder',
			'process_title' : 'string'
		}

	def step(self):
		'''
		Transfer article pdfs and OJS xml
		to the relevant folder on the OJS server
		'''
		try:
			self.getVariables()
			self.transferPDFs()
			self.transferXML()
		except (DataError, OSError) as e:
			return "Execution halted due to error {0}".format(e.strerror)

		return None

	def getVariables(self):
		'''
		This script pulls in all the variables
		from the command line and the config file 
		that are necessary for its running.
		Errors in variables will lead to an 
		Exception being thrown.
		We need the path to the OJS mount,
		the current process dir, the pdf dir,
		and the ojs xml dir.
		'''
		ojs_mount = self.getConfigItem('ojs_mount')
		ojs_metadata_dir = self.getConfigItem('metadata_ojs_path', None, 'process_folder_structure')
		self.ojs_metadata_dir = os.path.join(self.command_line.process_path, ojs_metadata_dir)
		pdf_path = self.getConfigItem('doc_pdf_path', None, 'process_folder_structure')
		self.pdf_dir = os.path.join(self.command_line.process_path, pdf_path)
		anchor_name = self.getConfigItem('metadata_goobi_anchor_file', None, 'process_files')
		anchor_data = goobi_tools.getAnchorFileData(\
			os.path.join(self.command_line.process_path, anchor_name), ['TitleDocMainShort'])
		volume_title = anchor_data['TitleDocMainShort']

		ojs_journal_folder = os.path.join(ojs_mount, volume_title)
		tools.find_or_create_dir(ojs_journal_folder)
		self.ojs_dest_dir = os.path.join(ojs_journal_folder, self.command_line.process_title)
		tools.find_or_create_dir(self.ojs_dest_dir)

		tools.ensureDirsExist(self.ojs_metadata_dir, self.pdf_dir, self.ojs_dest_dir)


	def transferPDFs(self):
		tools.copy_files(self.pdf_dir, self.ojs_dest_dir)


	def transferXML(self):
		tools.copy_files(self.ojs_metadata_dir, self.ojs_dest_dir)

if __name__ == '__main__':
	
	UploadToOJS( ).begin()