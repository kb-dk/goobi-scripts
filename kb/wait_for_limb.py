from goobi.goobi_step import Step
import os

class WaitForLimb( Step ):

	def setup(self):
		self.name = 'A tester'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( [''] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_path' : 'folder'
		}

	def step(self):
		'''
		This script's role is to wait until
		LIMB processing is complete before finishing.
		'''
		self.getVariables()
		return None

	def getVariables(self):
		'''
		We need the limb_output folder,
		the location of the toc file
		'''
		limb_out = self.getConfigItem('limb_output')
		self.limb_dir = os.path.join(limb_out, self.command_line.process_title)
		
		print self.limb_dir


if __name__ == '__main__':
	
	WaitForLimb( ).begin()
