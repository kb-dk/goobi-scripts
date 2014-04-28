from goobi.goobi_step import Step

import tools
import os, sys
class ValidateLimbOutput( Step ):

	def setup(self):
		self.name = 'ValidateLimbOutput'
		self.config_main_section = 'validate_limb_output'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			'process_title' : 'string',
			'process_path' : 'folder'
		}


	def step(self):
		'''
		This class checks the output from a LIMB process
		to see if it matches certain criteria
		Require params process_title from command line
		Other values taken from config.ini
		'''
		self.getVariables()
		self.performValidations()
		print self.limb_dir
		print self.alto_dir


		return None	

	def getVariables(self):
		'''
		Get all required vars from command line + config
		and confirm their existence.
		'''
		process_title = self.command_line.process_title
		limb = self.getConfigItem('limb_output')
		alto = self.getConfigItem('alto')
		toc = self.getConfigItem('toc')
		pdf = self.getConfigItem('pdf')
		originals = self.getConfigItem('input_files')

		# join paths to create absolute paths
		self.limb_dir = os.path.join(limb, process_title)
		self.alto_dir = os.path.join(self.limb_dir, alto)
		self.toc_dir = os.path.join(self.limb_dir, toc)
		self.pdf_dir = os.path.join(self.limb_dir, pdf)
		self.originals_dir = os.path.join(self.limb_dir, originals)

		# exit if one of our directories is missing
		if not tools.checkDirectoriesExist(self.limb_dir, self.alto_dir, \
			self.toc_dir, self.pdf_dir, self.originals_dir):
			print "path not found - exiting..."
			sys.exit(1)


	def performValidations(self):
		'''
		1: validering af pdf (antal sider i pdf == antal input billeder)
		2: validering af toc-fil (pt. er der en fil - validering ved parsing efterfoelgende)
		3: validering af alto-filer (evt. "er der lige saa mange som input billeder" eller "er der filer")
		4: en funktion kan give antallet af input billeder 
		'''
		if not self.tocExists(): 
			print "toc not found - exiting..."
			sys.exit(1)

	# make sure a .toc file exists in toc directory
	def tocExists(self):
		for file in os.listdir(self.toc_dir):
			if file.endswith('.toc'): return True
		
		return False
if __name__ == '__main__':
	
	ValidateLimbOutput().begin()