from goobi.goobi_step import Step
import os
import shutil
import time
import traceback
import tools


class CopyToLimb( Step ):

	def setup(self):
		self.name = 'Copy to LIMB'
		self.config_main_section = 'copy_to_limb'
		self.essential_config_sections = set( [] )
		self.essential_commandlines = {
			"process_id" : "number",
			"source" : "folder",
		}

	def step(self):
		try:
			files_not_copied  = True
			source_dir = self.command_line.source
			transit_dir = os.path.join(self.getConfigItem('limb_transit'),os.path.basename(source_dir))
			hotfolder_dir = self.getConfigItem('limb_hotfolder')
			sleep_interval = int(self.getConfigItem('sleep_interval'))
			retries = int(self.getConfigItem('retries'))
									
			self.info_message("source_dir "+source_dir)
						
			error = tools.copy_files(source_dir,hotfolder_dir,transit_dir,False,sleep_interval,retries,self)
		except Exception as e:
			self.error_message("An error happened %s" %e)	
			traceback.format_exc()
			self.error_message("Script Failed !!!!")
		if files_not_copied and retries <= 0:
			self.error_message("Maximum number of retries exceeded. Script Stopped")	
		return error

if __name__ == '__main__':	
	CopyToLimb().begin()
