from goobi.goobi_step import Step
import os, subprocess
import tools.goobi as goobi_tools
import tools.tools as tools
from tools.errors import DataError



class RunOJSImport( Step ):

	def setup(self):
		self.name = 'Run OJS Import'
		self.config_main_section = 'ojs'
		self.essential_config_sections = set( ['ojs'] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_path' : 'folder',
			'process_title' : 'string'
		}

	def step(self):
		'''
		This script logs into the OJS server
		and runs the PHP script for import 
		of a journal using the OJS XML generated
		'''
		try:
			self.getVariables()
			self.runImport()
		except DataError as e:
			return "Execution halted due to error {0}".format(e.strerror)
		except subprocess.CalledProcessError as e:
			return "System command failed {0}".format(e.cmd)
		return None

	def getVariables(self):
		'''
		This script pulls in all the variables
		from the command line and the config file 
		that are necessary for its running.
		Errors in variables will lead to an 
		Exception being thrown.
		We need the ojs server, and user 
		path to the correct dir for the import tool
		path to the correct dir for the xml
		name of the journal and an OJS admin user
		'''
		self.ojs_server = self.getConfigItem('ojs_server')
		self.ojs_server_user = self.getConfigItem('ojs_server_user')
		self.ojs_app_user = self.getConfigItem('ojs_app_user')
		self.tool_path = self.getConfigItem('tool_path')

		anchor_name = self.getConfigItem('metadata_goobi_anchor_file', None, 'process_files')
		anchor_data = goobi_tools.getAnchorFileData(\
			os.path.join(self.command_line.process_path, anchor_name), ['TitleDocMainShort'])
		self.volume_title = tools.parseTitle(anchor_data['TitleDocMainShort'])

		# build the path to the ojs xml file based in the form 
		# <upload_dir>/<journal_name>/<process_name>/<process_name>.xml
		upload_dir = self.getConfigItem('upload_dir').\
			format(self.volume_title, self.command_line.process_title)

		xml_name = "{0}.xml".format(self.command_line.process_title)
		self.xml_path = os.path.join(upload_dir,  xml_name)

	def runImport(self):
		'''
		subprocess.call(['ssh', 'romc-admin@strid.kb.dk', 
			'sudo', 'php', '/var/www/html/ojs/tools/importExport.php', 
			'NativeImportExportPlugin', 'import', '/var/www/html/tidsskrift-dk/sample_ojs2.xml', 
			'landskab', 'romc'])
		Using the supplied variables - call the script on the OJS server through ssh
		throw a CalledProcessError if the script failed
		'''
		login = "{0}@{1}".format(self.ojs_server_user, self.ojs_server)
		subprocess.check_call(['ssh', login, 'sudo', 'php', self.tool_path, 
			'NativeImportExportPlugin', 'import', self.xml_path, self.volume_title, self.ojs_app_user])
		

if __name__ == '__main__':
	
	RunOJSImport().begin()