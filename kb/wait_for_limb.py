from goobi.goobi_step import Step
import tools.tools as tools
import tools.limb as limb_tools
import os, time

class WaitForLimb( Step ):

	def setup(self):
		self.name = 'Wait for LIMB'
		self.config_main_section = 'limb_output'
		self.essential_config_sections = set( [''] )
		self.essential_commandlines = {
			'process_id' : 'number',
			'process_path' : 'folder',
			'auto_report_problem' : 'string',
			'step_id' : 'number'
		}

	def step(self):
		'''
		This script's role is to wait until
		LIMB processing is complete before finishing.
		In the event of a timeout, it reports back to 
		previous step before exiting.
		'''
		retry_counter = 0
		try:
			self.getVariables()
			# keep on retrying for the given number of attempts
			while retry_counter < self.retry_num:
				if self.limbIsReady():
					self.info_message("LIMB output is ready - exiting.")
					return None
				else:
					# if they haven't arrived, sit and wait for a while
					self.info_message("LIMB output not ready - sleeping for {0} seconds...".format(self.retry_wait))
					retry_counter += 1
					time.sleep(self.retry_wait)			
		except IOError as e:
			print e.strerror
		# if we've gotten this far, we've timed out and need to go back to the previous step
		self.reportToStep("Timed out waiting for LIMB output.")

	def limbIsReady(self):
		'''
		Check to see if LIMB is finished
		return boolean
		'''
		if limb_tools.tocExists(self.toc_dir) \
			and limb_tools.altoFileCountMatches(self.alto_dir, self.input_files_dir):
			return True
		else:
			return False

	def getVariables(self):
		'''
		We need the limb_output folder,
		the location of the toc file
		Throws error if any directories are missing
		or if our retry vals are not numbers
		'''
		process_title = self.command_line.process_title
		limb = self.getConfigItem('limb_output')
		alto = self.getConfigItem('alto')
		toc = self.getConfigItem('toc')
		pdf = self.getConfigItem('pdf')
		inputs = self.getConfigItem('input_files')

		self.retry_num = int(self.getConfigItem('retry_num'))
		self.retry_wait = int(self.getConfigItem('retry_wait'))

		# join paths to create absolute paths
		self.limb_dir = os.path.join(limb, process_title)
		self.alto_dir = os.path.join(self.limb_dir, alto)
		self.toc_dir = os.path.join(self.limb_dir, toc)
		self.pdf_dir = os.path.join(self.limb_dir, pdf)
		self.input_files_dir = os.path.join(self.limb_dir, inputs)

		# raises error if one of our directories is missing
		tools.ensureDirsExist(self.limb_dir, self.alto_dir, \
			self.toc_dir, self.pdf_dir, self.input_files_dir)

if __name__ == '__main__':
	
	WaitForLimb( ).begin()
