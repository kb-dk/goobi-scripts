from goobi.goobi_step import Step

import tools
import os
class SplitPdf( Step ):

	def setup(self):
		self.name = 'Pdf splitter'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			'process_title' : 'string',
			'process_path' : 'folder'
		}

	def step(self):
		'''
		Splits a pdf file according to a toc file
		1. set necessary variables
		2. get data from toc file
		3. cut up pdf file
		4. profit!
		'''
		self.getVariables()
		self.getToc()
		self.dividePdf()

		return None

	def getVariables(self):
		'''
		Get all required vars from command line + config
		and confirm their existence.
		'''
		process_title = self.command_line.process_title
		limb = self.getConfigItem('limb_output')
		toc = self.getConfigItem('toc')
		pdf = self.getConfigItem('pdf')

		# join paths to create absolute paths
		self.limb_dir = os.path.join(limb, process_title)
		self.toc_dir = os.path.join(self.limb_dir, toc)
		self.pdf_dir = os.path.join(self.limb_dir, pdf)

		# return false if one of our directories is missing
		return tools.checkDirectoriesExist(self.limb_dir, self.toc_dir, self.pdf_dir)
	
	def getToc(self):
		toc = tools.getFirstFileWithExtension(self.toc_dir, '.toc')
		self.toc_data = tools.parseToc(os.path.join(self.toc_dir, toc))
		#print toc_data

	def dividePdf(self):
		return None


if __name__ == '__main__':
	
	SplitPdf( ).begin()
